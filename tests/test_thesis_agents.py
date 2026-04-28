import asyncio
from unittest.mock import MagicMock, patch

from stocksense.core.thesis_forensics_schemas import (
    AdversarialEvaluation,
    ClaimAssessment,
    ConvictionDiff,
    EvidenceBundle,
    EvidenceItem,
    MemorySnapshot,
)
from stocksense.orchestration.thesis_agents import run_adversarial_evaluation, run_conviction_synthesis


def test_adversarial_evaluation_uses_structured_output():
    expected = AdversarialEvaluation(
        support=["Services growth supports durability."],
        opposition=["Valuation leaves little margin of safety."],
        contradictions=["AI margin claim lacks direct evidence."],
        missing_evidence=["Latest segment margin details."],
        human_review_items=["Confirm AI impact claim."],
        claim_assessments=[
            ClaimAssessment(
                claim="Services growth supports durability.",
                stance="supports",
                confidence="medium",
                evidence_refs=["news_01"],
                rationale="The provided news item supports durability.",
            )
        ],
    )

    mock_llm = MagicMock()
    structured = MagicMock()
    mock_llm.with_structured_output.return_value = structured
    structured.invoke.return_value = expected

    bundle = EvidenceBundle(
        ticker="AAPL",
        evidence=[
            EvidenceItem(local_id="news_01", source_type="news", source_name="NewsAPI", title="Apple AI", text="Apple announced AI features.")
        ],
    )

    with patch("stocksense.orchestration.thesis_agents.get_chat_llm", return_value=mock_llm):
        result = asyncio.run(run_adversarial_evaluation("AAPL AI thesis", bundle, MemorySnapshot()))

    mock_llm.with_structured_output.assert_called_once_with(AdversarialEvaluation)
    assert result.contradictions == ["AI margin claim lacks direct evidence."]


def test_conviction_synthesis_uses_structured_output():
    expected = ConvictionDiff(
        verdict="revise",
        confidence="medium",
        strengthened_claims=["Services claim remains intact."],
        weakened_claims=["AI margin claim weakened."],
        broken_claims=[],
        unsupported_claims=["No direct AI margin evidence."],
        summary="Revise thesis before relying on it.",
        next_actions=["Edit thesis", "Monitor next earnings"],
        claim_assessments=[
            ClaimAssessment(
                claim="AI margin claim weakened.",
                stance="weakens",
                confidence="medium",
                evidence_refs=["news_01"],
                rationale="The evidence does not directly support margin expansion.",
            )
        ],
    )

    mock_llm = MagicMock()
    structured = MagicMock()
    mock_llm.with_structured_output.return_value = structured
    structured.invoke.return_value = expected

    evaluation = AdversarialEvaluation(
        support=["Services growth"],
        opposition=["Valuation risk"],
        contradictions=["AI margin claim lacks direct evidence"],
        missing_evidence=[],
        human_review_items=[],
    )

    bundle = EvidenceBundle(
        ticker="AAPL",
        evidence=[
            EvidenceItem(
                local_id="news_01",
                source_type="news",
                source_name="NewsAPI",
                title="Apple AI",
                text="Apple announced AI features.",
            )
        ],
    )

    with patch("stocksense.orchestration.thesis_agents.get_chat_llm", return_value=mock_llm):
        result = asyncio.run(run_conviction_synthesis("AAPL thesis", bundle, MemorySnapshot(), evaluation))

    mock_llm.with_structured_output.assert_called_once_with(ConvictionDiff)
    assert result.verdict == "revise"


def test_adversarial_evaluation_repairs_invalid_evidence_refs_once():
    invalid = AdversarialEvaluation(
        claim_assessments=[
            ClaimAssessment(
                claim="AI features support the thesis",
                stance="supports",
                confidence="medium",
                evidence_refs=["missing_ref"],
                rationale="Bad ref",
            )
        ]
    )
    repaired = AdversarialEvaluation(
        claim_assessments=[
            ClaimAssessment(
                claim="AI features support the thesis",
                stance="supports",
                confidence="medium",
                evidence_refs=["news_01"],
                rationale="News item supports the claim.",
            )
        ]
    )

    mock_llm = MagicMock()
    structured = MagicMock()
    mock_llm.with_structured_output.return_value = structured
    structured.invoke.side_effect = [invalid, repaired]

    bundle = EvidenceBundle(
        ticker="AAPL",
        evidence=[
            EvidenceItem(
                local_id="news_01",
                source_type="news",
                source_name="NewsAPI",
                title="Apple AI",
                text="Apple announced AI features.",
            )
        ],
    )

    with patch("stocksense.orchestration.thesis_agents.get_chat_llm", return_value=mock_llm):
        result = asyncio.run(run_adversarial_evaluation("AAPL AI thesis", bundle, MemorySnapshot()))

    assert result.claim_assessments[0].evidence_refs == ["news_01"]
    assert structured.invoke.call_count == 2
