"""Authenticated persistence and dependency-health regressions without live user data."""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from stocksense import main
from stocksense.api import auth_routes
from stocksense.db import database, supabase_client


def test_create_thesis_persists_independent_research_snapshot(monkeypatch):
    client = MagicMock()
    client.table.return_value.insert.return_value.execute.return_value.data = [{'id': 'thesis'}]
    monkeypatch.setattr(supabase_client, 'get_user_supabase_client', lambda token: client)
    monkeypatch.setattr(supabase_client, '_create_thesis_history', lambda *args: None)
    snapshot = {'sentiment': 'Neutral', 'confidence': 0.5, 'timestamp': '2026-10-26T20:00:00Z'}
    request = {'ticker': 'MSFT', 'thesis_summary': 'A durable investment thesis', 'origin_analysis_snapshot': snapshot}
    assert supabase_client.create_thesis('user', 'token', request) == {'id': 'thesis'}
    inserted = client.table.return_value.insert.call_args.args[0]
    assert inserted['origin_analysis_snapshot'] == snapshot
    assert 'origin_analysis_id' not in inserted


def test_thesis_change_reason_only_goes_to_history(monkeypatch):
    client = MagicMock()
    current = {'id': 'thesis', 'thesis_summary': 'A durable investment case', 'conviction_level': 'medium', 'kill_criteria': []}
    client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value.data = current
    updated = {**current, 'conviction_level': 'high'}
    client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data = [updated]
    monkeypatch.setattr(supabase_client, 'get_user_supabase_client', lambda token: client)
    updates = {'conviction_level': 'high', 'change_reason': 'New primary evidence'}
    assert supabase_client.update_thesis('user', 'test-token', 'thesis', updates) == updated
    client.table.return_value.update.assert_called_once_with({'conviction_level': 'high'})
    history = client.table.return_value.insert.call_args.args[0]
    assert history['change_reason'] == 'New primary evidence'
    assert history['change_type'] == 'conviction_changed'
    assert updates['change_reason'] == 'New primary evidence'


def test_metadata_only_thesis_update_is_rejected():
    with pytest.raises(HTTPException) as error:
        auth_routes.modify_thesis('thesis', auth_routes.ThesisUpdate(change_reason='Only metadata'), {'id':'user', 'access_token':'test'})
    assert error.value.status_code == 400


def test_database_failure_is_not_reported_as_empty_cache(monkeypatch):
    client = MagicMock()
    client.table.return_value.select.return_value.order.return_value.execute.side_effect = RuntimeError('ConnectionTerminated')
    monkeypatch.setattr(database, 'get_supabase_client', lambda: client)
    with pytest.raises(RuntimeError, match='temporarily unavailable'):
        database.get_all_cached_tickers_with_timestamps()


def test_health_and_cache_endpoint_report_dependency_failure(monkeypatch):
    def fail():
        raise RuntimeError('Cached analyses are temporarily unavailable. Please retry.')
    monkeypatch.setattr(database, 'get_all_cached_tickers_with_timestamps', fail)
    health = asyncio.run(main.health_check())
    assert health['status'] == 'degraded'
    assert health['checks']['database']['status'] == 'error'
    assert 'cached_analyses' not in health['checks']['database']
    monkeypatch.setattr(main, 'get_all_cached_tickers_with_timestamps', fail)
    with pytest.raises(HTTPException) as error:
        asyncio.run(main.get_cached_tickers())
    assert error.value.status_code >= 500


def test_user_clients_are_isolated_from_shared_anonymous_client(monkeypatch):
    first, second = MagicMock(), MagicMock()
    shared = MagicMock()
    monkeypatch.setenv('SUPABASE_URL', 'https://example.supabase.co')
    monkeypatch.setenv('SUPABASE_ANON_KEY', 'public-test-key')
    factory = MagicMock(side_effect=[first, second])
    monkeypatch.setattr(supabase_client, 'create_client', factory)
    monkeypatch.setattr(supabase_client, 'get_supabase_client', lambda: shared)
    assert supabase_client.get_user_supabase_client('user-a') is first
    assert supabase_client.get_user_supabase_client('user-b') is second
    first.postgrest.auth.assert_called_once_with('user-a')
    second.postgrest.auth.assert_called_once_with('user-b')
    shared.postgrest.auth.assert_not_called()


def test_alert_reads_and_detail_share_alert_history_and_pending_is_unread(monkeypatch):
    from stocksense.core import monitor
    client = MagicMock()
    query = client.table.return_value.select.return_value
    query.eq.return_value = query
    query.order.return_value.execute.return_value.data = [{'id': 'qa-alert'}]
    query.single.return_value.execute.return_value.data = {'id': 'qa-alert'}
    monkeypatch.setattr(monitor, 'get_user_supabase_client', lambda token: client)
    monkeypatch.setattr(supabase_client, 'get_user_supabase_client', lambda token: client)
    assert monitor.get_pending_alerts('user', 'test') == [{'id': 'qa-alert'}]
    assert ('is_read', False) in [call.args for call in query.eq.call_args_list]
    assert auth_routes.get_kill_alert('qa-alert', {'id': 'user', 'access_token': 'test'}) == {'id': 'qa-alert'}
    assert all(call.args == ('alert_history',) for call in client.table.call_args_list)


def test_alert_status_update_restores_pending_and_checks_affected_rows(monkeypatch):
    from stocksense.core import monitor
    client = MagicMock()
    response = client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value
    response.data = []
    monkeypatch.setattr(monitor, 'get_user_supabase_client', lambda token: client)
    assert not monitor.update_alert_status('user', 'test', 'missing', 'pending')
    update = client.table.return_value.update.call_args.args[0]
    assert update == {'status': 'pending', 'is_read': False, 'resolved_at': None}
    response.data = [{'id': 'qa-alert'}]
    assert monitor.update_alert_status('user', 'test', 'qa-alert', 'acknowledged')
    update = client.table.return_value.update.call_args.args[0]
    assert update['is_read'] is True and update['status'] == 'acknowledged'
    assert update['resolved_at']
