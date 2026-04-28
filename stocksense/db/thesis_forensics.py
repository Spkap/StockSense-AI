"""
Persistence helpers for thesis check runs.

Uses the admin client because server-side orchestration writes rows on behalf
of authenticated users after token verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from stocksense.core.evidence_hashing import hash_evidence_items
from stocksense.core.thesis_forensics_schemas import EvidenceBundle, ThesisCheckFinal
from stocksense.db.supabase_client import get_supabase_admin_client


def build_run_insert(
    user_id: str,
    thesis_id: str,
    ticker: str,
    *,
    thesis_hash: str | None = None,
    run_mode: str = "normal",
    idempotency_key: str | None = None,
) -> dict:
    return {
        "user_id": user_id,
        "thesis_id": thesis_id,
        "ticker": ticker.upper(),
        "status": "running",
        "run_mode": run_mode,
        "thesis_hash": thesis_hash,
        "idempotency_key": idempotency_key,
    }


def build_final_update(final: ThesisCheckFinal, *, status: str = "completed") -> dict:
    return {
        "status": status,
        "evidence_hash": final.evidence_hash,
        "thesis_hash": final.thesis_hash,
        "run_mode": final.run_mode,
        "cache_hit": final.cache_hit,
        "final_verdict": final.conviction.verdict,
        "final_confidence": final.conviction.confidence,
        "final_summary": final.conviction.summary,
        "final_result": final.model_dump(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


def create_thesis_check_run(
    user_id: str,
    thesis_id: str,
    ticker: str,
    *,
    thesis_hash: str | None = None,
    run_mode: str = "normal",
    idempotency_key: str | None = None,
) -> str:
    client = get_supabase_admin_client()
    response = client.table("thesis_check_runs").insert(
        build_run_insert(
            user_id,
            thesis_id,
            ticker,
            thesis_hash=thesis_hash,
            run_mode=run_mode,
            idempotency_key=idempotency_key,
        )
    ).execute()
    return response.data[0]["id"]


def log_thesis_check_step(
    run_id: str,
    step_name: str,
    status: str,
    data: dict | None = None,
    latency_ms: int = 0,
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
        client.table("thesis_check_steps").insert(
            {
                "run_id": run_id,
                "step_name": step_name,
                "status": status,
                "latency_ms": latency_ms,
                "data": data or {},
                "error_message": error_message,
                "retry_count": retry_count,
                "model": model,
                "prompt_version": prompt_version,
                "input_token_estimate": input_token_estimate,
                "output_token_estimate": output_token_estimate,
                "cost_estimate_usd": cost_estimate_usd,
                "validation_errors": validation_errors or [],
            }
        ).execute()
    except Exception:
        return


def save_evidence_bundle(run_id: str, thesis_id: str, ticker: str, bundle: EvidenceBundle) -> str:
    evidence_hash = hash_evidence_items(bundle.evidence)
    if not bundle.evidence:
        return evidence_hash

    rows = []
    for item in bundle.evidence:
        rows.append(
            {
                "run_id": run_id,
                "thesis_id": thesis_id,
                "ticker": ticker.upper(),
                "source_type": item.source_type,
                "local_id": item.local_id,
                "source_name": item.source_name,
                "title": item.title,
                "text": item.text,
                "url": item.url,
                "published_at": item.published_at,
                "reliability_tier": item.reliability_tier,
                "evidence_hash": evidence_hash,
                "metadata": item.metadata,
            }
        )

    client = get_supabase_admin_client()
    client.table("thesis_evidence_items").insert(rows).execute()
    return evidence_hash


def complete_thesis_check_run(final: ThesisCheckFinal, *, status: str = "completed") -> None:
    client = get_supabase_admin_client()
    client.table("thesis_check_runs").update(build_final_update(final, status=status)).eq("id", final.run_id).execute()


def fail_thesis_check_run(run_id: str, error_message: str) -> None:
    client = get_supabase_admin_client()
    client.table("thesis_check_runs").update(
        {
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", run_id).execute()


def cancel_thesis_check_run(run_id: str, user_id: str) -> None:
    client = get_supabase_admin_client()
    client.table("thesis_check_runs").update(
        {
            "status": "cancelled",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", run_id).eq("user_id", user_id).execute()


def is_thesis_check_run_cancelled(run_id: str) -> bool:
    try:
        client = get_supabase_admin_client()
        response = (
            client.table("thesis_check_runs")
            .select("status")
            .eq("id", run_id)
            .single()
            .execute()
        )
        return (response.data or {}).get("status") == "cancelled"
    except Exception:
        return False


def find_latest_completed_run(user_id: str, thesis_id: str) -> dict | None:
    client = get_supabase_admin_client()
    response = (
        client.table("thesis_check_runs")
        .select("*")
        .eq("user_id", user_id)
        .eq("thesis_id", thesis_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    for run in response.data or []:
        if run.get("status") in {"completed", "completed_cached"} and run.get("final_result"):
            return run
    return None


def get_thesis_check_run_bundle(user_id: str, run_id: str) -> dict[str, Any] | None:
    client = get_supabase_admin_client()
    run_response = (
        client.table("thesis_check_runs")
        .select("*")
        .eq("id", run_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not run_response.data:
        return None

    steps_response = (
        client.table("thesis_check_steps")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at", desc=False)
        .execute()
    )
    evidence_response = (
        client.table("thesis_evidence_items")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at", desc=False)
        .execute()
    )

    return {
        "run": run_response.data,
        "steps": steps_response.data or [],
        "evidence": evidence_response.data or [],
    }


def get_latest_thesis_check_run_bundle(user_id: str, thesis_id: str) -> dict[str, Any] | None:
    client = get_supabase_admin_client()
    run_response = (
        client.table("thesis_check_runs")
        .select("*")
        .eq("user_id", user_id)
        .eq("thesis_id", thesis_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not run_response.data:
        return None
    return get_thesis_check_run_bundle(user_id, run_response.data[0]["id"])


def save_thesis_correction(
    *,
    user_id: str,
    thesis_id: str,
    run_id: str | None,
    correction_type: str,
    correction_text: str | None = None,
    claim: str | None = None,
    evidence_local_id: str | None = None,
) -> dict:
    client = get_supabase_admin_client()
    payload = {
        "user_id": user_id,
        "thesis_id": thesis_id,
        "run_id": run_id,
        "evidence_local_id": evidence_local_id,
        "claim": claim,
        "correction_type": correction_type,
        "correction_text": correction_text,
    }
    response = client.table("thesis_corrections").insert(payload).execute()
    return response.data[0]
