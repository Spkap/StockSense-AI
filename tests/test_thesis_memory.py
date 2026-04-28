from unittest.mock import MagicMock, patch

from stocksense.orchestration.thesis_memory import build_memory_snapshot


def test_memory_snapshot_counts_history_alerts_and_cached_analysis():
    fake_client = MagicMock()

    thesis_response = MagicMock()
    thesis_response.data = {"id": "thesis_1", "ticker": "AAPL", "thesis_summary": "AI thesis"}

    history_response = MagicMock()
    history_response.data = [{"id": "h1"}, {"id": "h2"}]

    alerts_response = MagicMock()
    alerts_response.data = [{"id": "a1"}]

    runs_response = MagicMock()
    runs_response.data = [{"id": "run_1", "final_verdict": "revise", "evidence_hash": "abc"}]

    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = thesis_response
    fake_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.side_effect = [
        history_response,
        alerts_response,
        runs_response,
    ]

    with patch("stocksense.orchestration.thesis_memory.get_supabase_client", return_value=fake_client):
        with patch("stocksense.orchestration.thesis_memory.get_latest_analysis", return_value={"ticker": "AAPL"}):
            snapshot = build_memory_snapshot("user_1", "token", "thesis_1")

    assert snapshot.thesis_history_count == 2
    assert snapshot.prior_alerts_count == 1
    assert snapshot.prior_run_found is True
    assert snapshot.latest_cached_analysis_found is True
    assert snapshot.latest_prior_verdict == "revise"


def test_memory_snapshot_degrades_when_queries_fail():
    fake_client = MagicMock()
    fake_client.table.side_effect = RuntimeError("db unavailable")

    with patch("stocksense.orchestration.thesis_memory.get_supabase_client", return_value=fake_client):
        snapshot = build_memory_snapshot("user_1", "token", "thesis_1")

    assert snapshot.prior_run_found is False
    assert snapshot.thesis_history_count == 0
