import asyncio
from unittest.mock import AsyncMock, patch

from stocksense.core.evidence_hashing import hash_text
from stocksense.core.thesis_forensics_schemas import (
    AdversarialEvaluation,
    ConvictionDiff,
    EvidenceBundle,
    EvidenceItem,
    MemorySnapshot,
)
from stocksense.orchestration.thesis_check import run_thesis_check_stream


def test_thesis_check_stream_emits_completed_event():
    async def collect():
        events = []
        async for event in run_thesis_check_stream(
            user_id="user_1",
            access_token="token",
            thesis_id="thesis_1",
            ticker="AAPL",
            thesis_text="Apple thesis",
        ):
            events.append(event)
        return events

    bundle = EvidenceBundle(
        ticker="AAPL",
        evidence=[EvidenceItem(source_type="news", source_name="NewsAPI", title="Apple", text="Apple news")],
    )

    with patch("stocksense.orchestration.thesis_check.create_thesis_check_run", return_value="run_1"):
        with patch("stocksense.orchestration.thesis_check.collect_evidence_for_ticker", new=AsyncMock(return_value=bundle)):
            with patch("stocksense.orchestration.thesis_check.build_memory_snapshot", return_value=MemorySnapshot()):
                with patch("stocksense.orchestration.thesis_check.save_evidence_bundle", return_value="hash_1"):
                    with patch("stocksense.orchestration.thesis_check.is_thesis_check_run_cancelled", return_value=False):
                        with patch("stocksense.orchestration.thesis_check.find_latest_completed_run", return_value=None):
                            with patch(
                                "stocksense.orchestration.thesis_check.run_adversarial_evaluation",
                                new=AsyncMock(return_value=AdversarialEvaluation(support=["support"])),
                            ):
                                with patch(
                                    "stocksense.orchestration.thesis_check.run_conviction_synthesis",
                                    new=AsyncMock(return_value=ConvictionDiff(verdict="hold", confidence="medium", summary="Hold thesis.")),
                                ):
                                    with patch("stocksense.orchestration.thesis_check.complete_thesis_check_run"):
                                        events = asyncio.run(collect())

    assert events[0].type == "started"
    assert events[-1].type == "completed"
    assert events[-1].data["conviction"]["verdict"] == "hold"


def test_thesis_check_skips_llm_when_no_evidence():
    async def collect():
        events = []
        async for event in run_thesis_check_stream(
            user_id="user_1",
            access_token="token",
            thesis_id="thesis_1",
            ticker="AAPL",
            thesis_text="Apple thesis",
        ):
            events.append(event)
        return events

    bundle = EvidenceBundle(ticker="AAPL", evidence=[])

    with patch("stocksense.orchestration.thesis_check.create_thesis_check_run", return_value="run_1"):
        with patch("stocksense.orchestration.thesis_check.collect_evidence_for_ticker", new=AsyncMock(return_value=bundle)):
            with patch("stocksense.orchestration.thesis_check.build_memory_snapshot", return_value=MemorySnapshot()):
                with patch("stocksense.orchestration.thesis_check.save_evidence_bundle", return_value="empty_hash"):
                    with patch("stocksense.orchestration.thesis_check.is_thesis_check_run_cancelled", return_value=False):
                        with patch(
                            "stocksense.orchestration.thesis_check.run_adversarial_evaluation",
                            new=AsyncMock(),
                        ) as evaluator:
                            with patch(
                                "stocksense.orchestration.thesis_check.run_conviction_synthesis",
                                new=AsyncMock(),
                            ) as synthesizer:
                                with patch("stocksense.orchestration.thesis_check.complete_thesis_check_run"):
                                    events = asyncio.run(collect())

    assert events[-1].type == "completed"
    assert events[-1].data["conviction"]["verdict"] == "insufficient_evidence"
    evaluator.assert_not_called()
    synthesizer.assert_not_called()


def test_thesis_check_uses_cached_result_when_evidence_and_thesis_match():
    async def collect():
        events = []
        async for event in run_thesis_check_stream(
            user_id="user_1",
            access_token="token",
            thesis_id="thesis_1",
            ticker="AAPL",
            thesis_text="Apple thesis",
        ):
            events.append(event)
        return events

    bundle = EvidenceBundle(
        ticker="AAPL",
        evidence=[EvidenceItem(source_type="news", source_name="NewsAPI", title="Apple", text="Apple news")],
    )
    previous_final = {
        "run_id": "old_run",
        "thesis_id": "thesis_1",
        "ticker": "AAPL",
        "evidence_hash": "hash_1",
        "thesis_hash": hash_text("Apple thesis"),
        "memory": MemorySnapshot().model_dump(),
        "evaluation": AdversarialEvaluation(support=["support"]).model_dump(),
        "conviction": ConvictionDiff(verdict="hold", confidence="medium", summary="Hold thesis.").model_dump(),
        "source_statuses": [],
        "cache_hit": False,
        "run_mode": "normal",
    }

    with patch("stocksense.orchestration.thesis_check.create_thesis_check_run", return_value="run_1"):
        with patch("stocksense.orchestration.thesis_check.collect_evidence_for_ticker", new=AsyncMock(return_value=bundle)):
            with patch("stocksense.orchestration.thesis_check.build_memory_snapshot", return_value=MemorySnapshot()):
                with patch("stocksense.orchestration.thesis_check.save_evidence_bundle", return_value="hash_1"):
                    with patch("stocksense.orchestration.thesis_check.is_thesis_check_run_cancelled", return_value=False):
                        with patch(
                            "stocksense.orchestration.thesis_check.find_latest_completed_run",
                            return_value={
                                "id": "old_run",
                                "evidence_hash": "hash_1",
                                "thesis_hash": previous_final["thesis_hash"],
                                "final_result": previous_final,
                            },
                        ):
                            with patch(
                                "stocksense.orchestration.thesis_check.run_adversarial_evaluation",
                                new=AsyncMock(),
                            ) as evaluator:
                                with patch(
                                    "stocksense.orchestration.thesis_check.run_conviction_synthesis",
                                    new=AsyncMock(),
                                ) as synthesizer:
                                    with patch("stocksense.orchestration.thesis_check.complete_thesis_check_run") as complete:
                                        events = asyncio.run(collect())

    assert events[-1].type == "completed"
    assert events[-1].data["cache_hit"] is True
    complete.assert_called_once()
    assert complete.call_args.kwargs["status"] == "completed_cached"
    evaluator.assert_not_called()
    synthesizer.assert_not_called()


def test_thesis_check_stream_emits_error_when_pipeline_fails():
    async def collect():
        events = []
        async for event in run_thesis_check_stream(
            user_id="user_1",
            access_token="token",
            thesis_id="thesis_1",
            ticker="AAPL",
            thesis_text="Apple thesis",
        ):
            events.append(event)
        return events

    with patch("stocksense.orchestration.thesis_check.create_thesis_check_run", return_value="run_1"):
        with patch("stocksense.orchestration.thesis_check.collect_evidence_for_ticker", side_effect=RuntimeError("boom")):
            with patch("stocksense.orchestration.thesis_check.fail_thesis_check_run"):
                events = asyncio.run(collect())

    assert events[-1].type == "error"
    assert "boom" in events[-1].message
