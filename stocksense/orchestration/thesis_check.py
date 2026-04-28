"""
Streaming thesis-check orchestrator.

Designed for daily use:
- quick start event
- parallel deterministic evidence collection
- deterministic memory snapshot
- two LLM calls
- persisted final result
"""

from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator

from stocksense.core.evidence_hashing import hash_text
from stocksense.core.thesis_forensics_schemas import ThesisCheckFinal, ThesisCheckStreamEvent
from stocksense.db.thesis_forensics import (
    complete_thesis_check_run,
    create_thesis_check_run,
    find_latest_completed_run,
    fail_thesis_check_run,
    is_thesis_check_run_cancelled,
    log_thesis_check_step,
    save_evidence_bundle,
)
from stocksense.orchestration.thesis_agents import run_adversarial_evaluation, run_conviction_synthesis
from stocksense.orchestration.thesis_evidence import collect_evidence_for_ticker
from stocksense.orchestration.thesis_memory import build_memory_snapshot


def _event(
    event_type: str,
    run_id: str,
    thesis_id: str,
    ticker: str,
    phase: str,
    progress: float,
    message: str,
    data: dict | None = None,
) -> ThesisCheckStreamEvent:
    return ThesisCheckStreamEvent(
        type=event_type,
        run_id=run_id,
        thesis_id=thesis_id,
        ticker=ticker,
        phase=phase,
        progress=progress,
        message=message,
        data=data or {},
    )


def _source_quality_summary(source_statuses: list) -> dict:
    failed = [status for status in source_statuses if status.status in {"failed", "timeout"}]
    empty = [status for status in source_statuses if status.status == "empty"]
    ok = [status for status in source_statuses if status.status == "ok"]
    return {
        "ok_sources": [status.source_type for status in ok],
        "failed_sources": [status.source_type for status in failed],
        "empty_sources": [status.source_type for status in empty],
        "partial_failure": bool(failed),
    }


def _insufficient_evidence_final(
    *,
    run_id: str,
    thesis_id: str,
    ticker: str,
    thesis_text: str,
    thesis_hash: str,
    evidence_hash: str,
    memory,
    source_statuses,
) -> ThesisCheckFinal:
    from stocksense.core.thesis_forensics_schemas import AdversarialEvaluation, ConvictionDiff

    return ThesisCheckFinal(
        run_id=run_id,
        thesis_id=thesis_id,
        ticker=ticker,
        evidence_hash=evidence_hash,
        thesis_hash=thesis_hash,
        memory=memory,
        source_statuses=source_statuses,
        evaluation=AdversarialEvaluation(
            missing_evidence=["No usable evidence was available from configured sources."],
            human_review_items=["Retry after sources recover or add manual evidence."],
        ),
        conviction=ConvictionDiff(
            verdict="insufficient_evidence",
            confidence="low",
            unsupported_claims=[thesis_text],
            summary="The thesis could not be checked because no usable evidence was available.",
            next_actions=["Retry later", "Check source configuration", "Add manual evidence before rerunning"],
        ),
    )


def _cached_final_from_prior(
    *,
    previous_run: dict,
    run_id: str,
    thesis_id: str,
    ticker: str,
    thesis_hash: str,
    evidence_hash: str,
    memory,
    source_statuses,
) -> ThesisCheckFinal | None:
    try:
        prior = ThesisCheckFinal.model_validate(previous_run["final_result"])
    except Exception:
        return None

    return prior.model_copy(
        update={
            "run_id": run_id,
            "thesis_id": thesis_id,
            "ticker": ticker,
            "evidence_hash": evidence_hash,
            "thesis_hash": thesis_hash,
            "memory": memory,
            "source_statuses": source_statuses,
            "cache_hit": True,
            "run_mode": "normal",
        },
        deep=True,
    )


async def run_thesis_check_stream(
    user_id: str,
    access_token: str,
    thesis_id: str,
    ticker: str,
    thesis_text: str,
) -> AsyncGenerator[ThesisCheckStreamEvent, None]:
    ticker = ticker.upper().strip()
    thesis_hash = hash_text(thesis_text)
    idempotency_key = f"{user_id}:{thesis_id}:{thesis_hash}:normal"
    run_id = create_thesis_check_run(
        user_id=user_id,
        thesis_id=thesis_id,
        ticker=ticker,
        thesis_hash=thesis_hash,
        idempotency_key=idempotency_key,
    )

    yield _event("started", run_id, thesis_id, ticker, "start", 0.02, "Starting thesis check")

    try:
        yield _event("source_started", run_id, thesis_id, ticker, "evidence", 0.08, "Collecting evidence in parallel")
        evidence_start = time.monotonic()
        memory_start = time.monotonic()
        evidence_task = asyncio.create_task(collect_evidence_for_ticker(ticker))
        memory_task = asyncio.create_task(asyncio.to_thread(build_memory_snapshot, user_id, access_token, thesis_id))

        evidence_bundle = None
        memory = None
        done, _ = await asyncio.wait({evidence_task, memory_task}, return_when=asyncio.FIRST_COMPLETED)
        if memory_task in done:
            memory = memory_task.result()
            memory_latency = int((time.monotonic() - memory_start) * 1000)
            log_thesis_check_step(run_id, "memory_snapshot", "completed", data=memory.model_dump(), latency_ms=memory_latency)
            yield _event("memory_completed", run_id, thesis_id, ticker, "memory", 0.18, "Loaded thesis memory", memory.model_dump())
        if evidence_task in done:
            evidence_bundle = evidence_task.result()

        if evidence_bundle is None:
            evidence_bundle = await evidence_task
        evidence_latency = int((time.monotonic() - evidence_start) * 1000)
        evidence_hash = save_evidence_bundle(run_id, thesis_id, ticker, evidence_bundle)
        log_thesis_check_step(
            run_id,
            "evidence_collection",
            "completed",
            data={
                "source_statuses": [status.model_dump() for status in evidence_bundle.source_statuses],
                "evidence_count": len(evidence_bundle.evidence),
                "evidence_hash": evidence_hash,
                "thesis_hash": thesis_hash,
            },
            latency_ms=evidence_latency,
        )
        yield _event(
            "source_completed",
            run_id,
            thesis_id,
            ticker,
            "evidence",
            0.35,
            f"Collected {len(evidence_bundle.evidence)} evidence items",
            {
                "source_statuses": [status.model_dump() for status in evidence_bundle.source_statuses],
                "evidence_count": len(evidence_bundle.evidence),
                "evidence_hash": evidence_hash,
            },
        )

        if memory is None:
            memory = await memory_task
            memory_latency = int((time.monotonic() - memory_start) * 1000)
            log_thesis_check_step(run_id, "memory_snapshot", "completed", data=memory.model_dump(), latency_ms=memory_latency)
            yield _event("memory_completed", run_id, thesis_id, ticker, "memory", 0.45, "Loaded thesis memory", memory.model_dump())

        preflight = {
            **_source_quality_summary(evidence_bundle.source_statuses),
            "evidence_count": len(evidence_bundle.evidence),
            "evidence_hash": evidence_hash,
            "thesis_hash": thesis_hash,
            "cache_hit": False,
        }
        log_thesis_check_step(run_id, "source_quality_gate", "completed", data=preflight)
        yield _event("preflight_completed", run_id, thesis_id, ticker, "preflight", 0.50, "Checked source quality", preflight)

        if is_thesis_check_run_cancelled(run_id):
            yield _event("cancelled", run_id, thesis_id, ticker, "cancelled", 1.0, "Thesis check cancelled")
            return

        if not evidence_bundle.evidence:
            final = _insufficient_evidence_final(
                run_id=run_id,
                thesis_id=thesis_id,
                ticker=ticker,
                thesis_text=thesis_text,
                thesis_hash=thesis_hash,
                evidence_hash=evidence_hash,
                memory=memory,
                source_statuses=evidence_bundle.source_statuses,
            )
            complete_thesis_check_run(final)
            log_thesis_check_step(run_id, "llm_gate", "skipped", data={"reason": "no_usable_evidence"})
            yield _event(
                "completed",
                run_id,
                thesis_id,
                ticker,
                "completed",
                1.0,
                "Thesis check complete: insufficient_evidence",
                final.model_dump(),
            )
            return

        try:
            previous_run = find_latest_completed_run(user_id, thesis_id)
        except Exception:
            previous_run = None
        if (
            previous_run
            and previous_run.get("evidence_hash") == evidence_hash
            and previous_run.get("thesis_hash") == thesis_hash
        ):
            cached_final = _cached_final_from_prior(
                previous_run=previous_run,
                run_id=run_id,
                thesis_id=thesis_id,
                ticker=ticker,
                thesis_hash=thesis_hash,
                evidence_hash=evidence_hash,
                memory=memory,
                source_statuses=evidence_bundle.source_statuses,
            )
            if cached_final:
                complete_thesis_check_run(cached_final, status="completed_cached")
                log_thesis_check_step(
                    run_id,
                    "llm_gate",
                    "skipped",
                    data={"reason": "no_material_change", "prior_run_id": previous_run.get("id")},
                )
                yield _event(
                    "completed",
                    run_id,
                    thesis_id,
                    ticker,
                    "completed",
                    1.0,
                    "No material change since the latest completed thesis check",
                    cached_final.model_dump(),
                )
                return

        yield _event("evaluation_started", run_id, thesis_id, ticker, "challenge", 0.52, "Challenging thesis against evidence")
        evaluation_start = time.monotonic()
        evaluation_result = await run_adversarial_evaluation(thesis_text, evidence_bundle, memory, return_metadata=True)
        if isinstance(evaluation_result, tuple):
            evaluation, evaluation_meta = evaluation_result
        else:
            evaluation, evaluation_meta = evaluation_result, {}
        evaluation_latency = int((time.monotonic() - evaluation_start) * 1000)
        log_thesis_check_step(
            run_id,
            "adversarial_evaluation",
            "completed",
            data=evaluation.model_dump(),
            latency_ms=evaluation_latency,
            retry_count=evaluation_meta.get("retry_count", 0),
            prompt_version=evaluation_meta.get("prompt_version"),
        )
        yield _event("evaluation_completed", run_id, thesis_id, ticker, "challenge", 0.72, "Challenge complete", evaluation.model_dump())

        if is_thesis_check_run_cancelled(run_id):
            yield _event("cancelled", run_id, thesis_id, ticker, "cancelled", 1.0, "Thesis check cancelled")
            return

        yield _event("synthesis_started", run_id, thesis_id, ticker, "conviction", 0.80, "Building conviction diff")
        synthesis_start = time.monotonic()
        conviction_result = await run_conviction_synthesis(
            thesis_text,
            evidence_bundle,
            memory,
            evaluation,
            return_metadata=True,
        )
        if isinstance(conviction_result, tuple):
            conviction, conviction_meta = conviction_result
        else:
            conviction, conviction_meta = conviction_result, {}
        synthesis_latency = int((time.monotonic() - synthesis_start) * 1000)

        final = ThesisCheckFinal(
            run_id=run_id,
            thesis_id=thesis_id,
            ticker=ticker,
            evidence_hash=evidence_hash,
            thesis_hash=thesis_hash,
            memory=memory,
            evaluation=evaluation,
            conviction=conviction,
            source_statuses=evidence_bundle.source_statuses,
        )
        complete_thesis_check_run(final)
        log_thesis_check_step(
            run_id,
            "conviction_synthesis",
            "completed",
            data=conviction.model_dump(),
            latency_ms=synthesis_latency,
            retry_count=conviction_meta.get("retry_count", 0),
            prompt_version=conviction_meta.get("prompt_version"),
        )

        yield _event(
            "completed",
            run_id,
            thesis_id,
            ticker,
            "completed",
            1.0,
            f"Thesis check complete: {conviction.verdict}",
            final.model_dump(),
        )
    except Exception as exc:
        try:
            fail_thesis_check_run(run_id, str(exc))
        except Exception:
            pass
        yield _event("error", run_id, thesis_id, ticker, "error", 1.0, str(exc), {"error": str(exc)})
