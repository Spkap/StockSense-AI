import asyncio
import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from stocksense import main
from stocksense.db import database
from stocksense.orchestration import streaming


def test_debate_write_updates_existing_owner_row_without_inserting(monkeypatch):
    client = MagicMock()
    client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    monkeypatch.setattr(database, 'get_user_supabase_client', lambda token: client)
    assert not database.save_debate('msft', {'ticker': 'MSFT'}, 42, 'user-token')
    client.table.assert_called_with('user_analysis_cache')
    client.table.return_value.insert.assert_not_called()
    client.table.return_value.update.return_value.eq.assert_called_with('ticker', 'MSFT')
    client.table.return_value.update.return_value.eq.return_value.eq.assert_called_with('id', 42)


def test_guest_and_user_reads_use_separate_clients(monkeypatch):
    guest, user = MagicMock(), MagicMock()
    for client, value in ((guest, 'guest'), (user, 'private')):
        client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = [{'debate_result': {'value': value}}]
    monkeypatch.setattr(database, 'get_supabase_client', lambda: guest)
    monkeypatch.setattr(database, 'get_user_supabase_client', lambda token: user)
    assert database.get_saved_debate('MSFT') == {'value': 'guest'}
    assert database.get_saved_debate('MSFT', 'user-token') == {'value': 'private'}
    guest.table.assert_called_with('analysis_cache')
    user.table.assert_called_with('user_analysis_cache')


def test_debate_stream_saves_before_completion_and_reports_failure(monkeypatch):
    monkeypatch.setattr(main.rate_limiter, 'is_allowed', lambda _: True)
    async def owner(_): return {'id': 'a', 'access_token': 'user-token'}
    monkeypatch.setattr(main, 'optional_research_user', owner)
    async def fake_stream(ticker):
        yield streaming.StreamEvent(streaming.StreamEventType.DEBATE_COMPLETED, data={'ticker': ticker})
    monkeypatch.setattr(streaming, 'run_streaming_debate_analysis', fake_stream)
    calls = []
    monkeypatch.setattr(database, 'get_research_id', lambda ticker, token: 42)
    monkeypatch.setattr(database, 'save_debate', lambda ticker, data, row_id, token: calls.append((ticker, row_id, token)) or False)
    async def run():
        request = Request({'type': 'http', 'headers': [], 'client': ('test', 1)})
        response = await main.analyze_stock_debate_stream('MSFT', request, 'Bearer token')
        payload = json.loads((await anext(response.body_iterator)).removeprefix('data: ').strip())
        assert calls == [('MSFT', 42, 'user-token')]
        assert payload['data']['cache_saved'] is False
        assert 'no longer available' in payload['data']['cache_warning']
        await response.body_iterator.aclose()
    asyncio.run(run())


def test_saved_debate_invalid_token_does_not_read_guest(monkeypatch):
    async def invalid(_): raise HTTPException(status_code=401, detail='Invalid token')
    monkeypatch.setattr(main, 'optional_research_user', invalid)
    read = MagicMock()
    monkeypatch.setattr(database, 'get_saved_debate', read)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(main.get_debate_result('MSFT', 'Bearer invalid'))
    assert exc.value.status_code == 401
    read.assert_not_called()
