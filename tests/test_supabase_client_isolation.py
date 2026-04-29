from unittest.mock import MagicMock, patch


def test_anon_supabase_client_is_not_cached_between_user_requests(monkeypatch):
    """RLS auth mutates the client, so anon clients must not be shared."""
    from stocksense.db import supabase_client

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    created_clients = [MagicMock(name="client_one"), MagicMock(name="client_two")]

    with patch("stocksense.db.supabase_client.create_client", side_effect=created_clients) as create_client:
        first = supabase_client.get_supabase_client()
        second = supabase_client.get_supabase_client()

    assert first is created_clients[0]
    assert second is created_clients[1]
    assert first is not second
    assert create_client.call_count == 2


def test_admin_supabase_client_remains_cached(monkeypatch):
    """The service-role client is not user-token mutated and can stay cached."""
    from stocksense.db import supabase_client

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")
    supabase_client.get_supabase_admin_client.cache_clear()

    with patch("stocksense.db.supabase_client.create_client", return_value=MagicMock()) as create_client:
        first = supabase_client.get_supabase_admin_client()
        second = supabase_client.get_supabase_admin_client()

    assert first is second
    assert create_client.call_count == 1

    supabase_client.get_supabase_admin_client.cache_clear()
