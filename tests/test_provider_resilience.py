"""Failure boundaries and source integrity for the live research pipeline."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest
from langchain_core.messages import AIMessage
from requests import HTTPError, Timeout
from yfinance.exceptions import YFRateLimitError

from stocksense.core import analyzer, data_collectors
from stocksense.agents import skeptic_agent
from stocksense.orchestration import react_flow, streaming


def _news_client(monkeypatch, outcomes):
    client = Mock()
    client.request_method.get.side_effect = outcomes
    monkeypatch.setattr(data_collectors, 'NewsApiClient', lambda **kwargs: client)
    monkeypatch.setattr(data_collectors, 'get_newsapi_key', lambda: 'test-key')
    monkeypatch.setattr(data_collectors.time, 'sleep', lambda _: None)
    return client


def _response(payload, status=200):
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    if status >= 400:
        response.raise_for_status.side_effect = HTTPError(response=response)
    return response


def test_news_transient_retry_retains_provenance_and_rejects_unsafe_url(monkeypatch):
    client = _news_client(monkeypatch, [Timeout('connection interrupted'), _response({'status': 'ok', 'articles': [
        {'title': 'Company reports results', 'source': {'name': 'Example News'},
         'url': 'https://example.com/story', 'publishedAt': '2026-10-26T12:00:00Z'},
        {'title': 'Second headline', 'url': 'javascript:alert(1)'},
        {'title': 'Malformed source', 'url': 'https://[invalid'},
    ]})])
    headlines = data_collectors.get_news('MSFT')
    assert client.request_method.get.call_count == 2
    assert headlines == ['Company reports results', 'Second headline', 'Malformed source']
    assert headlines.articles[0]['source'] == 'Example News'
    assert headlines.articles[0]['url'] == 'https://example.com/story'
    assert headlines.articles[0]['published_at'] == '2026-10-26T12:00:00Z'
    assert headlines.articles[1]['url'] is None
    assert headlines.articles[2]['url'] is None


@pytest.mark.parametrize(('status', 'code'), [(401, 'apiKeyInvalid'), (429, 'apiKeyExhausted')])
def test_news_auth_and_quota_are_not_retried_or_exposed(monkeypatch, status, code):
    client = _news_client(monkeypatch, [_response({'status': 'error', 'code': code, 'message': 'private-key'}, status)])
    result = react_flow.fetch_news_headlines.invoke({'ticker': 'MSFT'})
    assert not result['success'] and client.request_method.get.call_count == 1
    assert 'private-key' not in str(result)
    assert result['error_code'] in ('news_auth', 'news_rate_limit')


def test_news_5xx_retries_once_then_reports_unavailability(monkeypatch):
    client = _news_client(monkeypatch, [_response({'code': 'unexpectedError'}, 500), _response({'code': 'unexpectedError'}, 503)])
    result = react_flow.fetch_news_headlines.invoke({'ticker': 'MSFT'})
    assert not result['success'] and result['error_code'] == 'news_unavailable'
    assert client.request_method.get.call_count == 2


def test_yahoo_rate_limit_retry_and_history_timeout(monkeypatch):
    history = pd.DataFrame({'Close': [5.0]})
    stock = Mock()
    stock.history.side_effect = [YFRateLimitError(), history]
    monkeypatch.setattr(data_collectors.yf, 'Ticker', lambda _: stock)
    monkeypatch.setattr(data_collectors.time, 'sleep', lambda _: None)
    assert data_collectors.get_price_history('MSFT') is history
    assert stock.history.call_count == 2
    assert stock.history.call_args.kwargs['timeout'] == 12
    assert stock.history.call_args.kwargs['raise_errors'] is True


def test_partial_fundamentals_survive_company_info_failure(monkeypatch):
    class Stock:
        @property
        def info(self):
            raise ConnectionError('upstream offline')
        income_stmt = pd.DataFrame({'2026': {'Revenue': 123}})
        balance_sheet = None
        cashflow = None
    monkeypatch.setattr(data_collectors.yf, 'Ticker', lambda _: Stock())
    monkeypatch.setattr(data_collectors.time, 'sleep', lambda _: None)
    result = react_flow.fetch_fundamentals.invoke({'ticker': 'MSFT'})
    assert result['success'] and result['data']['income_statement']
    assert 'company information' in result['data']['unavailable_sections']


def test_bad_price_values_do_not_discard_valid_close(monkeypatch):
    frame = pd.DataFrame({'Open': [float('nan')], 'High': [12], 'Low': [10],
                          'Close': [11], 'Volume': [float('nan')]},
                         index=pd.DatetimeIndex(['2026-10-26'], name='Date'))
    monkeypatch.setattr(react_flow, 'get_price_history', lambda *args, **kwargs: frame)
    result = react_flow.fetch_price_data.invoke({'ticker': 'MSFT'})
    assert result['success'] and result['price_data'][0]['Close'] == 11
    assert result['price_data'][0]['Open'] is None and result['price_data'][0]['Volume'] is None


def test_stream_retains_source_only_for_matching_headline(monkeypatch):
    results = {
        'fetch_news_headlines': {'success': True, 'headlines': ['Real headline'],
            'articles': [{'title': 'Real headline', 'source': 'Example', 'url': 'https://example.com/a', 'published_at': '2026-10-26T12:00:00Z'}]},
        'fetch_price_data': {'success': True, 'price_data': [{'Date': '2026-10-26', 'Close': 10}]},
        'fetch_fundamentals': {'success': False},
        'analyze_sentiment': {'success': True, 'overall_sentiment': 'Neutral', 'overall_confidence': .5,
            'headline_analyses': [{'headline': 'Real headline', 'sentiment': 'Neutral', 'confidence': .5, 'reasoning': 'Mixed', 'key_entities': []}]},
        'generate_skeptic_critique': {'success': False},
    }
    for name, value in results.items():
        monkeypatch.setattr(react_flow, name, SimpleNamespace(invoke=lambda args, value=value: value))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('MSFT')]
    data = asyncio.run(run())[-1].data
    assert data['headline_analyses'][0]['url'] == 'https://example.com/a'
    assert data['headline_analyses'][0]['source'] == 'Example'
    assert 'not been independently challenged' in data['warnings'][-1]
    assert 'url' not in data_collectors.attach_news_sources([{'headline': 'Different'}], results['fetch_news_headlines']['articles'])[0]


def test_stream_reports_required_failure_without_waiting_for_optional_data(monkeypatch):
    import threading
    import time
    release = threading.Event()
    monkeypatch.setattr(react_flow, 'fetch_news_headlines', SimpleNamespace(invoke=lambda _: {'success': False, 'error': 'quota exhausted'}))
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda _: release.wait(2) or {'success': True}))
    monkeypatch.setattr(react_flow, 'fetch_fundamentals', SimpleNamespace(invoke=lambda _: release.wait(2) or {'success': True}))
    async def run():
        start = time.monotonic()
        events = [event async for event in streaming.run_streaming_analysis('MSFT')]
        duration = time.monotonic() - start
        release.set()
        return events, duration
    try:
        events, duration = asyncio.run(run())
    finally:
        release.set()
    assert events[-1].event_type == streaming.StreamEventType.ERROR
    assert 'quota exhausted' in events[-1].message
    assert duration < 1


def _sentiment_payload(headline):
    return {'overall_sentiment': 'Neutral', 'overall_confidence': .5, 'confidence_reasoning': 'Mixed',
            'bullish_count': 0, 'bearish_count': 0, 'neutral_count': 1, 'insufficient_data_count': 0,
            'headline_analyses': [{'headline': headline, 'sentiment': 'Neutral', 'confidence': .5,
                                   'reasoning': 'Mixed', 'key_entities': []}],
            'potential_impact': 'Uncertain'}


def test_model_retries_invalid_json_and_rejects_invented_headline(monkeypatch):
    llm = Mock()
    llm.bind.return_value.invoke.side_effect = [SimpleNamespace(content=json.dumps(_sentiment_payload('Invented'))),
                                                SimpleNamespace(content=json.dumps(_sentiment_payload('Original')))]
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    result = analyzer.analyze_sentiment_structured(['Original'])
    assert result.headline_analyses[0].headline == 'Original'
    assert llm.bind.return_value.invoke.call_count == 2


def test_sentiment_counts_are_derived_from_validated_headlines(monkeypatch):
    payload = _sentiment_payload('Original')
    payload.update(bullish_count=99, neutral_count=0)
    llm = Mock()
    llm.bind.return_value.invoke.return_value = SimpleNamespace(content=json.dumps(payload))
    monkeypatch.setattr(analyzer, 'get_chat_llm', lambda **kwargs: llm)
    result = analyzer.analyze_sentiment_structured(['Original'])
    assert result.bullish_count == 0 and result.neutral_count == 1


def test_skeptic_retries_malformed_output_without_inventing_agreement(monkeypatch):
    payload = {'skeptic_sentiment': 'Partially Disagree', 'primary_disagreement': 'Uncertain margins',
               'critiques': [{'critique': 'Margins are unclear', 'assumption_challenged': 'Margins hold', 'evidence': 'Not provided'}],
               'bear_cases': [{'argument': 'Margins fall', 'trigger': 'Weak earnings', 'severity': 'Medium'}],
               'skeptic_confidence': .5}
    llm = Mock()
    llm.bind.return_value.invoke.side_effect = [SimpleNamespace(content='{'), SimpleNamespace(content=json.dumps(payload))]
    monkeypatch.setattr(skeptic_agent, 'get_chat_llm', lambda **kwargs: llm)
    primary = SimpleNamespace(overall_sentiment='Bullish', overall_confidence=.7, confidence_reasoning='Evidence',
                              potential_impact='Uncertain', key_themes=[], risks_identified=[],
                              model_dump_json=lambda: '{}')
    result = skeptic_agent.generate_skeptic_analysis(primary, ['Original'], 'MSFT')
    assert result.error is None and result.critiques and result.bear_cases
    assert llm.bind.return_value.invoke.call_count == 2


def test_react_required_tool_failure_stops_without_false_success(monkeypatch):
    calls = []
    class FakeTool:
        name = 'fetch_news_headlines'
        def invoke(self, args):
            calls.append(args)
            return {'success': False, 'error': 'News service is rate limited.', 'error_code': 'news_rate_limit'}
    llm = Mock()
    llm.bind_tools.return_value.invoke.return_value = AIMessage(content='', tool_calls=[
        {'name': 'fetch_news_headlines', 'args': {'ticker': 'WRONG'}, 'id': 'call-1'}])
    monkeypatch.setattr(react_flow, 'get_chat_llm', lambda **kwargs: llm)
    monkeypatch.setattr(react_flow, 'tools', [FakeTool()])
    monkeypatch.setattr(react_flow, '_cached_react_app', None)
    result = react_flow.run_react_analysis('MSFT')
    assert result['error'] == 'News service is rate limited.'
    assert calls[0]['ticker'] == 'MSFT'
    assert not result['summary'] and not result['headlines']
    assert llm.bind_tools.return_value.invoke.call_count == 1


def test_react_exception_never_claims_data_was_collected(monkeypatch):
    monkeypatch.setattr(react_flow, 'get_react_app', lambda: (_ for _ in ()).throw(RuntimeError('unexpected error')))
    result = react_flow.run_react_analysis('MSFT')
    assert result['error'] and 'successful' not in result['summary'].lower()
    assert result['headlines'] == [] and result['sentiment_report'] == ''


def test_react_collects_real_evidence_and_cannot_save_partial_results(monkeypatch):
    captured = {}
    def tool(name, result):
        instance = SimpleNamespace(name=name, invoke=Mock(return_value=result))
        captured[name] = instance
        return instance
    headline = 'Company reports results'
    sentiment = _sentiment_payload(headline)
    sentiment.update(success=True, sentiment_report='Neutral evidence',
                     key_themes=[{'theme': 'Results', 'sentiment_direction': 'Neutral', 'headline_count': 1, 'summary': 'Mixed'}],
                     risks_identified=['Margin risk'], information_gaps=['Guidance'])
    tools = [
        tool('fetch_news_headlines', {'success': True, 'headlines': [headline], 'articles': [{'title': headline, 'source': 'Example', 'url': 'https://example.com/a'}]}),
        tool('fetch_price_data', {'success': True, 'price_data': [{'Date': '2026-10-26', 'Close': 10}]}),
        tool('analyze_sentiment', sentiment),
        tool('generate_skeptic_critique', {'success': True, 'skeptic_report': 'Review', 'skeptic_sentiment': 'Partially Disagree', 'skeptic_confidence': .5}),
        tool('save_analysis_results', {'success': True}),
    ]
    responses = [
        AIMessage(content='Premature conclusion'),
        AIMessage(content='', tool_calls=[{'name': 'fetch_news_headlines', 'args': {'ticker': 'WRONG'}, 'id': 'news'},
                                          {'name': 'fetch_price_data', 'args': {'ticker': 'WRONG'}, 'id': 'prices'}]),
        AIMessage(content='', tool_calls=[{'name': 'analyze_sentiment', 'args': {'headlines': ['Fabricated']}, 'id': 'sentiment'}]),
        AIMessage(content='', tool_calls=[{'name': 'generate_skeptic_critique', 'args': {'ticker': 'WRONG', 'headlines': ['Fabricated'], 'primary_sentiment': 'Bullish', 'primary_confidence': 1}, 'id': 'skeptic'}]),
        AIMessage(content='Evidence-based summary'),
    ]
    llm = Mock()
    llm.bind_tools.return_value.invoke.side_effect = responses
    monkeypatch.setattr(react_flow, 'get_chat_llm', lambda **kwargs: llm)
    monkeypatch.setattr(react_flow, 'tools', tools)
    monkeypatch.setattr(react_flow, '_cached_react_app', None)
    result = react_flow.run_react_analysis('MSFT')
    assert result['error'] is None and result['headlines'] == [headline]
    assert result['headline_analyses'][0]['url'] == 'https://example.com/a'
    assert captured['fetch_news_headlines'].invoke.call_args.args[0]['ticker'] == 'MSFT'
    assert captured['analyze_sentiment'].invoke.call_args.args[0]['headlines'] == [headline]
    skeptic_input = captured['generate_skeptic_critique'].invoke.call_args.args[0]
    assert skeptic_input['primary_analysis']['risks_identified'] == ['Margin risk']
    assert skeptic_input['primary_analysis']['key_themes'][0]['theme'] == 'Results'
    assert 'save_analysis_results' not in [item.name for item in llm.bind_tools.call_args.args[0]]
    captured['save_analysis_results'].invoke.assert_not_called()


def test_scheduler_skips_failed_analysis_without_creating_alerts(monkeypatch):
    from stocksense import scheduler
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.not_.is_.return_value.execute.return_value.data = [
        {'id': 'thesis', 'user_id': 'user', 'ticker': 'MSFT', 'kill_criteria': ['risk']}]
    monkeypatch.setattr(scheduler, 'get_supabase_client', lambda: client)
    monkeypatch.setattr(scheduler, 'run_react_analysis', lambda _: {'error': 'provider unavailable', 'summary': 'Do not treat as evidence'})
    signals = Mock()
    monkeypatch.setattr(scheduler, 'extract_signals_from_analysis', signals)
    asyncio.run(scheduler.check_all_active_theses())
    signals.assert_not_called()
    client.table.return_value.insert.assert_not_called()


def test_missing_ticker_price_error_names_symbol(monkeypatch):
    from stocksense.orchestration import react_flow
    from stocksense.core.data_collectors import ProviderError
    def missing(*args, **kwargs):
        raise ProviderError('No data', 'market_no_data')
    monkeypatch.setattr(react_flow, 'get_price_history', missing)
    result = react_flow.fetch_price_data.invoke({'ticker': 'ZZZZZ'})
    assert result['error_code'] == 'market_no_data'
    assert result['error'] == 'Ticker ZZZZZ was not found or has no price data. Check the symbol and try again.'
