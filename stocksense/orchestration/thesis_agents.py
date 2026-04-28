"""
Collapsed LLM roles for fast thesis checks.

v1 uses two calls:
1. adversarial evaluation
2. conviction synthesis
"""

from __future__ import annotations

import asyncio
import json

from langchain_core.messages import HumanMessage, SystemMessage

from stocksense.core.config import get_chat_llm
from stocksense.core.thesis_forensics_schemas import (
    AdversarialEvaluation,
    ClaimAssessment,
    ConvictionDiff,
    EvidenceBundle,
    MemorySnapshot,
)


ADVERSARIAL_EVALUATOR_PROMPT_VERSION = "2026-04-28.v2"
CONVICTION_SYNTHESIZER_PROMPT_VERSION = "2026-04-28.v2"


class EvidenceReferenceError(ValueError):
    """Raised when an LLM output references evidence that was not provided."""


def _compact_evidence(bundle: EvidenceBundle) -> list[dict]:
    compact = []
    for index, item in enumerate(bundle.evidence[:30]):
        local_id = item.local_id or f"{item.source_type}_{index + 1:02d}"
        compact.append(
            {
                "id": local_id,
                "source_type": item.source_type,
                "source_name": item.source_name,
                "title": item.title,
                "text": item.text[:900],
                "reliability_tier": item.reliability_tier,
                "published_at": item.published_at,
            }
        )
    return compact


def _valid_evidence_refs(bundle: EvidenceBundle) -> set[str]:
    refs: set[str] = set()
    for index, item in enumerate(bundle.evidence[:30]):
        refs.add(item.local_id or f"{item.source_type}_{index + 1:02d}")
    return refs


def _validate_claim_refs(claims: list[ClaimAssessment], valid_refs: set[str]) -> None:
    invalid_refs: list[str] = []
    ungrounded_claims: list[str] = []

    for claim in claims:
        if claim.stance != "unsupported" and not claim.evidence_refs:
            ungrounded_claims.append(claim.claim)
        for ref in claim.evidence_refs:
            if ref not in valid_refs:
                invalid_refs.append(ref)

    if invalid_refs or ungrounded_claims:
        details = []
        if invalid_refs:
            details.append(f"invalid evidence refs: {sorted(set(invalid_refs))}")
        if ungrounded_claims:
            details.append(f"claims missing refs: {ungrounded_claims[:3]}")
        raise EvidenceReferenceError("; ".join(details))


def validate_adversarial_evaluation_refs(evaluation: AdversarialEvaluation, bundle: EvidenceBundle) -> None:
    if (
        evaluation.support
        or evaluation.opposition
        or evaluation.contradictions
    ) and not evaluation.claim_assessments:
        raise EvidenceReferenceError("grounded adversarial claims require claim_assessments with evidence refs")
    _validate_claim_refs(evaluation.claim_assessments, _valid_evidence_refs(bundle))


def validate_conviction_diff_refs(conviction: ConvictionDiff, bundle: EvidenceBundle) -> None:
    if (
        conviction.strengthened_claims
        or conviction.weakened_claims
        or conviction.broken_claims
    ) and not conviction.claim_assessments:
        raise EvidenceReferenceError("grounded conviction claims require claim_assessments with evidence refs")
    _validate_claim_refs(conviction.claim_assessments, _valid_evidence_refs(bundle))


async def _invoke_with_one_repair(structured, messages, validator):
    try:
        result = await asyncio.to_thread(structured.invoke, messages)
        validator(result)
        return result, 0
    except Exception as exc:
        repair_messages = [
            *messages,
            HumanMessage(
                content=(
                    "The previous structured output failed validation. "
                    f"Validation error: {exc}. "
                    "Return the same schema again. Use only evidence ids that appear in the provided evidence. "
                    "For unsupported claims, use stance unsupported and leave evidence_refs empty."
                )
            ),
        ]
        result = await asyncio.to_thread(structured.invoke, repair_messages)
        validator(result)
        return result, 1


async def run_adversarial_evaluation(
    thesis_text: str,
    evidence_bundle: EvidenceBundle,
    memory: MemorySnapshot,
    *,
    return_metadata: bool = False,
) -> AdversarialEvaluation | tuple[AdversarialEvaluation, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(AdversarialEvaluation)

    payload = {
        "thesis": thesis_text,
        "ticker": evidence_bundle.ticker,
        "evidence": _compact_evidence(evidence_bundle),
        "source_statuses": [status.model_dump() for status in evidence_bundle.source_statuses],
        "memory": memory.model_dump(),
    }

    messages = [
        SystemMessage(
            content=(
                "You are an adversarial investment research evaluator. "
                "Challenge the user's thesis using only provided evidence and memory. "
                "Do not invent facts. Mark missing evidence explicitly. "
                "When assessing a claim, populate claim_assessments. "
                "Every supports, weakens, or contradicts assessment must cite provided evidence ids. "
                "Unsupported assessments must use no evidence refs."
            )
        ),
        HumanMessage(content=json.dumps(payload, sort_keys=True)),
    ]

    result, retry_count = await _invoke_with_one_repair(
        structured,
        messages,
        lambda output: validate_adversarial_evaluation_refs(output, evidence_bundle),
    )
    if return_metadata:
        return result, {
            "prompt_version": ADVERSARIAL_EVALUATOR_PROMPT_VERSION,
            "retry_count": retry_count,
            "evidence_ref_count": len(_valid_evidence_refs(evidence_bundle)),
        }
    return result


async def run_conviction_synthesis(
    thesis_text: str,
    evidence_bundle: EvidenceBundle,
    memory: MemorySnapshot,
    evaluation: AdversarialEvaluation,
    *,
    return_metadata: bool = False,
) -> ConvictionDiff | tuple[ConvictionDiff, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(ConvictionDiff)

    referenced_ids = sorted(
        {
            ref
            for claim in evaluation.claim_assessments
            for ref in claim.evidence_refs
            if ref in _valid_evidence_refs(evidence_bundle)
        }
    )
    compact_evidence = _compact_evidence(evidence_bundle)
    evidence_for_synthesis = [
        item for item in compact_evidence if not referenced_ids or item["id"] in referenced_ids
    ]

    payload = {
        "thesis": thesis_text,
        "ticker": evidence_bundle.ticker,
        "evidence": evidence_for_synthesis,
        "source_statuses": [status.model_dump() for status in evidence_bundle.source_statuses],
        "memory": memory.model_dump(),
        "adversarial_evaluation": evaluation.model_dump(),
    }

    messages = [
        SystemMessage(
            content=(
                "You produce a conviction diff for a saved investment thesis. "
                "Return a practical verdict: hold, revise, monitor, invalidate, or insufficient_evidence. "
                "Every unsupported claim must be labeled unsupported. "
                "Do not introduce evidence not present in the adversarial evaluation or evidence list. "
                "Populate claim_assessments with evidence refs for supported, weakened, and contradicted claims. "
                "This is research support, not financial advice."
            )
        ),
        HumanMessage(content=json.dumps(payload, sort_keys=True)),
    ]

    result, retry_count = await _invoke_with_one_repair(
        structured,
        messages,
        lambda output: validate_conviction_diff_refs(output, evidence_bundle),
    )
    if return_metadata:
        return result, {
            "prompt_version": CONVICTION_SYNTHESIZER_PROMPT_VERSION,
            "retry_count": retry_count,
            "evidence_ref_count": len(_valid_evidence_refs(evidence_bundle)),
        }
    return result
