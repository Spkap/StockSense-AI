"""
Deterministic memory retrieval for thesis checks.

This is intentionally not an LLM agent in v1. It fetches known user/project state.
"""

from __future__ import annotations

import logging

from stocksense.core.thesis_forensics_schemas import MemorySnapshot
from stocksense.db.database import get_latest_analysis
from stocksense.db.supabase_client import get_supabase_client

logger = logging.getLogger("stocksense.thesis_memory")


def build_memory_snapshot(user_id: str, access_token: str, thesis_id: str) -> MemorySnapshot:
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)

        thesis_response = (
            client.table("theses")
            .select("*")
            .eq("id", thesis_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        thesis = thesis_response.data or {}
        ticker = thesis.get("ticker", "")

        history_response = (
            client.table("thesis_history")
            .select("*")
            .eq("thesis_id", thesis_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        history = history_response.data or []

        alerts_response = (
            client.table("alert_history")
            .select("*")
            .eq("thesis_id", thesis_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        alerts = alerts_response.data or []

        runs_response = (
            client.table("thesis_check_runs")
            .select("*")
            .eq("thesis_id", thesis_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        prior_runs = runs_response.data or []

        try:
            corrections_response = (
                client.table("thesis_corrections")
                .select("*")
                .eq("thesis_id", thesis_id)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )
            corrections = corrections_response.data or []
        except Exception:
            corrections = []

        latest_cached_analysis = get_latest_analysis(ticker) if ticker else None

        user_corrections = []
        for correction in corrections:
            correction_type = correction.get("correction_type")
            correction_text = correction.get("correction_text")
            claim = correction.get("claim")
            if correction_type and correction_text:
                user_corrections.append(f"{correction_type}: {correction_text}")
            elif correction_type and claim:
                user_corrections.append(f"{correction_type}: {claim}")

        for item in history[:5]:
            reason = item.get("change_reason")
            if reason:
                user_corrections.append(reason)

        notable_prior_changes = []
        for alert in alerts[:5]:
            message = alert.get("message")
            if message:
                notable_prior_changes.append(message)

        latest_prior_verdict = None
        latest_prior_run_id = None
        latest_prior_evidence_hash = None
        latest_prior_thesis_hash = None
        if prior_runs:
            latest_completed = next(
                (
                    run
                    for run in prior_runs
                    if run.get("status") in {"completed", "completed_cached"}
                ),
                prior_runs[0],
            )
            latest_prior_run_id = latest_completed.get("id")
            latest_prior_verdict = latest_completed.get("final_verdict")
            latest_prior_evidence_hash = latest_completed.get("evidence_hash")
            latest_prior_thesis_hash = latest_completed.get("thesis_hash")

        return MemorySnapshot(
            prior_run_found=bool(prior_runs),
            prior_alerts_count=len(alerts),
            thesis_history_count=len(history),
            latest_cached_analysis_found=bool(latest_cached_analysis),
            latest_prior_run_id=latest_prior_run_id,
            latest_prior_verdict=latest_prior_verdict,
            latest_prior_evidence_hash=latest_prior_evidence_hash,
            latest_prior_thesis_hash=latest_prior_thesis_hash,
            user_corrections=user_corrections,
            notable_prior_changes=notable_prior_changes,
        )
    except Exception as exc:
        logger.warning("memory snapshot failed for thesis %s: %s", thesis_id, exc)
        return MemorySnapshot()
