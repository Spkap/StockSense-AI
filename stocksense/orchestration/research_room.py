"""
Research Room streaming orchestrator.
"""

from __future__ import annotations

import time
from typing import AsyncGenerator

from stocksense.core.evidence_indexing import hash_source_content, rank_evidence_chunks
from stocksense.core.research_schemas import (
    NarrativeTruthTest,
    ResearchEvidenceBundle,
    ResearchMemo,
    ResearchRoomFinal,
    ResearchThesisDraft,
)
from stocksense.core.run_schemas import RunStreamEvent
from stocksense.db.evidence_memory import (
    evidence_chunk_rows_to_prior_items,
    persist_research_evidence_bundle,
    search_evidence_chunks_fts,
)
from stocksense.db.run_controller import (
    complete_agent_run,
    create_agent_run,
    fail_agent_run,
    is_agent_run_cancelled,
    log_agent_run_step,
)
from stocksense.orchestration.research_room_agents import run_research_room_agents
from stocksense.orchestration.research_room_evidence import collect_research_evidence


def _event(
    event_type: str,
    run_id: str,
    ticker: str,
    phase: str,
    progress: float,
    message: str,
    data: dict | None = None,
) -> RunStreamEvent:
    return RunStreamEvent(
        type=event_type,
        run_id=run_id,
        run_type="research_room",
        ticker=ticker,
        phase=phase,
        progress=progress,
        message=message,
        data=data or {},
    )


def _insufficient_evidence_final(
    *,
    run_id: str,
    ticker: str,
    question: str,
    bundle: ResearchEvidenceBundle,
) -> ResearchRoomFinal:
    return ResearchRoomFinal(
        run_id=run_id,
        ticker=ticker,
        question=question,
        company_snapshot=bundle.company_snapshot,
        narrative_test=NarrativeTruthTest(
            verdict="insufficient_evidence",
            confidence="low",
            answer="No usable evidence was available to test the narrative.",
            missing_proof=["SEC filings, company facts, price, fundamentals, or news evidence"],
            next_watch_items=["Retry once sources recover or add manual evidence."],
        ),
        memo=ResearchMemo(
            verdict="insufficient_evidence",
            executive_summary="Research Room could not test the narrative because no evidence was collected.",
            missing_proof=["No usable source returned evidence."],
            next_watch_items=["Retry later", "Check source configuration"],
        ),
        thesis_draft=ResearchThesisDraft(
            ticker=ticker,
            thesis_summary=f"{ticker} thesis draft requires evidence before it should be saved.",
            conviction_level="low",
            kill_criteria=["Evidence sources remain unavailable for this ticker."],
            evidence_refs=[],
        ),
        evidence=[],
        source_statuses=bundle.source_statuses,
    )


def _evidence_hash(bundle: ResearchEvidenceBundle) -> str:
    return hash_source_content([item.model_dump(mode="json") for item in bundle.evidence])


def _bundle_with_prior_memory(
    bundle: ResearchEvidenceBundle,
    prior_rows: list[dict],
) -> tuple[ResearchEvidenceBundle, int]:
    existing_ids = {item.local_id for item in bundle.evidence}
    prior_items = evidence_chunk_rows_to_prior_items(
        bundle.ticker,
        prior_rows,
        existing_local_ids=existing_ids,
    )
    if not prior_items:
        return bundle, 0

    company_snapshot = {
        **bundle.company_snapshot,
        "prior_evidence_count": len(prior_items),
    }
    return (
        bundle.model_copy(
            update={
                "company_snapshot": company_snapshot,
                "evidence": [*bundle.evidence, *prior_items],
            },
            deep=True,
        ),
        len(prior_items),
    )


def _index_and_retrieve_memory(
    *,
    ticker: str,
    question: str,
    bundle: ResearchEvidenceBundle,
) -> tuple[ResearchEvidenceBundle, dict]:
    metadata = {
        "indexed_documents": 0,
        "indexed_chunks": 0,
        "prior_evidence_count": 0,
        "retrieval_available": False,
        "persistence_available": False,
        "errors": [],
    }
    enriched_bundle = bundle

    try:
        prior_rows = search_evidence_chunks_fts(ticker, question, limit=8)
        enriched_bundle, prior_count = _bundle_with_prior_memory(bundle, prior_rows)
        metadata.update(
            {
                "prior_evidence_count": prior_count,
                "retrieval_available": True,
            }
        )
    except Exception as exc:
        metadata["errors"].append(f"retrieval: {exc}")

    try:
        persist_summary = persist_research_evidence_bundle(bundle)
        metadata.update(
            {
                "indexed_documents": persist_summary.get("documents", 0),
                "indexed_chunks": persist_summary.get("chunks", 0),
                "persistence_available": True,
            }
        )
    except Exception as exc:
        metadata["errors"].append(f"persistence: {exc}")

    return enriched_bundle, metadata


async def run_research_room_stream(
    user_id: str,
    ticker: str,
    question: str,
) -> AsyncGenerator[RunStreamEvent, None]:
    ticker = ticker.upper().strip()
    input_hash = hash_source_content({"ticker": ticker, "question": question})
    run_id = create_agent_run(
        user_id=user_id,
        run_type="research_room",
        ticker=ticker,
        question=question,
        input_hash=input_hash,
    )

    yield _event("started", run_id, ticker, "start", 0.02, "Starting Research Room")

    try:
        plan_payload = {
            "ticker": ticker,
            "question": question,
            "source_plan": ["SEC submissions", "SEC company facts", "price", "fundamentals", "news"],
            "agent_plan": ["planner", "filing/fundamentals analyst", "contradiction agent", "memo compiler", "evidence referee"],
        }
        log_agent_run_step(
            run_id=run_id,
            step_name="research_plan",
            phase="plan",
            status="completed",
            event_type="plan_completed",
            data=plan_payload,
        )
        yield _event("plan_completed", run_id, ticker, "plan", 0.10, "Built research plan", plan_payload)

        source_start = time.monotonic()
        yield _event("source_started", run_id, ticker, "sources", 0.16, "Collecting SEC, market, and news evidence")
        bundle = await collect_research_evidence(ticker, question)
        evidence_hash = _evidence_hash(bundle)
        log_agent_run_step(
            run_id=run_id,
            step_name="evidence_collection",
            phase="sources",
            status="completed",
            event_type="source_completed",
            latency_ms=int((time.monotonic() - source_start) * 1000),
            data={
                "evidence_count": len(bundle.evidence),
                "evidence_hash": evidence_hash,
                "source_statuses": [status.model_dump() for status in bundle.source_statuses],
            },
        )
        yield _event(
            "source_completed",
            run_id,
            ticker,
            "sources",
            0.34,
            f"Collected {len(bundle.evidence)} evidence receipts",
            {
                "company_snapshot": bundle.company_snapshot,
                "source_statuses": [status.model_dump() for status in bundle.source_statuses],
                "evidence_count": len(bundle.evidence),
                "evidence_hash": evidence_hash,
            },
        )

        index_start = time.monotonic()
        bundle, memory_metadata = _index_and_retrieve_memory(ticker=ticker, question=question, bundle=bundle)
        log_agent_run_step(
            run_id=run_id,
            step_name="evidence_memory",
            phase="index",
            status="completed" if not memory_metadata.get("errors") else "skipped",
            event_type="index_completed",
            latency_ms=int((time.monotonic() - index_start) * 1000),
            data=memory_metadata,
            error_message="; ".join(memory_metadata.get("errors", [])) or None,
        )
        yield _event(
            "index_completed",
            run_id,
            ticker,
            "index",
            0.40,
            (
                "Indexed current evidence and loaded prior memory"
                if not memory_metadata.get("errors")
                else "Evidence memory unavailable; continuing with current receipts"
            ),
            memory_metadata,
        )

        ranked = rank_evidence_chunks(question, [item.model_dump() for item in bundle.evidence], max_items=12)
        log_agent_run_step(
            run_id=run_id,
            step_name="evidence_retrieval",
            phase="retrieval",
            status="completed",
            event_type="retrieval_completed",
            data={"retrieved_ids": [item["local_id"] for item in ranked], "query": question},
        )
        yield _event(
            "retrieval_completed",
            run_id,
            ticker,
            "retrieval",
            0.44,
            "Selected evidence for analyst context",
            {"retrieved_ids": [item["local_id"] for item in ranked]},
        )

        if is_agent_run_cancelled(run_id):
            yield _event("cancelled", run_id, ticker, "cancelled", 1.0, "Research Room cancelled")
            return

        if not bundle.evidence:
            final = _insufficient_evidence_final(run_id=run_id, ticker=ticker, question=question, bundle=bundle)
            complete_agent_run(run_id, final.model_dump(), evidence_hash=evidence_hash)
            log_agent_run_step(
                run_id=run_id,
                step_name="llm_gate",
                phase="agents",
                status="skipped",
                event_type="agent_completed",
                data={"reason": "no_usable_evidence"},
            )
            yield _event("agent_completed", run_id, ticker, "agents", 0.80, "Skipped analyst agents: no usable evidence")
            yield _event("referee_completed", run_id, ticker, "referee", 0.90, "Evidence referee skipped")
            yield _event("memo_completed", run_id, ticker, "memo", 0.96, "Insufficient evidence memo compiled", final.memo.model_dump())
            yield _event("completed", run_id, ticker, "completed", 1.0, "Research Room complete: insufficient evidence", final.model_dump())
            return

        agent_start = time.monotonic()
        final_result = await run_research_room_agents(
            run_id=run_id,
            ticker=ticker,
            question=question,
            bundle=bundle,
            return_metadata=True,
        )
        final, metadata = final_result if isinstance(final_result, tuple) else (final_result, {})
        log_agent_run_step(
            run_id=run_id,
            step_name="research_room_agents",
            phase="agents",
            status="completed",
            event_type="agent_completed",
            latency_ms=int((time.monotonic() - agent_start) * 1000),
            data={"metadata": metadata, "verdict": final.narrative_test.verdict},
            retry_count=sum(int(role_meta.get("retry_count", 0)) for role_meta in metadata.values() if isinstance(role_meta, dict)),
        )
        yield _event(
            "agent_completed",
            run_id,
            ticker,
            "agents",
            0.76,
            "Analyst agents completed",
            {"verdict": final.narrative_test.verdict, "metadata": metadata},
        )

        if is_agent_run_cancelled(run_id):
            yield _event("cancelled", run_id, ticker, "cancelled", 1.0, "Research Room cancelled")
            return

        log_agent_run_step(
            run_id=run_id,
            step_name="evidence_referee",
            phase="referee",
            status="completed",
            event_type="referee_completed",
            data={"evidence_count": len(final.evidence), "claim_count": len(final.bull_case) + len(final.bear_case)},
        )
        yield _event("referee_completed", run_id, ticker, "referee", 0.84, "Evidence refs validated")

        log_agent_run_step(
            run_id=run_id,
            step_name="memo_compiler",
            phase="memo",
            status="completed",
            event_type="memo_completed",
            data=final.memo.model_dump(),
        )
        yield _event("memo_completed", run_id, ticker, "memo", 0.94, "Research memo compiled", final.memo.model_dump())

        complete_agent_run(run_id, final.model_dump(), evidence_hash=evidence_hash)
        yield _event(
            "completed",
            run_id,
            ticker,
            "completed",
            1.0,
            f"Research Room complete: {final.narrative_test.verdict}",
            final.model_dump(),
        )
    except Exception as exc:
        try:
            fail_agent_run(run_id, str(exc))
        except Exception:
            pass
        yield _event("error", run_id, ticker, "error", 1.0, str(exc), {"error": str(exc)})
