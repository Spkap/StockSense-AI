from pydantic import ValidationError

from stocksense.core.thesis_forensics_schemas import (
    AdversarialEvaluation,
    ConvictionDiff,
    EvidenceBundle,
    EvidenceItem,
    MemorySnapshot,
    SourceStatus,
    ThesisCheckFinal,
)


def test_evidence_item_requires_supported_source_type():
    item = EvidenceItem(
        source_type="news",
        source_name="NewsAPI",
        title="AAPL expands AI features",
        text="Apple announced new AI features.",
        url="https://example.com/aapl-ai",
        published_at="2026-04-28T00:00:00Z",
        reliability_tier="medium",
    )

    assert item.source_type == "news"
    assert item.reliability_tier == "medium"


def test_evidence_item_rejects_unknown_source_type():
    try:
        EvidenceItem(
            source_type="forum",
            source_name="Forum",
            title="Rumor",
            text="Unverified post",
            reliability_tier="low",
        )
    except ValidationError as exc:
        assert "source_type" in str(exc)
    else:
        raise AssertionError("EvidenceItem accepted unsupported source_type")


def test_evidence_bundle_tracks_partial_failures():
    bundle = EvidenceBundle(
        ticker="AAPL",
        source_statuses=[
            SourceStatus(source_type="news", status="ok", latency_ms=120),
            SourceStatus(source_type="fundamentals", status="failed", latency_ms=6000, error="timeout"),
        ],
        evidence=[
            EvidenceItem(
                source_type="news",
                source_name="NewsAPI",
                title="Apple reports earnings",
                text="Apple reported earnings.",
                reliability_tier="medium",
            )
        ],
    )

    assert bundle.has_partial_failure is True
    assert bundle.available_source_types == ["news"]


def test_conviction_diff_supports_core_sections():
    diff = ConvictionDiff(
        verdict="revise",
        confidence="medium",
        strengthened_claims=["Services revenue remains durable."],
        weakened_claims=["Hardware replacement cycle looks slower."],
        broken_claims=[],
        unsupported_claims=["AI margin impact is not evidenced."],
        summary="The thesis should be revised, not invalidated.",
        next_actions=["Revise AI margin claim", "Monitor next earnings call"],
    )

    assert diff.verdict == "revise"
    assert "AI margin" in diff.unsupported_claims[0]


def test_final_result_contains_run_metadata():
    final = ThesisCheckFinal(
        run_id="run_123",
        thesis_id="thesis_123",
        ticker="AAPL",
        evidence_hash="abc123",
        memory=MemorySnapshot(
            prior_run_found=False,
            prior_alerts_count=0,
            thesis_history_count=1,
            latest_cached_analysis_found=True,
        ),
        evaluation=AdversarialEvaluation(
            support=["Strong installed base"],
            opposition=["Valuation is demanding"],
            contradictions=["AI claim lacks direct evidence"],
            missing_evidence=["Latest 10-Q segment margin detail"],
            human_review_items=["Confirm AI margin claim"],
        ),
        conviction=ConvictionDiff(
            verdict="revise",
            confidence="medium",
            strengthened_claims=[],
            weakened_claims=["AI margin claim weaker than expected"],
            broken_claims=[],
            unsupported_claims=["No direct evidence for AI margin expansion"],
            summary="Revise the thesis before relying on it.",
            next_actions=["Edit thesis", "Run deep review"],
        ),
    )

    assert final.ticker == "AAPL"
    assert final.conviction.verdict == "revise"
