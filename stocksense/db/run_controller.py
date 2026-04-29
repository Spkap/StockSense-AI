"""
Generic agent-run persistence.

This module mirrors the thesis_forensics persistence style while keeping new
Research Room and World Model runs on their own tables.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stocksense.core.run_schemas import RunEventType, RunStatus, RunType
from stocksense.db.supabase_client import get_supabase_admin_client


TERMINAL_STATUSES: set[str] = {"completed", "completed_cached", "failed", "cancelled"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def build_agent_run_insert(
    *,
    user_id: str,
    run_type: RunType,
    ticker: str | None = None,
    thesis_id: str | None = None,
    question: str | None = None,
    phase: str | None = "start",
    progress: float = 0.0,
    idempotency_key: str | None = None,
    input_hash: str | None = None,
) -> dict[str, Any]:
    return _strip_none(
        {
            "user_id": user_id,
            "run_type": run_type,
            "status": "running",
            "ticker": ticker.upper().strip() if ticker else None,
            "thesis_id": thesis_id,
            "question": question,
            "phase": phase,
            "progress": progress,
            "idempotency_key": idempotency_key,
            "input_hash": input_hash,
        }
    )


def build_agent_run_update(
    *,
    status: RunStatus | None = None,
    phase: str | None = None,
    progress: float | None = None,
    evidence_hash: str | None = None,
    cache_hit: bool | None = None,
    final_result: dict | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    payload = _strip_none(
        {
            "status": status,
            "phase": phase,
            "progress": progress,
            "evidence_hash": evidence_hash,
            "cache_hit": cache_hit,
            "final_result": final_result,
            "error_message": error_message,
            "updated_at": _now_iso(),
        }
    )
    if status in TERMINAL_STATUSES:
        payload["completed_at"] = _now_iso()
    return payload


def build_agent_step_insert(
    *,
    run_id: str,
    step_name: str,
    phase: str,
    status: str,
    event_type: RunEventType | None = None,
    latency_ms: int = 0,
    data: dict | None = None,
    error_message: str | None = None,
    retry_count: int = 0,
    model: str | None = None,
    prompt_version: str | None = None,
    input_token_estimate: int | None = None,
    output_token_estimate: int | None = None,
    cost_estimate_usd: float | None = None,
    validation_errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "step_name": step_name,
        "phase": phase,
        "status": status,
        "event_type": event_type,
        "latency_ms": max(0, latency_ms),
        "data": data or {},
        "error_message": error_message,
        "retry_count": max(0, retry_count),
        "model": model,
        "prompt_version": prompt_version,
        "input_token_estimate": input_token_estimate,
        "output_token_estimate": output_token_estimate,
        "cost_estimate_usd": cost_estimate_usd,
        "validation_errors": validation_errors or [],
    }


def create_agent_run(
    *,
    user_id: str,
    run_type: RunType,
    ticker: str | None = None,
    thesis_id: str | None = None,
    question: str | None = None,
    phase: str | None = "start",
    progress: float = 0.0,
    idempotency_key: str | None = None,
    input_hash: str | None = None,
) -> str:
    client = get_supabase_admin_client()
    response = client.table("agent_runs").insert(
        build_agent_run_insert(
            user_id=user_id,
            run_type=run_type,
            ticker=ticker,
            thesis_id=thesis_id,
            question=question,
            phase=phase,
            progress=progress,
            idempotency_key=idempotency_key,
            input_hash=input_hash,
        )
    ).execute()
    return response.data[0]["id"]


def log_agent_run_step(
    *,
    run_id: str,
    step_name: str,
    phase: str,
    status: str,
    event_type: RunEventType | None = None,
    latency_ms: int = 0,
    data: dict | None = None,
    error_message: str | None = None,
    retry_count: int = 0,
    model: str | None = None,
    prompt_version: str | None = None,
    input_token_estimate: int | None = None,
    output_token_estimate: int | None = None,
    cost_estimate_usd: float | None = None,
    validation_errors: list[str] | None = None,
) -> None:
    try:
        client = get_supabase_admin_client()
        client.table("agent_run_steps").insert(
            build_agent_step_insert(
                run_id=run_id,
                step_name=step_name,
                phase=phase,
                status=status,
                event_type=event_type,
                latency_ms=latency_ms,
                data=data,
                error_message=error_message,
                retry_count=retry_count,
                model=model,
                prompt_version=prompt_version,
                input_token_estimate=input_token_estimate,
                output_token_estimate=output_token_estimate,
                cost_estimate_usd=cost_estimate_usd,
                validation_errors=validation_errors,
            )
        ).execute()
    except Exception:
        return


def complete_agent_run(
    run_id: str,
    final_result: dict,
    *,
    status: RunStatus = "completed",
    evidence_hash: str | None = None,
    cache_hit: bool = False,
) -> None:
    client = get_supabase_admin_client()
    client.table("agent_runs").update(
        build_agent_run_update(
            status=status,
            phase="completed",
            progress=1.0,
            evidence_hash=evidence_hash,
            cache_hit=cache_hit,
            final_result=final_result,
        )
    ).eq("id", run_id).execute()


def fail_agent_run(run_id: str, error_message: str) -> None:
    client = get_supabase_admin_client()
    client.table("agent_runs").update(
        build_agent_run_update(
            status="failed",
            phase="error",
            progress=1.0,
            error_message=error_message,
        )
    ).eq("id", run_id).execute()


def cancel_agent_run(run_id: str, user_id: str) -> bool:
    client = get_supabase_admin_client()
    response = client.table("agent_runs").update(
        build_agent_run_update(status="cancelled", phase="cancelled", progress=1.0)
    ).eq("id", run_id).eq("user_id", user_id).execute()
    return bool(response.data)


def is_agent_run_cancelled(run_id: str) -> bool:
    try:
        client = get_supabase_admin_client()
        response = client.table("agent_runs").select("status").eq("id", run_id).single().execute()
        return (response.data or {}).get("status") == "cancelled"
    except Exception:
        return False


def get_agent_run_bundle(user_id: str, run_id: str) -> dict[str, Any] | None:
    client = get_supabase_admin_client()
    run_response = (
        client.table("agent_runs")
        .select("*")
        .eq("id", run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_response.data:
        return None

    steps_response = (
        client.table("agent_run_steps")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at", desc=False)
        .execute()
    )

    return {
        "run": run_response.data,
        "steps": steps_response.data or [],
    }
