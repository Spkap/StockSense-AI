import asyncio
from unittest.mock import AsyncMock, patch

from stocksense.core.research_schemas import (
    ClaimAssessment,
    MetricEvidence,
    NarrativeTruthTest,
    ResearchEvidenceBundle,
    ResearchEvidenceItem,
    ResearchMemo,
    ResearchRoomFinal,
    ResearchThesisDraft,
)
from stocksense.orchestration.research_room import run_research_room_stream


def _bundle(evidence=True):
    return ResearchEvidenceBundle(
        ticker="AMD",
        company_snapshot={"cik": "0000002488"},
        evidence=[
            ResearchEvidenceItem(
                local_id="fact_revenue_01",
                source_type="sec_company_facts",
                source_name="SEC Company Facts",
                title="AMD Revenue",
                text="Revenue was 10 USD.",
                reliability_tier="high",
            )
        ]
        if evidence
        else [],
    )


def _final():
    return ResearchRoomFinal(
        run_id="run_1",
        ticker="AMD",
        question="Is AMD AI real?",
        company_snapshot={"cik": "0000002488"},
        narrative_test=NarrativeTruthTest(
            verdict="mixed",
            confidence="medium",
            answer="Revenue is supported, margin proof missing.",
            supported=[
                ClaimAssessment(
                    claim="Revenue supports the narrative",
                    stance="supports",
                    confidence="medium",
                    evidence_refs=["fact_revenue_01"],
                    rationale="SEC company facts include revenue.",
                )
            ],
            missing_proof=["AI margin"],
        ),
        key_metrics=[MetricEvidence(metric="Revenue", value=10, evidence_refs=["fact_revenue_01"])],
        evidence=_bundle().evidence,
        memo=ResearchMemo(verdict="mixed", executive_summary="Supported but incomplete."),
        thesis_draft=ResearchThesisDraft(
            ticker="AMD",
            thesis_summary="AMD thesis partially supported.",
            evidence_refs=["fact_revenue_01"],
        ),
    )


def test_research_room_stream_emits_expected_event_order():
    async def collect():
        events = []
        async for event in run_research_room_stream("user_1", "AMD", "Is AMD AI real?"):
            events.append(event)
        return events

    with patch("stocksense.orchestration.research_room.create_agent_run", return_value="run_1"):
        with patch("stocksense.orchestration.research_room.collect_research_evidence", new=AsyncMock(return_value=_bundle())):
            with patch("stocksense.orchestration.research_room.is_agent_run_cancelled", return_value=False):
                with patch("stocksense.orchestration.research_room.run_research_room_agents", new=AsyncMock(return_value=(_final(), {}))):
                    with patch("stocksense.orchestration.research_room.complete_agent_run"):
                        with patch("stocksense.orchestration.research_room.log_agent_run_step"):
                            with patch(
                                "stocksense.orchestration.research_room._index_and_retrieve_memory",
                                side_effect=lambda ticker, question, bundle: (bundle, {"memory_available": False}),
                            ):
                                events = asyncio.run(collect())

    types = [event.type for event in events]
    expected = [
        "started",
        "plan_completed",
        "source_completed",
        "retrieval_completed",
        "agent_completed",
        "referee_completed",
        "memo_completed",
        "completed",
    ]
    assert [event_type for event_type in types if event_type in expected] == expected
    assert events[-1].data["narrative_test"]["verdict"] == "mixed"


def test_research_room_skips_agents_when_no_evidence():
    async def collect():
        events = []
        async for event in run_research_room_stream("user_1", "AMD", "Is AMD AI real?"):
            events.append(event)
        return events

    with patch("stocksense.orchestration.research_room.create_agent_run", return_value="run_1"):
        with patch("stocksense.orchestration.research_room.collect_research_evidence", new=AsyncMock(return_value=_bundle(evidence=False))):
            with patch("stocksense.orchestration.research_room.is_agent_run_cancelled", return_value=False):
                with patch("stocksense.orchestration.research_room.run_research_room_agents", new=AsyncMock()) as agents:
                    with patch("stocksense.orchestration.research_room.complete_agent_run"):
                        with patch("stocksense.orchestration.research_room.log_agent_run_step"):
                            with patch(
                                "stocksense.orchestration.research_room._index_and_retrieve_memory",
                                side_effect=lambda ticker, question, bundle: (bundle, {"memory_available": False}),
                            ):
                                events = asyncio.run(collect())

    assert events[-1].type == "completed"
    assert events[-1].data["narrative_test"]["verdict"] == "insufficient_evidence"
    agents.assert_not_called()


def test_research_room_emits_cancelled_before_agents():
    async def collect():
        events = []
        async for event in run_research_room_stream("user_1", "AMD", "Is AMD AI real?"):
            events.append(event)
        return events

    with patch("stocksense.orchestration.research_room.create_agent_run", return_value="run_1"):
        with patch("stocksense.orchestration.research_room.collect_research_evidence", new=AsyncMock(return_value=_bundle())):
            with patch("stocksense.orchestration.research_room.is_agent_run_cancelled", return_value=True):
                with patch("stocksense.orchestration.research_room.run_research_room_agents", new=AsyncMock()) as agents:
                    with patch("stocksense.orchestration.research_room.log_agent_run_step"):
                        with patch(
                            "stocksense.orchestration.research_room._index_and_retrieve_memory",
                            side_effect=lambda ticker, question, bundle: (bundle, {"memory_available": False}),
                        ):
                            events = asyncio.run(collect())

    assert events[-1].type == "cancelled"
    agents.assert_not_called()


def test_research_room_adds_prior_memory_before_agents():
    async def collect():
        events = []
        async for event in run_research_room_stream("user_1", "AMD", "Is AMD AI real?"):
            events.append(event)
        return events

    async def fake_agents(**kwargs):
        bundle = kwargs["bundle"]
        assert any(item.source_type == "prior_run" for item in bundle.evidence)
        return _final(), {}

    with patch("stocksense.orchestration.research_room.create_agent_run", return_value="run_1"):
        with patch("stocksense.orchestration.research_room.collect_research_evidence", new=AsyncMock(return_value=_bundle())):
            with patch("stocksense.orchestration.research_room.is_agent_run_cancelled", return_value=False):
                with patch("stocksense.orchestration.research_room.search_evidence_chunks_fts", return_value=[
                    {
                        "id": "chunk_1",
                        "local_id": "fact_revenue_01",
                        "text": "Prior run found revenue proof for the AI server thesis.",
                        "reliability_tier": "high",
                        "metadata": {"title": "Prior revenue proof", "source_name": "SEC Company Facts"},
                    }
                ]):
                    with patch("stocksense.orchestration.research_room.persist_research_evidence_bundle", return_value={"documents": 1, "chunks": 1}):
                        with patch("stocksense.orchestration.research_room.run_research_room_agents", new=AsyncMock(side_effect=fake_agents)):
                            with patch("stocksense.orchestration.research_room.complete_agent_run"):
                                with patch("stocksense.orchestration.research_room.log_agent_run_step"):
                                    events = asyncio.run(collect())

    assert any(event.type == "index_completed" for event in events)
    assert events[-1].type == "completed"
