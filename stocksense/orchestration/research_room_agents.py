"""
Research Room analyst roles.

The roles are scoped and evidence-bound. They do not make buy/sell calls,
price targets, or claims without receipts.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from stocksense.core.config import get_chat_llm
from stocksense.core.research_schemas import (
    ContradictionReview,
    ResearchAnalystBrief,
    ResearchEvidenceBundle,
    ResearchEvidenceItem,
    ResearchMemoPackage,
    ResearchPlan,
    ResearchRoomFinal,
)


RESEARCH_PLANNER_PROMPT_VERSION = "2026-04-28.v1"
RESEARCH_ANALYST_PROMPT_VERSION = "2026-04-28.v1"
CONTRADICTION_AGENT_PROMPT_VERSION = "2026-04-28.v1"
MEMO_COMPILER_PROMPT_VERSION = "2026-04-28.v1"


class EvidenceReferenceError(ValueError):
    """Raised when a research output cites evidence that was not provided."""


def _compact_evidence(evidence: list[ResearchEvidenceItem]) -> list[dict[str, Any]]:
    return [
        {
            "id": item.local_id,
            "source_type": item.source_type,
            "source_name": item.source_name,
            "title": item.title,
            "text": item.text[:1000],
            "url": item.url,
            "reliability_tier": item.reliability_tier,
            "period": item.period,
            "accession_number": item.accession_number,
        }
        for item in evidence[:40]
    ]


def _valid_evidence_refs(bundle: ResearchEvidenceBundle) -> set[str]:
    return {item.local_id for item in bundle.evidence}


def _collect_evidence_refs(value: Any) -> list[str]:
    if isinstance(value, BaseModel):
        return _collect_evidence_refs(value.model_dump())
    if isinstance(value, dict):
        refs: list[str] = []
        for key, child in value.items():
            if key == "evidence_refs" and isinstance(child, list):
                refs.extend(str(ref) for ref in child)
            else:
                refs.extend(_collect_evidence_refs(child))
        return refs
    if isinstance(value, list):
        refs: list[str] = []
        for item in value:
            refs.extend(_collect_evidence_refs(item))
        return refs
    return []


def validate_research_refs(output: Any, bundle: ResearchEvidenceBundle) -> None:
    valid_refs = _valid_evidence_refs(bundle)
    invalid = sorted({ref for ref in _collect_evidence_refs(output) if ref not in valid_refs})
    if invalid:
        raise EvidenceReferenceError(f"invalid evidence refs: {invalid}")


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
                    f"Validation error: {exc}. Return the same schema again. "
                    "Use only evidence ids in the provided evidence list. "
                    "Unsupported claims must have empty evidence_refs."
                )
            ),
        ]
        result = await asyncio.to_thread(structured.invoke, repair_messages)
        validator(result)
        return result, 1


def _base_payload(question: str, bundle: ResearchEvidenceBundle) -> dict[str, Any]:
    return {
        "ticker": bundle.ticker,
        "question": question,
        "company_snapshot": bundle.company_snapshot,
        "source_statuses": [status.model_dump() for status in bundle.source_statuses],
        "evidence": _compact_evidence(bundle.evidence),
    }


async def run_research_planner(
    question: str,
    bundle: ResearchEvidenceBundle,
    *,
    return_metadata: bool = False,
) -> ResearchPlan | tuple[ResearchPlan, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(ResearchPlan)
    messages = [
        SystemMessage(
            content=(
                "You are a stock research planner. Break the user's narrative into "
                "testable research focus areas and identify source gaps. Do not make "
                "investment recommendations."
            )
        ),
        HumanMessage(content=json.dumps(_base_payload(question, bundle), sort_keys=True)),
    ]
    result, retry_count = await _invoke_with_one_repair(structured, messages, lambda output: None)
    if return_metadata:
        return result, {"prompt_version": RESEARCH_PLANNER_PROMPT_VERSION, "retry_count": retry_count}
    return result


async def run_research_analyst(
    question: str,
    bundle: ResearchEvidenceBundle,
    plan: ResearchPlan,
    *,
    return_metadata: bool = False,
) -> ResearchAnalystBrief | tuple[ResearchAnalystBrief, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(ResearchAnalystBrief)
    payload = {**_base_payload(question, bundle), "plan": plan.model_dump()}
    messages = [
        SystemMessage(
            content=(
                "You are a filing and fundamentals analyst. Extract metrics, bull "
                "evidence, and bear evidence using only provided evidence. Every "
                "grounded claim must cite evidence_refs. No buy/sell recommendations "
                "and no price targets."
            )
        ),
        HumanMessage(content=json.dumps(payload, sort_keys=True)),
    ]
    result, retry_count = await _invoke_with_one_repair(
        structured,
        messages,
        lambda output: validate_research_refs(output, bundle),
    )
    if return_metadata:
        return result, {"prompt_version": RESEARCH_ANALYST_PROMPT_VERSION, "retry_count": retry_count}
    return result


async def run_contradiction_agent(
    question: str,
    bundle: ResearchEvidenceBundle,
    plan: ResearchPlan,
    analyst: ResearchAnalystBrief,
    *,
    return_metadata: bool = False,
) -> ContradictionReview | tuple[ContradictionReview, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(ContradictionReview)
    payload = {
        **_base_payload(question, bundle),
        "plan": plan.model_dump(),
        "analyst_brief": analyst.model_dump(),
    }
    messages = [
        SystemMessage(
            content=(
                "You are a contradiction agent. Find evidence-backed tensions between "
                "the market narrative and the receipts. Cite evidence for each "
                "contradiction. If evidence is missing, leave it as missing proof, not "
                "a contradiction."
            )
        ),
        HumanMessage(content=json.dumps(payload, sort_keys=True)),
    ]
    result, retry_count = await _invoke_with_one_repair(
        structured,
        messages,
        lambda output: validate_research_refs(output, bundle),
    )
    if return_metadata:
        return result, {"prompt_version": CONTRADICTION_AGENT_PROMPT_VERSION, "retry_count": retry_count}
    return result


async def run_memo_compiler(
    question: str,
    bundle: ResearchEvidenceBundle,
    plan: ResearchPlan,
    analyst: ResearchAnalystBrief,
    contradictions: ContradictionReview,
    *,
    return_metadata: bool = False,
) -> ResearchMemoPackage | tuple[ResearchMemoPackage, dict]:
    llm = get_chat_llm(temperature=0.1)
    structured = llm.with_structured_output(ResearchMemoPackage)
    payload = {
        **_base_payload(question, bundle),
        "plan": plan.model_dump(),
        "analyst_brief": analyst.model_dump(),
        "contradiction_review": contradictions.model_dump(),
    }
    messages = [
        SystemMessage(
            content=(
                "You compile a research memo and thesis draft. Be explicit about "
                "supported, weakened, contradicted, and missing proof. This is research "
                "support, not financial advice. Do not issue buy/sell recommendations."
            )
        ),
        HumanMessage(content=json.dumps(payload, sort_keys=True)),
    ]
    result, retry_count = await _invoke_with_one_repair(
        structured,
        messages,
        lambda output: validate_research_refs(output, bundle),
    )
    if return_metadata:
        return result, {"prompt_version": MEMO_COMPILER_PROMPT_VERSION, "retry_count": retry_count}
    return result


def run_evidence_referee(final: ResearchRoomFinal) -> ResearchRoomFinal:
    valid_refs = {item.local_id for item in final.evidence}
    invalid = sorted({ref for ref in _collect_evidence_refs(final) if ref not in valid_refs})
    if invalid:
        raise EvidenceReferenceError(f"final output has invalid evidence refs: {invalid}")
    return final


async def run_research_room_agents(
    *,
    run_id: str,
    ticker: str,
    question: str,
    bundle: ResearchEvidenceBundle,
    return_metadata: bool = False,
) -> ResearchRoomFinal | tuple[ResearchRoomFinal, dict[str, dict]]:
    plan_result = await run_research_planner(question, bundle, return_metadata=True)
    plan, plan_meta = plan_result if isinstance(plan_result, tuple) else (plan_result, {})

    analyst_result = await run_research_analyst(question, bundle, plan, return_metadata=True)
    analyst, analyst_meta = analyst_result if isinstance(analyst_result, tuple) else (analyst_result, {})

    contradiction_result = await run_contradiction_agent(question, bundle, plan, analyst, return_metadata=True)
    contradictions, contradiction_meta = (
        contradiction_result if isinstance(contradiction_result, tuple) else (contradiction_result, {})
    )

    memo_result = await run_memo_compiler(question, bundle, plan, analyst, contradictions, return_metadata=True)
    memo_package, memo_meta = memo_result if isinstance(memo_result, tuple) else (memo_result, {})

    company_snapshot = {
        **bundle.company_snapshot,
        **analyst.company_snapshot,
    }
    final = ResearchRoomFinal(
        run_id=run_id,
        ticker=ticker.upper().strip(),
        question=question,
        company_snapshot=company_snapshot,
        narrative_test=memo_package.narrative_test,
        key_metrics=analyst.key_metrics,
        contradiction_cards=contradictions.contradiction_cards,
        bull_case=analyst.bull_case,
        bear_case=analyst.bear_case,
        evidence=bundle.evidence,
        memo=memo_package.memo,
        thesis_draft=memo_package.thesis_draft,
        source_statuses=bundle.source_statuses,
    )
    final = run_evidence_referee(final)

    metadata = {
        "planner": plan_meta,
        "analyst": analyst_meta,
        "contradiction_agent": contradiction_meta,
        "memo_compiler": memo_meta,
        "evidence_referee": {"valid_ref_count": len(_valid_evidence_refs(bundle))},
    }
    if return_metadata:
        return final, metadata
    return final
