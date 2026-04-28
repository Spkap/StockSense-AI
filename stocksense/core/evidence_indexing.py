"""
Evidence hashing, chunking, and lightweight retrieval helpers.

The MVP ships lexical ranking first. The database schema already has nullable
embedding columns so semantic retrieval can be added without another data
model rewrite.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9$%.-]+")


def _stable_payload(value: str | dict | list | Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def hash_source_content(text_or_json: str | dict | list | Any) -> str:
    payload = _stable_payload(text_or_json)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def chunk_text(text: str, max_chars: int = 1100, overlap_chars: int = 120) -> list[str]:
    normalized = " ".join((text or "").split())
    if not normalized:
        return []
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    overlap_chars = max(0, min(overlap_chars, max_chars // 2))

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        hard_end = min(len(normalized), start + max_chars)
        end = hard_end
        if hard_end < len(normalized):
            boundary = normalized.rfind(" ", start, hard_end)
            if boundary > start + max_chars * 0.55:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        next_start = max(0, end - overlap_chars)
        if next_start <= start:
            next_start = end
        start = next_start
    return chunks


def build_evidence_local_id(source_type: str, index: int, filing_type: str | None = None) -> str:
    prefix = source_type.lower().strip().replace("-", "_").replace(" ", "_")
    if prefix in {"sec", "sec_filing", "sec_filings"}:
        prefix = "sec"
        if filing_type:
            prefix = f"{prefix}_{filing_type.lower().replace('-', '').replace(' ', '')}"
    elif prefix in {"fact", "facts", "sec_company_facts"}:
        prefix = "fact"
        if filing_type:
            prefix = f"{prefix}_{filing_type.lower().replace('-', '_').replace(' ', '_')}"
    return f"{prefix}_{index:02d}"


def tokenize_query(query: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(query or "") if len(token) > 1}


def rank_evidence_chunks(query: str, chunks: list[dict[str, Any]], max_items: int = 12) -> list[dict[str, Any]]:
    query_terms = tokenize_query(query)
    if not query_terms:
        return chunks[:max_items]

    tier_boost = {"high": 2.0, "medium": 1.0, "low": 0.25}

    def score(chunk: dict[str, Any]) -> tuple[float, str]:
        text_terms = tokenize_query(chunk.get("text", ""))
        overlap = len(query_terms & text_terms)
        source_boost = tier_boost.get(str(chunk.get("reliability_tier", "medium")), 1.0)
        return overlap * 10 + source_boost, str(chunk.get("local_id", ""))

    ranked = sorted(chunks, key=score, reverse=True)
    return [chunk for chunk in ranked if score(chunk)[0] > 0][:max_items]


def build_fts_query_payload(ticker: str, query: str, limit: int = 12) -> dict[str, Any]:
    return {
        "ticker": ticker.upper().strip(),
        "query": " ".join(query.split()),
        "limit": limit,
    }
