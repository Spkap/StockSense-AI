import pytest
from pydantic import ValidationError

from stocksense.core.research_schemas import (
    ClaimAssessment,
    ContradictionCard,
    MetricEvidence,
    NarrativeTruthTest,
    ResearchMemo,
    ResearchRoomFinal,
    ResearchThesisDraft,
)


def test_grounded_claim_requires_evidence_refs():
    with pytest.raises(ValidationError):
        ClaimAssessment(
            claim="AI revenue supports the narrative",
            stance="supports",
            confidence="medium",
            evidence_refs=[],
            rationale="Missing citation",
        )


def test_unsupported_claim_must_not_include_evidence_refs():
    with pytest.raises(ValidationError):
        ClaimAssessment(
            claim="Unproven claim",
            stance="unsupported",
            confidence="low",
            evidence_refs=["sec_10q_01"],
            rationale="Unsupported means no receipt",
        )


def test_metric_evidence_requires_receipt():
    with pytest.raises(ValidationError):
        MetricEvidence(metric="Revenue", value=10, period="2026-Q1", evidence_refs=[])


def test_final_research_room_shape_accepts_supported_narrative():
    final = ResearchRoomFinal(
        run_id="run_1",
        ticker="AMD",
        question="Is the AI server thesis real?",
        company_snapshot={"cik": "0000002488"},
        narrative_test=NarrativeTruthTest(
            verdict="mixed",
            confidence="medium",
            answer="AI server evidence exists, but margin proof is still incomplete.",
            supported=[
                ClaimAssessment(
                    claim="Revenue supports the AI server narrative",
                    stance="supports",
                    confidence="medium",
                    evidence_refs=["fact_revenue_01"],
                    rationale="Revenue fact supports directionality.",
                )
            ],
            missing_proof=["Segment-level AI server margin"],
        ),
        key_metrics=[
            MetricEvidence(metric="Revenue", value=10, period="2026-Q1", evidence_refs=["fact_revenue_01"])
        ],
        contradiction_cards=[
            ContradictionCard(
                title="Margin gap",
                contradiction="Narrative talks margins but evidence is only revenue.",
                severity="medium",
                evidence_refs=["fact_revenue_01"],
                why_it_matters="Revenue without margin can still disappoint.",
            )
        ],
        memo=ResearchMemo(
            verdict="mixed",
            executive_summary="Evidence is real but incomplete.",
            missing_proof=["Segment-level AI server margin"],
        ),
        thesis_draft=ResearchThesisDraft(
            ticker="AMD",
            thesis_summary="AMD AI server thesis is partially supported but needs margin proof.",
            evidence_refs=["fact_revenue_01"],
        ),
    )

    assert final.narrative_test.verdict == "mixed"
    assert final.thesis_draft.ticker == "AMD"
