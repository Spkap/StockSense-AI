from unittest.mock import MagicMock, patch

from stocksense.db.run_controller import (
    build_agent_run_insert,
    build_agent_run_update,
    build_agent_step_insert,
    create_agent_run,
    is_agent_run_cancelled,
)


def test_build_agent_run_insert_normalizes_ticker():
    payload = build_agent_run_insert(
        user_id="user_1",
        run_type="research_room",
        ticker=" amd ",
        question="Is the AI server thesis real?",
        input_hash="hash_1",
    )

    assert payload["user_id"] == "user_1"
    assert payload["run_type"] == "research_room"
    assert payload["ticker"] == "AMD"
    assert payload["status"] == "running"
    assert payload["question"] == "Is the AI server thesis real?"


def test_build_agent_run_update_sets_terminal_completed_at():
    payload = build_agent_run_update(
        status="completed",
        phase="completed",
        progress=1.0,
        evidence_hash="hash_1",
        final_result={"verdict": "mixed"},
    )

    assert payload["status"] == "completed"
    assert payload["final_result"]["verdict"] == "mixed"
    assert payload["completed_at"]
    assert payload["updated_at"]


def test_build_agent_step_insert_payload():
    payload = build_agent_step_insert(
        run_id="run_1",
        step_name="sec_collection",
        phase="sources",
        status="completed",
        event_type="source_completed",
        latency_ms=12,
        data={"evidence_count": 3},
        retry_count=1,
        prompt_version="2026-04-28.v1",
    )

    assert payload["run_id"] == "run_1"
    assert payload["event_type"] == "source_completed"
    assert payload["data"]["evidence_count"] == 3
    assert payload["retry_count"] == 1


def test_create_agent_run_returns_inserted_id():
    fake_client = MagicMock()
    response = MagicMock()
    response.data = [{"id": "run_123"}]
    fake_client.table.return_value.insert.return_value.execute.return_value = response

    with patch("stocksense.db.run_controller.get_supabase_admin_client", return_value=fake_client):
        run_id = create_agent_run(user_id="user_1", run_type="research_room", ticker="AMD")

    assert run_id == "run_123"


def test_is_agent_run_cancelled_returns_false_on_db_failure():
    with patch("stocksense.db.run_controller.get_supabase_admin_client", side_effect=RuntimeError("db down")):
        assert is_agent_run_cancelled("run_1") is False
