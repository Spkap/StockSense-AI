"""Provider failures and async inference must remain honest and responsive."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from stocksense.core import data_collectors, analyzer
from stocksense.agents import skeptic_agent
from stocksense.agents.bull_analyst import BullAnalyst
from stocksense.agents.bear_analyst import BearAnalyst
from stocksense.agents.synthesizer import Synthesizer


def test_news_search_excludes_body_mentions_and_deduplicates(monkeypatch):
    response = Mock()
    response.json.return_value = {'status': 'ok', 'articles': [
        {'title': ' Apple earnings '}, {'title': 'apple earnings'}, {'title': '[Removed]'},
        {'title': None}, {'title': '   '}, {'title': 'Apple product update'}]}
    client = Mock()
    client.request_method.get.return_value = response
    monkeypatch.setattr(data_collectors, 'get_newsapi_key', lambda: 'test')
    monkeypatch.setattr(data_collectors, 'NewsApiClient', lambda **kwargs: client)
    assert data_collectors.get_news('AAPL') == ['Apple earnings', 'Apple product update']
    call = client.request_method.get.call_args.kwargs
    assert call['params']['searchIn'] == 'title,description'
    assert call['timeout'] == 15


def test_debate_agents_use_async_model_calls(monkeypatch):
    async def run():
        for agent_type in (BullAnalyst, BearAnalyst):
            agent = agent_type()
            agent.llm = SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content='{"thesis":"Evidence-based case","confidence":0.5,"key_claims":[]}')),
                                        invoke=Mock(side_effect=AssertionError('synchronous model call')))
            agent.llm.bind = lambda **kwargs: agent.llm
            result = await agent.analyze('AAPL', {}, [], [], {})
            assert result.ticker == 'AAPL'
            agent.llm.ainvoke.assert_awaited_once()
            agent.llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content='{"rebuttals": []}'))
            assert await agent.generate_rebuttal({}, {}, {}) == []
            agent.llm.ainvoke.assert_awaited_once()
        agent = Synthesizer()
        agent.llm = SimpleNamespace(ainvoke=AsyncMock(return_value=SimpleNamespace(content='{}')),
                                    invoke=Mock(side_effect=AssertionError('synchronous model call')))
        agent.llm.bind = lambda **kwargs: agent.llm
        agent.llm.ainvoke = AsyncMock(return_value=SimpleNamespace(content='{"bull_probability":0.2,"base_probability":0.5,"bear_probability":0.3,"recommendation":"Hold","conviction":0.6,"decisive_factors":[],"unresolved_questions":[],"reasoning":"Mixed evidence"}'))
        await agent.synthesize('AAPL', {}, {}, [], [], {})
        agent.llm.ainvoke.assert_awaited_once()
    asyncio.run(run())


def test_malformed_skeptic_output_is_unavailable_not_agreement(monkeypatch):
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content='{"truncated":')
    monkeypatch.setattr(skeptic_agent, 'get_chat_llm', lambda **kwargs: llm)
    primary = SimpleNamespace(overall_sentiment='Bullish', overall_confidence=.8, confidence_reasoning='Demand evidence',
                              potential_impact='Uncertain', key_themes=[], risks_identified=[],
                              model_dump_json=lambda: '{}')
    result = skeptic_agent.generate_skeptic_analysis(primary, ['headline'], 'AAPL')
    assert result.error
    assert result.skeptic_sentiment == 'Unavailable'
    response_format = llm.bind.call_args.kwargs['response_format']
    assert response_format['type'] == 'json_schema'
    schema = response_format['json_schema']['schema']
    assert {'critiques', 'bear_cases'}.issubset(schema['required'])
    assert schema['properties']['critiques']['minItems'] == 1
    assert schema['properties']['bear_cases']['minItems'] == 1


def test_malformed_sentiment_output_is_failure_not_neutral(monkeypatch):
    import pytest
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content='broken JSON')
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    with pytest.raises(RuntimeError, match='could not be completed'):
        analyzer.analyze_sentiment_structured(['headline'])
    schema = llm.bind.call_args.kwargs['response_format']['json_schema']['schema']
    assert schema['properties']['headline_analyses']['minItems'] == 1
    assert schema['properties']['headline_analyses']['maxItems'] == 1


def test_nonfinite_provider_data_is_valid_json_at_each_boundary(monkeypatch):
    import json
    from stocksense.orchestration.streaming import StreamEvent, StreamEventType
    from stocksense.db import database
    from unittest.mock import MagicMock
    raw = {'info': {'pe_ratio': float('nan')}, 'income_statement': {'2026': {'income': float('inf')}},
           'nested': [float('-inf'), {'valid': 12.5}]}
    clean = data_collectors.json_safe_data(raw)
    assert clean['info']['pe_ratio'] is None
    assert clean['income_statement']['2026']['income'] is None
    assert clean['nested'] == [None, {'valid': 12.5}]
    event = StreamEvent(StreamEventType.COMPLETED, data={'fundamental_data': raw})
    payload = json.loads(event.to_sse().removeprefix('data: '), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    assert payload['data']['fundamental_data'] == clean
    admin = MagicMock()
    admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{'id': 1}]
    monkeypatch.setattr(database, 'get_supabase_admin_client', lambda: admin)
    database.save_analysis('AAPL', 'summary', 'report', fundamental_data=raw)
    stored = admin.table.return_value.update.call_args.args[0]
    assert stored['fundamental_data'] == clean
    json.dumps(stored, allow_nan=False)


def test_invalid_debate_outputs_never_create_fallback_recommendation():
    import pytest
    async def run():
        analyst = BullAnalyst()
        analyst.llm = Mock()
        analyst.llm.bind.return_value.ainvoke = AsyncMock(return_value=SimpleNamespace(content='{}'))
        with pytest.raises(RuntimeError, match='unavailable'):
            await analyst.analyze('AAPL', {}, [], [], {})
        synthesizer = Synthesizer()
        synthesizer.llm = Mock()
        for payload in ('{}', '{"bull_probability":0.5,"base_probability":0.5,"bear_probability":0.5,"recommendation":"Hold","conviction":0.5,"decisive_factors":[],"unresolved_questions":[],"reasoning":"test"}'):
            synthesizer.llm.bind.return_value.ainvoke = AsyncMock(return_value=SimpleNamespace(content=payload))
            with pytest.raises(RuntimeError, match='could not be completed'):
                await synthesizer.synthesize('AAPL', {}, {}, [], [], {})
    asyncio.run(run())


def test_missing_skeptic_fields_never_default_to_agreement(monkeypatch):
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content='{}')
    monkeypatch.setattr(skeptic_agent, 'get_chat_llm', lambda **kwargs: llm)
    primary = SimpleNamespace(overall_sentiment='Bullish', overall_confidence=.8, confidence_reasoning='Demand evidence',
                              potential_impact='Uncertain', key_themes=[], risks_identified=[],
                              model_dump_json=lambda: '{}')
    result = skeptic_agent.generate_skeptic_analysis(primary, ['headline'], 'AAPL')
    assert result.error
    assert result.skeptic_sentiment == 'Unavailable'


def test_missing_sentiment_fields_never_default_to_neutral(monkeypatch):
    import pytest
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content='{}')
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    with pytest.raises(RuntimeError):
        analyzer.analyze_sentiment_structured(['headline'])


def test_skeptic_receives_real_primary_themes_and_risks(monkeypatch):
    from stocksense.orchestration.react_flow import generate_skeptic_critique
    from stocksense.core.schemas import SentimentAnalysisResult
    captured = []
    primary = {'overall_sentiment': 'Bullish', 'overall_confidence': .7, 'confidence_reasoning': 'Demand evidence',
               'bullish_count': 1, 'bearish_count': 0, 'neutral_count': 0, 'insufficient_data_count': 0,
               'headline_analyses': [], 'key_themes': [{'theme': 'Demand growth', 'sentiment_direction': 'Bullish', 'headline_count': 1, 'summary': 'Demand rises'}],
               'potential_impact': 'Moderate Positive', 'risks_identified': ['Supply constraints'], 'information_gaps': ['Margins']}
    def fake_skeptic(context, headlines, ticker):
        captured.append(context)
        return skeptic_agent.SkepticAnalysis(skeptic_sentiment='Partially Disagree', primary_disagreement='Margins unknown', skeptic_confidence=.6)
    monkeypatch.setattr(skeptic_agent, 'generate_skeptic_analysis', fake_skeptic)
    result = generate_skeptic_critique.invoke({'ticker': 'AAPL', 'headlines': ['headline'], 'primary_sentiment': 'Bullish', 'primary_confidence': .7, 'primary_analysis': primary})
    assert result['success']
    assert captured[0].key_themes[0].theme == 'Demand growth'
    assert captured[0].risks_identified == ['Supply constraints']
    assert captured[0].confidence_reasoning == 'Demand evidence'
