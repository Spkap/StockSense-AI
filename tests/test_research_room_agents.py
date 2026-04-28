import asyncio
from unittest.mock import MagicMock, patch

from stocksense.core.research_schemas import (
    ClaimAssessment,
    ContradictionCard,
    ContradictionReview,
    MetricEvidence,
    NarrativeTruthTest,
    ResearchAnalystBrief,
    ResearchEvidenceBundle,
    ResearchEvidenceItem,
    ResearchMemo,
    ResearchMemoPackage,
    ResearchPlan,
    ResearchThesisDraft,
)
from stocksense.orchestration.research_room_agents import (
    run_research_analyst,
    run_research_planner,
    run_research_room_agents,
)


def _bundle():
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
            ),
            ResearchEvidenceItem(
                local_id="sec_10q_01",
                source_type="sec_filing",
                source_name="SEC EDGAR",
                title="AMD 10-Q",
                text="AMD filed its 10-Q.",
                reliability_tier="high",
            ),
        ],
    )


def test_research_planner_uses_structured_output():
    expected = ResearchPlan(focus_areas=["AI server revenue"], source_queries=["revenue"])
    mock_llm = MagicMock()
    structured = MagicMock()
    structured.invoke.return_value = expected
    mock_llm.with_structured_output.return_value = structured

    with patch("stocksense.orchestration.research_room_agents.get_chat_llm", return_value=mock_llm):
        result = asyncio.run(run_research_planner("Is AMD AI real?", _bundle()))

    mock_llm.with_structured_output.assert_called_once_with(ResearchPlan)
    assert result.focus_areas == ["AI server revenue"]


def test_research_analyst_repairs_invalid_refs_once():
    invalid = ResearchAnalystBrief(
        key_metrics=[MetricEvidence(metric="Revenue", value=10, evidence_refs=["missing_ref"])],
    )
    repaired = ResearchAnalystBrief(
        key_metrics=[MetricEvidence(metric="Revenue", value=10, evidence_refs=["fact_revenue_01"])],
    )
    mock_llm = MagicMock()
    structured = MagicMock()
    structured.invoke.side_effect = [invalid, repaired]
    mock_llm.with_structured_output.return_value = structured

    with patch("stocksense.orchestration.research_room_agents.get_chat_llm", return_value=mock_llm):
        result = asyncio.run(run_research_analyst("Is AMD AI real?", _bundle(), ResearchPlan()))

    assert result.key_metrics[0].evidence_refs == ["fact_revenue_01"]
    assert structured.invoke.call_count == 2


def test_research_room_agents_compose_final_output():
    plan = ResearchPlan(focus_areas=["AI server revenue"], source_queries=["revenue"])
    analyst = ResearchAnalystBrief(
        company_snapshot={"name": "AMD"},
        key_metrics=[MetricEvidence(metric="Revenue", value=10, evidence_refs=["fact_revenue_01"])],
        bull_case=[
            ClaimAssessment(
                claim="Revenue supports the narrative",
                stance="supports",
                confidence="medium",
                evidence_refs=["fact_revenue_01"],
                rationale="Revenue receipt exists.",
            )
        ],
        bear_case=[
            ClaimAssessment(
                claim="Margin proof is still missing",
                stance="unsupported",
                confidence="low",
                evidence_refs=[],
                rationale="No margin evidence in receipts.",
            )
        ],
    )
    contradictions = ContradictionReview(
        contradiction_cards=[
            ContradictionCard(
                title="Revenue without margin",
                contradiction="Narrative implies margins but receipts only show revenue.",
                severity="medium",
                evidence_refs=["fact_revenue_01"],
                why_it_matters="Margin conversion is the actual thesis test.",
            )
        ]
    )
    memo = ResearchMemoPackage(
        narrative_test=NarrativeTruthTest(
            verdict="mixed",
            confidence="medium",
            answer="Revenue is supported, margin proof is missing.",
            supported=[
                ClaimAssessment(
                    claim="Revenue supports the narrative",
                    stance="supports",
                    confidence="medium",
                    evidence_refs=["fact_revenue_01"],
                    rationale="Revenue receipt exists.",
                )
            ],
            missing_proof=["AI server margin"],
        ),
        memo=ResearchMemo(
            verdict="mixed",
            executive_summary="Supported but incomplete.",
            missing_proof=["AI server margin"],
        ),
        thesis_draft=ResearchThesisDraft(
            ticker="AMD",
            thesis_summary="AMD AI server thesis is partially supported.",
            evidence_refs=["fact_revenue_01"],
        ),
    )

    class FakeLLM:
        def __init__(self):
            self.outputs = {
                ResearchPlan: plan,
                ResearchAnalystBrief: analyst,
                ContradictionReview: contradictions,
                ResearchMemoPackage: memo,
            }

        def with_structured_output(self, schema):
            structured = MagicMock()
            structured.invoke.return_value = self.outputs[schema]
            return structured

    with patch("stocksense.orchestration.research_room_agents.get_chat_llm", return_value=FakeLLM()):
        final = asyncio.run(
            run_research_room_agents(
                run_id="run_1",
                ticker="AMD",
                question="Is AMD AI real?",
                bundle=_bundle(),
            )
        )

    assert final.run_id == "run_1"
    assert final.narrative_test.verdict == "mixed"
    assert final.key_metrics[0].evidence_refs == ["fact_revenue_01"]
