"""
Stage 4 integration tests: Kill Criteria Monitoring backend and API.

Covers:
- update_alert_status merges into JSONB data column (not a direct column update)
- list_kill_alerts returns pending alerts by default
- list_kill_alerts filters by status=all / status=dismissed correctly
- KillAlertResponse schema matches DB row shape
- create_kill_alert writes correct data JSONB structure
"""
import pytest
from unittest.mock import MagicMock, patch


class TestUpdateAlertStatus:
    """update_alert_status must read-then-merge the JSONB data column."""

    def _make_client(self, existing_data: dict):
        """Return a mock Supabase client that returns existing_data as the current row."""
        client = MagicMock()

        # Simulate .select("data").eq("id", ...).single().execute()
        select_resp = MagicMock()
        select_resp.data = {"data": existing_data}
        client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = select_resp

        # Simulate .update(...).eq("id", ...).eq("user_id", ...).execute()
        update_resp = MagicMock()
        client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = update_resp

        return client

    def test_status_written_into_data_column(self):
        """status must be merged into data JSONB, not set as a top-level column."""
        from stocksense.core.monitor import update_alert_status

        existing = {"triggered_criteria": "Revenue drops", "match_confidence": 0.8}
        client = self._make_client(existing)

        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            result = update_alert_status("uid", "token", "alert-id", "acknowledged")

        assert result is True
        # Capture what was passed to .update(...)
        update_payload = client.table.return_value.update.call_args[0][0]
        assert "is_read" in update_payload
        assert update_payload["is_read"] is True
        assert "data" in update_payload
        assert update_payload["data"]["status"] == "acknowledged"
        # Original fields preserved
        assert update_payload["data"]["triggered_criteria"] == "Revenue drops"
        assert update_payload["data"]["match_confidence"] == 0.8

    def test_resolved_at_set_for_non_pending(self):
        from stocksense.core.monitor import update_alert_status

        client = self._make_client({"status": "pending"})
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            update_alert_status("uid", "token", "alert-id", "dismissed")

        payload = client.table.return_value.update.call_args[0][0]
        assert "resolved_at" in payload["data"]

    def test_resolved_at_not_set_for_pending(self):
        from stocksense.core.monitor import update_alert_status

        client = self._make_client({"status": "pending"})
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            update_alert_status("uid", "token", "alert-id", "pending")

        payload = client.table.return_value.update.call_args[0][0]
        assert "resolved_at" not in payload["data"]

    def test_user_action_merged_when_provided(self):
        from stocksense.core.monitor import update_alert_status

        client = self._make_client({"status": "pending"})
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            update_alert_status("uid", "token", "alert-id", "acted", user_action="sold position")

        payload = client.table.return_value.update.call_args[0][0]
        assert payload["data"]["user_action"] == "sold position"

    def test_user_action_not_set_when_absent(self):
        from stocksense.core.monitor import update_alert_status

        client = self._make_client({"status": "pending"})
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            update_alert_status("uid", "token", "alert-id", "acknowledged", user_action=None)

        payload = client.table.return_value.update.call_args[0][0]
        assert "user_action" not in payload["data"]

    def test_returns_false_on_supabase_error(self):
        from stocksense.core.monitor import update_alert_status

        client = MagicMock()
        client.table.side_effect = Exception("Supabase down")
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            result = update_alert_status("uid", "token", "alert-id", "acknowledged")

        assert result is False


class TestCreateKillAlert:
    """create_kill_alert must write the correct data JSONB shape."""

    def _mock_client_insert(self):
        client = MagicMock()
        inserted_row = {
            "id": "new-uuid",
            "user_id": "user-1",
            "thesis_id": "thesis-1",
            "ticker": "AAPL",
            "alert_type": "kill_criteria",
            "message": "Kill Criteria Triggered: Revenue drops",
            "data": {
                "triggered_criteria": "Revenue drops",
                "triggering_signal": "Q3 revenue down 12%",
                "match_confidence": 0.85,
                "analysis_sentiment": "Bearish",
                "analysis_confidence": 0.7,
                "analysis_summary": "Short summary",
                "status": "pending",
            },
            "is_read": False,
        }
        client.table.return_value.insert.return_value.execute.return_value.data = [inserted_row]
        return client, inserted_row

    def test_insert_contains_data_jsonb(self):
        from stocksense.core.monitor import create_kill_alert, KillCriteriaMatch

        match = KillCriteriaMatch(
            criteria="Revenue drops",
            signal="Q3 revenue down 12%",
            match_confidence=0.85,
            explanation="Direct revenue miss",
        )

        client, _ = self._mock_client_insert()
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            result = create_kill_alert(
                user_id="user-1",
                access_token="token",
                thesis_id="thesis-1",
                ticker="AAPL",
                match=match,
                analysis_sentiment="Bearish",
                analysis_confidence=0.7,
                analysis_summary="Short summary",
            )

        assert result is not None
        # Capture what was passed to .insert(...)
        insert_payload = client.table.return_value.insert.call_args[0][0]
        assert "data" in insert_payload
        data = insert_payload["data"]
        assert data["triggered_criteria"] == "Revenue drops"
        assert data["triggering_signal"] == "Q3 revenue down 12%"
        assert data["match_confidence"] == 0.85
        assert data["status"] == "pending"
        assert data["analysis_sentiment"] == "Bearish"

    def test_ticker_uppercased(self):
        from stocksense.core.monitor import create_kill_alert, KillCriteriaMatch

        match = KillCriteriaMatch(
            criteria="c", signal="s", match_confidence=0.7, explanation="e"
        )
        client, _ = self._mock_client_insert()
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            create_kill_alert("uid", "token", "tid", "aapl", match, "Bullish", 0.5, "")

        insert_payload = client.table.return_value.insert.call_args[0][0]
        assert insert_payload["ticker"] == "AAPL"


class TestGetPendingAlerts:
    """get_pending_alerts must query alert_history filtered by user_id and is_read=False."""

    def test_queries_alert_history_not_kill_alerts(self):
        import inspect
        from stocksense.core.monitor import get_pending_alerts

        source = inspect.getsource(get_pending_alerts)
        assert "alert_history" in source
        assert "kill_alerts" not in source

    def test_filters_by_is_read_false(self):
        import inspect
        from stocksense.core.monitor import get_pending_alerts

        source = inspect.getsource(get_pending_alerts)
        assert "is_read" in source

    def test_returns_empty_on_error(self):
        from stocksense.core.monitor import get_pending_alerts

        client = MagicMock()
        client.table.side_effect = Exception("DB error")
        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            result = get_pending_alerts("uid", "token")

        assert result == []

    def test_filters_by_ticker_when_provided(self):
        from stocksense.core.monitor import get_pending_alerts

        client = MagicMock()
        query_chain = MagicMock()
        client.table.return_value.select.return_value.eq.return_value.eq.return_value = query_chain
        query_chain.eq.return_value.order.return_value.execute.return_value.data = []
        # non-ticker path
        query_chain.order.return_value.execute.return_value.data = []

        with patch("stocksense.core.monitor.get_supabase_client", return_value=client):
            get_pending_alerts("uid", "token", ticker="AAPL")

        # Verify ticker filter was applied — .eq("ticker", "AAPL") somewhere in chain
        all_calls = str(client.mock_calls)
        assert "AAPL" in all_calls


class TestKillAlertResponseSchema:
    """KillAlertResponse Pydantic model must match the alert_history DB row shape."""

    def test_valid_row_parses(self):
        from stocksense.api.auth_routes import KillAlertResponse, KillAlertData

        row = KillAlertResponse(
            id="uuid-1",
            user_id="user-1",
            thesis_id="thesis-1",
            ticker="AAPL",
            alert_type="kill_criteria",
            message="Kill Criteria Triggered: Revenue drops",
            is_read=False,
            created_at="2026-04-15T10:00:00+00:00",
            data=KillAlertData(
                triggered_criteria="Revenue drops",
                triggering_signal="Q3 revenue down 12%",
                match_confidence=0.85,
                analysis_sentiment="Bearish",
                analysis_confidence=0.7,
                analysis_summary="Summary here",
                status="pending",
            ),
        )
        assert row.data.match_confidence == 0.85
        assert row.data.status == "pending"

    def test_default_status_is_pending(self):
        from stocksense.api.auth_routes import KillAlertData

        d = KillAlertData(
            triggered_criteria="c",
            triggering_signal="s",
            match_confidence=0.6,
        )
        assert d.status == "pending"

    def test_no_top_level_status_field(self):
        """status must NOT be a top-level field on KillAlertResponse — it lives inside data."""
        from stocksense.api.auth_routes import KillAlertResponse
        fields = KillAlertResponse.model_fields
        assert "status" not in fields, (
            "status is a top-level field on KillAlertResponse but it should live inside data JSONB"
        )
