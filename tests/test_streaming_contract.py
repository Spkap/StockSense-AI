"""Regression coverage for streaming completion, failure, and responsiveness."""
import asyncio
import json
import threading
from types import SimpleNamespace
import pytest
from fastapi import HTTPException

from starlette.requests import Request

from stocksense import main
from stocksense.orchestration import react_flow, streaming


def test_chart_year_prices_use_requested_ticker_and_period(monkeypatch):
    request = Request({'type': 'http', 'headers': [], 'client': ('test', 1)})
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    seen = []
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda args: seen.append(args) or {'success': True, 'price_data': [{'Date': '2026-01-02', 'Close': 100}]}))
    result = asyncio.run(main.get_price_history_for_chart('msft', request))
    assert seen == [{'ticker': 'MSFT', 'period': '1y'}]
    assert result['ticker'] == 'MSFT' and result['adjusted'] is True
    assert result['price_data'][0]['Close'] == 100


def test_chart_year_provider_failure_never_returns_fake_data(monkeypatch):
    request = Request({'type': 'http', 'headers': [], 'client': ('test', 1)})
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda _: {'success': False, 'error': 'Market data unavailable', 'error_code': 'market_unavailable'}))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.get_price_history_for_chart('MSFT', request))
    assert exc.value.status_code == 503


def test_saved_research_outage_returns_service_unavailable(monkeypatch):
    def unavailable(_ticker):
        raise RuntimeError("private database failure")
    monkeypatch.setattr(main, "get_latest_analysis", unavailable)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.get_analysis_results("MSFT"))
    assert exc.value.status_code == 503
    assert "private database failure" not in exc.value.detail


def test_react_reports_failed_cache_write(monkeypatch):
    from stocksense.db import database
    monkeypatch.setattr(main, "validate_ticker", lambda ticker, check_exists=True: (True, None))
    monkeypatch.setattr(main.rate_limiter, "is_allowed", lambda client: True)
    monkeypatch.setattr(main, "run_react_analysis", lambda ticker: {
        "ticker": ticker, "summary": "Research complete", "sentiment_report": "Neutral"
    })
    monkeypatch.setattr(database, "save_analysis", lambda **kwargs: None)
    request = Request({'type': 'http', 'headers': [], 'client': ('test', 1)})
    result = asyncio.run(main.analyze_stock("MSFT", request, force=True, authorization=None))
    assert result["data"]["cache_saved"] is False
    assert "saving failed" in result["message"]


def mock_tools(monkeypatch, failed=None, block=None):
    results = {
        'fetch_news_headlines': {'success': True, 'headlines': ['Company reports results']},
        'fetch_fundamentals': {'success': True, 'data': {'info': {'pe_ratio': 20}}},
        'fetch_price_data': {'success': True, 'price_data': [{'Date': '2026-10-23', 'Close': 100}]},
        'analyze_sentiment': {'success': True, 'overall_sentiment': 'Neutral', 'overall_confidence': .5},
        'generate_skeptic_critique': {'success': True, 'skeptic_sentiment': 'Agree with Reservations'},
    }
    for name, result in results.items():
        def invoke(args, name=name, result=result):
            if block and name == 'fetch_news_headlines':
                block.wait(2)
            return {'success': False, 'error': 'provider unavailable'} if name == failed else result
        monkeypatch.setattr(react_flow, name, SimpleNamespace(invoke=invoke))


def test_stream_has_full_frontend_contract(monkeypatch):
    mock_tools(monkeypatch)
    async def run():
        return [event async for event in streaming.run_streaming_analysis('aapl')]
    events = asyncio.run(run())
    result = events[-1]
    assert result.event_type == streaming.StreamEventType.COMPLETED
    assert len(result.data['reasoning_steps']) == 5
    assert result.data['fundamental_data']['info']['pe_ratio'] == 20
    assert result.data['agent_type'] == 'staged'
    assert result.data['source'] == 'streaming_analysis'
    assert result.data['headlines_count'] == 1
    assert result.data['iterations'] == 1


def test_required_tool_failure_never_emits_success(monkeypatch):
    for failed in ('fetch_news_headlines', 'fetch_price_data', 'analyze_sentiment'):
        mock_tools(monkeypatch, failed)
        async def run():
            return [event async for event in streaming.run_streaming_analysis('AAPL')]
        events = asyncio.run(run())
        assert events[-1].event_type == streaming.StreamEventType.ERROR
        assert events[-1].message == ('Sentiment analysis is temporarily unavailable. Please try again.' if failed == 'analyze_sentiment' else 'provider unavailable')
        assert not any(e.event_type == streaming.StreamEventType.COMPLETED for e in events)


def test_price_error_is_actionable_without_duplicate_prefix(monkeypatch):
    mock_tools(monkeypatch)
    message = 'Ticker ZZZZZ was not found or has no price data. Check the symbol and try again.'
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda _: {'success': False, 'error': message, 'error_code': 'market_no_data'}))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('ZZZZZ')]
    events = asyncio.run(run())
    assert events[-1].message == message


def test_market_outage_is_not_misidentified_as_a_bad_ticker(monkeypatch):
    mock_tools(monkeypatch)
    message = 'Market data is temporarily unavailable. Please retry.'
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda _: {'success': False, 'error': message, 'error_code': 'market_unavailable'}))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('MSFT')]
    assert asyncio.run(run())[-1].message == message


def test_missing_news_waits_for_price_to_identify_missing_ticker(monkeypatch):
    mock_tools(monkeypatch)
    monkeypatch.setattr(react_flow, 'fetch_news_headlines', SimpleNamespace(invoke=lambda _: {'success': False, 'error': 'No news', 'error_code': 'news_no_results'}))
    monkeypatch.setattr(react_flow, 'fetch_price_data', SimpleNamespace(invoke=lambda _: {'success': False, 'error': 'Ticker ZZZZZ was not found or has no price data.', 'error_code': 'market_no_data'}))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('ZZZZZ')]
    assert asyncio.run(run())[-1].message == 'Ticker ZZZZZ was not found or has no price data.'


def test_blocked_provider_does_not_block_event_loop(monkeypatch):
    release = threading.Event()
    mock_tools(monkeypatch, block=release)
    async def run():
        stream = streaming.run_streaming_analysis('AAPL')
        await anext(stream)  # started
        await anext(stream)  # news tool started
        pending = asyncio.create_task(anext(stream))
        await asyncio.sleep(.02)
        # The provider remains blocked in its worker, while this coroutine runs.
        assert not pending.done()
        release.set()
        await asyncio.wait_for(pending, .5)
        await stream.aclose()
    asyncio.run(run())


def test_terminal_event_only_after_cache_write(monkeypatch):
    saved = []
    monkeypatch.setattr(main, 'validate_ticker', lambda ticker, check_exists=True: (True, None))
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    async def fake_stream(ticker):
        yield streaming.StreamEvent(streaming.StreamEventType.COMPLETED, data={'ticker': ticker, 'summary': 'Complete'})
    monkeypatch.setattr(streaming, 'run_streaming_analysis', fake_stream)
    from stocksense.db import database
    monkeypatch.setattr(database, 'save_analysis', lambda **kwargs: saved.append(kwargs) or {'id': 1})
    async def run():
        response = await main.analyze_stock_stream('AAPL', Request({'type': 'http', 'headers': [], 'client': ('test', 1)}))
        first = await anext(response.body_iterator)
        assert saved
        payload = json.loads(first.removeprefix('data: ').strip())
        assert payload['data']['cache_saved'] is True
    asyncio.run(run())


def test_stream_sends_heartbeat_without_marking_analysis_complete(monkeypatch):
    monkeypatch.setattr(main, 'validate_ticker', lambda ticker, check_exists=True: (True, None))
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    monkeypatch.setattr(main, 'STREAM_HEARTBEAT_SECONDS', .01)
    async def slow_stream(ticker):
        await asyncio.sleep(.04)
        yield streaming.StreamEvent(streaming.StreamEventType.ERROR, message='provider unavailable')
    monkeypatch.setattr(streaming, 'run_streaming_analysis', slow_stream)
    async def run():
        response = await main.analyze_stock_stream('MSFT', Request({'type': 'http', 'headers': [], 'client': ('test', 1)}))
        first = await anext(response.body_iterator)
        assert first == ': keep-alive\n\n'
        remaining = [part async for part in response.body_iterator]
        assert any('provider unavailable' in part for part in remaining)
    asyncio.run(run())


def test_cached_results_preserve_structured_analysis(monkeypatch):
    cached = {'id': 1, 'ticker': 'AAPL', 'analysis_summary': 'summary', 'sentiment_report': 'report',
              'timestamp': '2026-10-24T00:00:00+00:00', 'overall_sentiment': 'Bullish',
              'skeptic_report': 'skeptic', 'fundamental_data': {'info': {'pe_ratio': 20}},
              'headline_analyses': [{'headline': 'news'}]}
    monkeypatch.setattr(main, 'get_latest_analysis', lambda ticker: cached)
    result = asyncio.run(main.get_analysis_results('AAPL'))['data']
    for key in ('overall_sentiment', 'skeptic_report', 'fundamental_data', 'headline_analyses'):
        assert result[key] == cached[key]
    assert result['summary'] == 'summary'
    assert result['agent_type'] == 'unknown'


def test_missing_fundamentals_is_explicit_optional_warning(monkeypatch):
    mock_tools(monkeypatch, failed='fetch_fundamentals')
    async def run():
        return [event async for event in streaming.run_streaming_analysis('AAPL')]
    result = asyncio.run(run())[-1]
    assert result.event_type == streaming.StreamEventType.COMPLETED
    assert result.data['fundamental_data'] == {}
    assert result.data['warnings'] == ['Fundamentals are unavailable; the analysis uses news and price history.']


def test_skeptic_failure_retains_primary_without_false_agreement(monkeypatch):
    mock_tools(monkeypatch, failed='generate_skeptic_critique')
    async def run():
        return [event async for event in streaming.run_streaming_analysis('AAPL')]
    result = asyncio.run(run())[-1]
    assert result.event_type == streaming.StreamEventType.COMPLETED
    assert result.data['overall_sentiment'] == 'Neutral'
    assert result.data['skeptic_sentiment'] == ''
    assert 'not been independently challenged' in result.data['warnings'][0]


def test_stream_passes_full_sentiment_result_to_skeptic(monkeypatch):
    mock_tools(monkeypatch)
    observed = []
    sentiment = {'success': True, 'overall_sentiment': 'Bullish', 'overall_confidence': .7,
                 'key_themes': [{'theme': 'Demand growth'}], 'risks_identified': ['Supply constraints']}
    monkeypatch.setattr(react_flow, 'analyze_sentiment', SimpleNamespace(invoke=lambda args: sentiment))
    def skeptic(args):
        observed.append(args['primary_analysis'])
        return {'success': False, 'error': 'test unavailable'}
    monkeypatch.setattr(react_flow, 'generate_skeptic_critique', SimpleNamespace(invoke=skeptic))
    async def run():
        return [event async for event in streaming.run_streaming_analysis('AAPL')]
    asyncio.run(run())
    assert observed == [sentiment]


def test_terminal_event_reports_empty_cache_write_as_unsaved(monkeypatch):
    monkeypatch.setattr(main, 'validate_ticker', lambda ticker, check_exists=True: (True, None))
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    async def fake_stream(ticker):
        yield streaming.StreamEvent(streaming.StreamEventType.COMPLETED, data={'ticker': ticker, 'summary': 'Complete'})
    monkeypatch.setattr(streaming, 'run_streaming_analysis', fake_stream)
    from stocksense.db import database
    monkeypatch.setattr(database, 'save_analysis', lambda **kwargs: None)
    async def run():
        response = await main.analyze_stock_stream('AAPL', Request({'type': 'http', 'headers': [], 'client': ('test', 1)}))
        payload = json.loads((await anext(response.body_iterator)).removeprefix('data: ').strip())
        assert payload['data']['cache_saved'] is False
        assert 'could not be saved' in payload['data']['cache_warning']
    asyncio.run(run())


def test_cache_delete_uses_verified_owner_or_guest_scope(monkeypatch):
    request = Request({'type': 'http', 'headers': [], 'client': ('test', 1)})
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda client: True)
    calls = []
    monkeypatch.setattr(main, 'delete_cached_analysis', lambda ticker, token: calls.append((ticker, token)) or True)
    async def owner(authorization):
        return {'id': 'user-a', 'access_token': 'user-a-token'} if authorization else None
    monkeypatch.setattr(main, 'optional_research_user', owner)
    asyncio.run(main.delete_analysis_results('AAPL', request, None))
    asyncio.run(main.delete_analysis_results('MSFT', request, 'Bearer test'))
    assert calls == [('AAPL', None), ('MSFT', 'user-a-token')]


def test_invalid_bearer_never_falls_back_to_guest(monkeypatch):
    from stocksense.api import auth_routes
    monkeypatch.setattr(auth_routes, 'verify_user_token', lambda token: None)
    with pytest.raises(HTTPException) as error:
        asyncio.run(main.optional_research_user('Bearer bad-token'))
    assert error.value.status_code == 401
