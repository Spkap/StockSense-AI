"""Verify the requested stock and source headlines survive sentiment analysis."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

from stocksense.core import analyzer
from stocksense.orchestration import react_flow, streaming


def test_sentiment_prompt_targets_requested_stock_and_preserves_original_headline(monkeypatch):
    original = 'Alphabet reports earnings alongside Microsoft'
    payload = {
        'overall_sentiment': 'Neutral', 'overall_confidence': .4,
        'confidence_reasoning': 'The implications for Microsoft are unclear.',
        'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 1,
        'insufficient_data_count': 0,
        'headline_analyses': [{'headline': f'  {original.lower()}  ', 'sentiment': 'Neutral',
                               'confidence': .4, 'reasoning': 'Multiple companies', 'key_entities': []}],
        'potential_impact': 'Uncertain',
    }
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content=json.dumps(payload))
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    result = analyzer.analyze_sentiment_structured([original], ticker='msft')
    prompt = llm.bind.return_value.invoke.call_args.args[0]
    assert 'target stock MSFT' in prompt
    assert 'specifically for MSFT' in prompt
    assert result.headline_analyses[0].headline == original


def test_stream_sentiment_receives_requested_ticker(monkeypatch):
    captured = {}
    def sentiment(args):
        captured.update(args)
        return {'success': True, 'overall_sentiment': 'Neutral', 'overall_confidence': .5,
                'headline_analyses': []}
    results = {
        'fetch_news_headlines': {'success': True, 'headlines': ['Headline'], 'articles': []},
        'fetch_price_data': {'success': True, 'price_data': [{'Date': '2026-10-26', 'Close': 10}]},
        'fetch_fundamentals': {'success': False},
        'generate_skeptic_critique': {'success': False},
    }
    for name, value in results.items():
        monkeypatch.setattr(react_flow, name, SimpleNamespace(invoke=lambda args, value=value: value))
    monkeypatch.setattr(react_flow, 'analyze_sentiment', SimpleNamespace(invoke=sentiment))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('msft')]
    events = asyncio.run(run())
    assert events[-1].event_type == streaming.StreamEventType.COMPLETED
    assert '1 headline analyzed' in events[-1].data['summary']
    assert 'articles analyzed' not in events[-1].data['summary']
    assert captured == {'headlines': ['Headline'], 'ticker': 'MSFT'}


def test_sentiment_tool_passes_ticker_to_model(monkeypatch):
    captured = {}
    def analyze(headlines, ticker=None):
        captured.update(headlines=headlines, ticker=ticker)
        return SimpleNamespace(overall_sentiment='Neutral', overall_confidence=.5,
            confidence_reasoning='Mixed', bullish_count=0, bearish_count=0, neutral_count=1,
            insufficient_data_count=0, headline_analyses=[], key_themes=[],
            potential_impact='Uncertain', risks_identified=[], information_gaps=[])
    monkeypatch.setattr(analyzer, 'analyze_sentiment_structured', analyze)
    monkeypatch.setattr(analyzer, 'format_sentiment_result', lambda _: 'A report')
    result = react_flow.analyze_sentiment.invoke({'headlines': ['Headline'], 'ticker': 'MSFT'})
    assert result['success']
    assert captured == {'headlines': ['Headline'], 'ticker': 'MSFT'}


def test_sentiment_retries_empty_headline_reasoning(monkeypatch):
    payload = {
        'overall_sentiment': 'Neutral', 'overall_confidence': .4, 'confidence_reasoning': 'Limited evidence',
        'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 1, 'insufficient_data_count': 0,
        'headline_analyses': [{'headline': 'Headline', 'sentiment': 'Neutral', 'confidence': .4,
                               'reasoning': '  ', 'key_entities': []}], 'potential_impact': 'Uncertain',
    }
    corrected = json.loads(json.dumps(payload))
    corrected['headline_analyses'][0]['reasoning'] = 'No direction established.'
    llm = Mock()
    llm.bind.return_value.invoke.side_effect = [SimpleNamespace(content=json.dumps(payload)),
                                               SimpleNamespace(content=json.dumps(corrected))]
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    result = analyzer.analyze_sentiment_structured(['Headline'], ticker='MSFT')
    assert result.headline_analyses[0].reasoning == 'No direction established.'
    assert llm.bind.return_value.invoke.call_count == 2


def test_graph_overrides_model_invented_ticker_for_sentiment(monkeypatch):
    from langchain_core.messages import AIMessage
    headline = 'Microsoft results'
    captured = {}
    def fake_tool(name, result):
        instance = SimpleNamespace(name=name, invoke=Mock(return_value=result))
        captured[name] = instance
        return instance
    tools = [
        fake_tool('fetch_news_headlines', {'success': True, 'headlines': [headline], 'articles': []}),
        fake_tool('fetch_price_data', {'success': True, 'price_data': [{'Date': '2026-10-26', 'Close': 10}]}),
        fake_tool('analyze_sentiment', {'success': True, 'sentiment_report': 'Neutral',
                  'overall_sentiment': 'Neutral', 'overall_confidence': .5, 'headline_analyses': []}),
        fake_tool('generate_skeptic_critique', {'success': True, 'skeptic_report': 'Review'}),
    ]
    responses = [
        AIMessage(content='', tool_calls=[{'name': 'fetch_news_headlines', 'args': {'ticker': 'WRONG'}, 'id': 'news'},
                                          {'name': 'fetch_price_data', 'args': {'ticker': 'WRONG'}, 'id': 'price'}]),
        AIMessage(content='', tool_calls=[{'name': 'analyze_sentiment', 'args': {'headlines': ['Wrong'], 'ticker': 'WRONG'}, 'id': 'sentiment'}]),
        AIMessage(content='', tool_calls=[{'name': 'generate_skeptic_critique', 'args': {'ticker': 'WRONG', 'headlines': ['Wrong'], 'primary_sentiment': 'Bullish', 'primary_confidence': 1}, 'id': 'review'}]),
        AIMessage(content='Summary'),
    ]
    llm = Mock()
    llm.bind_tools.return_value.invoke.side_effect = responses
    monkeypatch.setattr(react_flow, 'get_chat_llm', lambda **kwargs: llm)
    monkeypatch.setattr(react_flow, 'tools', tools)
    monkeypatch.setattr(react_flow, '_cached_react_app', None)
    result = react_flow.run_react_analysis('MSFT')
    assert result['error'] is None
    assert captured['analyze_sentiment'].invoke.call_args.args[0] == {'headlines': [headline], 'ticker': 'MSFT'}
