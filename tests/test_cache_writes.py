"""Cache writes must use the backend service role, with reads left public."""
from unittest.mock import MagicMock
import pytest
from stocksense.db import database


def test_save_analysis_uses_admin_client(monkeypatch):
    admin = MagicMock()
    admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    admin.table.return_value.insert.return_value.execute.return_value.data = [{'id': 'saved'}]
    public = MagicMock()
    monkeypatch.setattr(database, 'get_supabase_admin_client', lambda: admin)
    monkeypatch.setattr(database, 'get_supabase_client', public)
    assert database.save_analysis('aapl', 'summary', 'report') == {'id': 'saved'}
    public.assert_not_called()
    payload = admin.table.return_value.insert.call_args.args[0]
    assert payload['ticker'] == 'AAPL'


def test_existing_ticker_is_refreshed_without_duplicate_insert(monkeypatch):
    admin = MagicMock()
    admin.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "existing"}]
    monkeypatch.setattr(database, "get_supabase_admin_client", lambda: admin)
    assert database.save_analysis("aapl", "new summary", "report") == {"id": "existing"}
    admin.table.return_value.insert.assert_not_called()
    payload = admin.table.return_value.update.call_args.args[0]
    assert payload["created_at"]


def test_database_read_failure_is_not_reported_as_missing(monkeypatch):
    client = MagicMock()
    client.table.side_effect = RuntimeError("database unavailable")
    monkeypatch.setattr(database, "get_supabase_client", lambda: client)
    with pytest.raises(RuntimeError, match="database unavailable"):
        database.get_latest_analysis("MSFT")


def test_user_cache_writes_use_user_scoped_client(monkeypatch):
    client = MagicMock()
    client.table.return_value.upsert.return_value.execute.return_value.data = [{'id': 1}]
    monkeypatch.setattr(database, 'get_user_supabase_client', lambda token: client if token == 'token-a' else None)
    guest = MagicMock()
    monkeypatch.setattr(database, 'get_supabase_admin_client', guest)
    assert database.save_analysis('MSFT', 'summary', 'report', user_id='user-a', access_token='token-a') == {'id': 1}
    client.table.assert_called_with('user_analysis_cache')
    assert client.table.return_value.upsert.call_args.args[0]['user_id'] == 'user-a'
    guest.assert_not_called()


def test_partial_identity_never_falls_back_to_guest(monkeypatch):
    guest = MagicMock()
    monkeypatch.setattr(database, 'get_supabase_admin_client', guest)
    with pytest.raises(ValueError):
        database.save_analysis('MSFT', 'summary', 'report', user_id='user-a')
    guest.assert_not_called()
