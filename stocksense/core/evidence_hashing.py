"""
Stable evidence hashing for fast unchanged-run detection.
"""

from __future__ import annotations

import hashlib
import json

from stocksense.core.thesis_forensics_schemas import EvidenceItem


def _canonical_item(item: EvidenceItem) -> dict:
    return {
        "source_type": item.source_type,
        "source_name": item.source_name,
        "title": item.title.strip(),
        "text": item.text.strip(),
        "url": item.url or "",
        "published_at": item.published_at or "",
        "reliability_tier": item.reliability_tier,
    }


def hash_evidence_items(items: list[EvidenceItem]) -> str:
    canonical = sorted(
        [_canonical_item(item) for item in items],
        key=lambda value: (
            value["source_type"],
            value["source_name"],
            value["title"],
            value["url"],
            value["text"],
        ),
    )
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def hash_text(value: str) -> str:
    normalized = " ".join(value.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def has_material_evidence_change(previous_hash: str | None, current_hash: str) -> bool:
    if not previous_hash:
        return True
    return previous_hash != current_hash
