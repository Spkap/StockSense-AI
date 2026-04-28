from stocksense.core.research_schemas import ResearchEvidenceBundle, ResearchEvidenceItem
from stocksense.db.evidence_memory import (
    build_research_evidence_chunk_payloads,
    build_research_evidence_document_payload,
    evidence_chunk_rows_to_prior_items,
)


def _item():
    return ResearchEvidenceItem(
        local_id="fact_revenue_01",
        source_type="sec_company_facts",
        source_name="SEC Company Facts",
        title="AMD revenue",
        text="Revenue was 10 USD for period ending 2026-03-31.",
        accession_number="0000002488-26-000010",
        filing_type="10-Q",
        metric_name="revenue",
        metric_value=10,
        period="2026-03-31",
        reliability_tier="high",
        metadata={"concept": "Revenue"},
    )


def test_build_research_evidence_document_payload_preserves_receipt_metadata():
    payload = build_research_evidence_document_payload(" amd ", _item())

    assert payload["ticker"] == "AMD"
    assert payload["source_type"] == "sec_company_facts"
    assert payload["content_hash"]
    assert payload["metadata"]["local_id"] == "fact_revenue_01"
    assert payload["raw_text"].startswith("Revenue was")


def test_build_research_evidence_chunk_payloads_keep_single_chunk_ref_stable():
    rows = build_research_evidence_chunk_payloads(
        source_document_id="doc_1",
        ticker="AMD",
        item=_item(),
    )

    assert rows[0]["local_id"] == "fact_revenue_01"
    assert rows[0]["metadata"]["original_local_id"] == "fact_revenue_01"
    assert rows[0]["reliability_tier"] == "high"


def test_evidence_chunk_rows_to_prior_items_prefixes_refs_for_agent_context():
    rows = [
        {
            "id": "chunk_1",
            "local_id": "fact_revenue_01",
            "text": "Revenue proof from a previous run.",
            "reliability_tier": "high",
            "metadata": {"title": "Prior revenue", "source_name": "SEC Company Facts"},
        }
    ]

    items = evidence_chunk_rows_to_prior_items("AMD", rows)

    assert items[0].local_id == "prior_01_fact_revenue_01"
    assert items[0].source_type == "prior_run"
    assert items[0].metadata["memory_chunk_id"] == "chunk_1"


def test_research_evidence_bundle_accepts_prior_memory_items():
    bundle = ResearchEvidenceBundle(ticker="AMD", evidence=[_item()])
    prior = evidence_chunk_rows_to_prior_items(
        "AMD",
        [{"local_id": "news_01", "text": "Prior news item", "metadata": {}}],
    )

    enriched = bundle.model_copy(update={"evidence": [*bundle.evidence, *prior]}, deep=True)

    assert any(item.source_type == "prior_run" for item in enriched.evidence)
