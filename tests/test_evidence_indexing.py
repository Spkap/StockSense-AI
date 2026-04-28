from stocksense.core.evidence_indexing import (
    build_evidence_local_id,
    build_fts_query_payload,
    chunk_text,
    hash_source_content,
    rank_evidence_chunks,
)


def test_stable_content_hash_for_json_key_order():
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}

    assert hash_source_content(left) == hash_source_content(right)


def test_chunk_size_stays_under_limit():
    text = " ".join(["revenue growth margin cash debt"] * 400)
    chunks = chunk_text(text, max_chars=1200, overlap_chars=120)

    assert chunks
    assert all(len(chunk) <= 1200 for chunk in chunks)


def test_build_local_ids_for_sec_and_fact_sources():
    assert build_evidence_local_id("sec", 1, filing_type="10-Q") == "sec_10q_01"
    assert build_evidence_local_id("fact", 1, filing_type="revenue") == "fact_revenue_01"


def test_fts_query_payload_builder():
    payload = build_fts_query_payload(" amd ", " AI server revenue ", limit=5)

    assert payload == {"ticker": "AMD", "query": "AI server revenue", "limit": 5}


def test_evidence_refs_stable_across_repeated_chunking():
    text = " ".join(["AI accelerator revenue grew while gaming weakened."] * 80)
    first = chunk_text(text, max_chars=400, overlap_chars=80)
    second = chunk_text(text, max_chars=400, overlap_chars=80)

    assert first == second


def test_rank_evidence_chunks_prefers_query_overlap_and_reliability():
    chunks = [
        {"local_id": "news_01", "text": "Gaming demand weakened", "reliability_tier": "medium"},
        {"local_id": "sec_10q_01", "text": "AI server revenue grew materially", "reliability_tier": "high"},
    ]

    ranked = rank_evidence_chunks("AI server revenue", chunks)

    assert ranked[0]["local_id"] == "sec_10q_01"
