from unittest.mock import MagicMock, patch

from stocksense.core.thesis_forensics_schemas import (
    AdversarialEvaluation,
    ConvictionDiff,
    MemorySnapshot,
    ThesisCheckFinal,
)
from stocksense.db.thesis_forensics import build_final_update, build_run_insert, create_thesis_check_run


def test_build_run_insert_payload():
    payload = build_run_insert(user_id="user_1", thesis_id="thesis_1", ticker="AAPL")

    assert payload["user_id"] == "user_1"
    assert payload["thesis_id"] == "thesis_1"
    assert payload["ticker"] == "AAPL"
    assert payload["status"] == "running"


def test_build_final_update_payload():
    final = ThesisCheckFinal(
        run_id="run_1",
        thesis_id="thesis_1",
        ticker="AAPL",
        evidence_hash="hash_1",
        memory=MemorySnapshot(),
        evaluation=AdversarialEvaluation(),
        conviction=ConvictionDiff(
            verdict="revise",
            confidence="medium",
            summary="Revise thesis.",
            next_actions=["Edit thesis"],
        ),
    )

    payload = build_final_update(final)

    assert payload["status"] == "completed"
    assert payload["final_verdict"] == "revise"
    assert payload["final_confidence"] == "medium"
    assert payload["evidence_hash"] == "hash_1"


def test_create_thesis_check_run_returns_inserted_id():
    fake_client = MagicMock()
    response = MagicMock()
    response.data = [{"id": "run_123"}]
    fake_client.table.return_value.insert.return_value.execute.return_value = response

    with patch("stocksense.db.thesis_forensics.get_supabase_admin_client", return_value=fake_client):
        run_id = create_thesis_check_run("user_1", "thesis_1", "AAPL")

    assert run_id == "run_123"
