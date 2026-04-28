from tests.evals.golden_set import GOLDEN_SET
from stocksense.core.research_schemas import (
    ClaimAssessment,
    MetricEvidence,
    NarrativeTruthTest,
    ResearchEvidenceItem,
    ResearchMemo,
    ResearchRoomFinal,
    ResearchThesisDraft,
)


def test_amd_research_room_demo_contract_exists():
    case = next(item for item in GOLDEN_SET if item["ticker"] == "AMD")

    assert case["research_room_question"] == "Is AMD's AI server thesis real, or is the market over-narrating it?"
    assert case["research_room_expectations"]["must_include_sec_or_company_facts"] is True


def test_research_room_demo_result_has_required_contract_fields():
    final = ResearchRoomFinal(
        run_id="run_amd",
        ticker="AMD",
        question="Is AMD's AI server thesis real, or is the market over-narrating it?",
        company_snapshot={"cik": "0000002488"},
        evidence=[
            ResearchEvidenceItem(
                local_id="fact_revenue_01",
                source_type="sec_company_facts",
                source_name="SEC Company Facts",
                title="AMD revenue",
                text="Revenue fact receipt.",
                reliability_tier="high",
            )
        ],
        narrative_test=NarrativeTruthTest(
            verdict="mixed",
            confidence="medium",
            answer="The AI server narrative has evidence, but margin proof is still missing.",
            supported=[
                ClaimAssessment(
                    claim="Revenue evidence supports part of the AI server thesis.",
                    stance="supports",
                    confidence="medium",
                    evidence_refs=["fact_revenue_01"],
                    rationale="SEC company facts provide a revenue receipt.",
                )
            ],
            missing_proof=["Segment-level AI server margin proof"],
        ),
        key_metrics=[MetricEvidence(metric="Revenue", value=10, evidence_refs=["fact_revenue_01"])],
        memo=ResearchMemo(
            verdict="mixed",
            executive_summary="Supported but incomplete.",
            missing_proof=["Segment-level AI server margin proof"],
        ),
        thesis_draft=ResearchThesisDraft(
            ticker="AMD",
            thesis_summary="AMD AI server thesis is partially supported but needs margin proof.",
            evidence_refs=["fact_revenue_01"],
        ),
    )

    assert final.narrative_test.verdict
    assert any(item.source_type in {"sec_filing", "sec_company_facts"} for item in final.evidence)
    assert final.narrative_test.missing_proof
    assert final.thesis_draft.thesis_summary
