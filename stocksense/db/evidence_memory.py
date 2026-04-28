"""
Source-document and evidence-chunk persistence helpers.
"""

from __future__ import annotations

from typing import Any

from stocksense.core.evidence_indexing import chunk_text, hash_source_content
from stocksense.core.research_schemas import ResearchEvidenceBundle, ResearchEvidenceItem
from stocksense.db.supabase_client import get_supabase_admin_client


def build_source_document_payload(
    *,
    ticker: str,
    source_type: str,
    source_name: str,
    title: str,
    cik: str | None = None,
    url: str | None = None,
    accession_number: str | None = None,
    filing_type: str | None = None,
    period: str | None = None,
    filed_at: str | None = None,
    published_at: str | None = None,
    raw_text: str | None = None,
    raw_json: dict | list | None = None,
    metadata: dict | None = None,
    content_hash: str | None = None,
) -> dict[str, Any]:
    hash_input = raw_json if raw_json is not None else raw_text or title
    return {
        "ticker": ticker.upper().strip(),
        "cik": cik,
        "source_type": source_type,
        "source_name": source_name,
        "title": title,
        "url": url,
        "accession_number": accession_number,
        "filing_type": filing_type,
        "period": period,
        "filed_at": filed_at,
        "published_at": published_at,
        "content_hash": content_hash or hash_source_content(hash_input),
        "raw_text": raw_text,
        "raw_json": raw_json,
        "metadata": metadata or {},
    }


def build_evidence_chunk_payloads(
    *,
    source_document_id: str,
    ticker: str,
    chunks: list[str],
    local_id_prefix: str,
    reliability_tier: str = "medium",
    metadata: dict | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            "source_document_id": source_document_id,
            "ticker": ticker.upper().strip(),
            "local_id": f"{local_id_prefix}_{index + 1:02d}",
            "chunk_index": index,
            "text": chunk,
            "reliability_tier": reliability_tier,
            "metadata": metadata or {},
        }
        for index, chunk in enumerate(chunks)
    ]


def upsert_source_document(**kwargs) -> dict[str, Any]:
    client = get_supabase_admin_client()
    payload = build_source_document_payload(**kwargs)
    response = client.table("source_documents").upsert(payload, on_conflict="content_hash").execute()
    return response.data[0]


def insert_evidence_chunks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    client = get_supabase_admin_client()
    response = client.table("evidence_chunks").upsert(rows, on_conflict="source_document_id,local_id").execute()
    return response.data or []


def build_research_evidence_document_payload(ticker: str, item: ResearchEvidenceItem) -> dict[str, Any]:
    metadata = {
        **(item.metadata or {}),
        "local_id": item.local_id,
        "source_type": item.source_type,
        "source_name": item.source_name,
        "title": item.title,
        "reliability_tier": item.reliability_tier,
    }
    content_hash = hash_source_content(
        {
            "ticker": ticker.upper().strip(),
            "source_type": item.source_type,
            "title": item.title,
            "text": item.text,
            "url": item.url,
            "accession_number": item.accession_number,
            "metric_name": item.metric_name,
            "period": item.period,
        }
    )
    return build_source_document_payload(
        ticker=ticker,
        source_type=item.source_type,
        source_name=item.source_name,
        title=item.title,
        url=item.url,
        accession_number=item.accession_number,
        filing_type=item.filing_type,
        period=item.period,
        published_at=item.published_at,
        raw_text=item.text,
        raw_json=item.metadata if item.metadata else None,
        metadata=metadata,
        content_hash=content_hash,
    )


def build_research_evidence_chunk_payloads(
    *,
    source_document_id: str,
    ticker: str,
    item: ResearchEvidenceItem,
) -> list[dict[str, Any]]:
    chunks = chunk_text(item.text, max_chars=1400, overlap_chars=140) or [item.text]
    metadata = {
        **(item.metadata or {}),
        "source_name": item.source_name,
        "source_type": item.source_type,
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at,
        "accession_number": item.accession_number,
        "filing_type": item.filing_type,
        "metric_name": item.metric_name,
        "metric_value": item.metric_value,
        "period": item.period,
        "original_local_id": item.local_id,
    }
    return [
        {
            "source_document_id": source_document_id,
            "ticker": ticker.upper().strip(),
            "local_id": item.local_id if len(chunks) == 1 else f"{item.local_id}_{index + 1:02d}",
            "chunk_index": index,
            "text": text,
            "reliability_tier": item.reliability_tier,
            "metadata": metadata,
        }
        for index, text in enumerate(chunks)
    ]


def persist_research_evidence_bundle(bundle: ResearchEvidenceBundle) -> dict[str, int]:
    """Persist source documents and chunks for future Research Room retrieval."""
    documents = 0
    chunks = 0
    client = get_supabase_admin_client()

    for item in bundle.evidence:
        if item.source_type == "prior_run":
            continue
        document_payload = build_research_evidence_document_payload(bundle.ticker, item)
        document_response = (
            client.table("source_documents")
            .upsert(document_payload, on_conflict="content_hash")
            .execute()
        )
        document = (document_response.data or [{}])[0]
        document_id = document.get("id")
        if not document_id:
            continue
        documents += 1
        chunk_rows = build_research_evidence_chunk_payloads(
            source_document_id=document_id,
            ticker=bundle.ticker,
            item=item,
        )
        chunks += len(insert_evidence_chunks(chunk_rows))

    return {"documents": documents, "chunks": chunks}


def evidence_chunk_rows_to_prior_items(
    ticker: str,
    rows: list[dict[str, Any]],
    *,
    existing_local_ids: set[str] | None = None,
    max_items: int = 8,
) -> list[ResearchEvidenceItem]:
    existing = existing_local_ids or set()
    prior_items: list[ResearchEvidenceItem] = []
    seen_text_hashes: set[str] = set()

    for row in rows:
        text = str(row.get("text") or "").strip()
        if not text:
            continue
        text_hash = hash_source_content(text)
        if text_hash in seen_text_hashes:
            continue
        seen_text_hashes.add(text_hash)

        metadata = row.get("metadata") or {}
        base_local_id = str(row.get("local_id") or metadata.get("original_local_id") or "memory")
        local_id = f"prior_{len(prior_items) + 1:02d}_{base_local_id}"
        if local_id in existing:
            continue
        reliability_tier = str(row.get("reliability_tier") or metadata.get("reliability_tier") or "medium")
        if reliability_tier not in {"high", "medium", "low"}:
            reliability_tier = "medium"

        prior_items.append(
            ResearchEvidenceItem(
                local_id=local_id,
                source_type="prior_run",
                source_name=str(metadata.get("source_name") or "Evidence Memory"),
                title=str(metadata.get("title") or f"{ticker.upper()} prior evidence"),
                text=text,
                url=metadata.get("url"),
                published_at=metadata.get("published_at"),
                accession_number=metadata.get("accession_number"),
                filing_type=metadata.get("filing_type"),
                metric_name=metadata.get("metric_name"),
                metric_value=metadata.get("metric_value"),
                period=metadata.get("period"),
                reliability_tier=reliability_tier,
                metadata={
                    **metadata,
                    "memory_chunk_id": row.get("id"),
                    "memory_local_id": base_local_id,
                    "memory_ticker": ticker.upper().strip(),
                },
            )
        )
        if len(prior_items) >= max_items:
            break

    return prior_items


def search_evidence_chunks_fts(ticker: str, query: str, limit: int = 12) -> list[dict[str, Any]]:
    client = get_supabase_admin_client()
    response = (
        client.table("evidence_chunks")
        .select("*")
        .eq("ticker", ticker.upper().strip())
        .text_search("fts", query, options={"type": "websearch"})
        .limit(limit)
        .execute()
    )
    return response.data or []


def get_evidence_chunks_by_ids(ticker: str, local_ids: list[str]) -> list[dict[str, Any]]:
    if not local_ids:
        return []
    client = get_supabase_admin_client()
    response = (
        client.table("evidence_chunks")
        .select("*")
        .eq("ticker", ticker.upper().strip())
        .in_("local_id", local_ids)
        .execute()
    )
    return response.data or []
