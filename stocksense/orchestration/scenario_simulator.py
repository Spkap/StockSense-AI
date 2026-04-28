from __future__ import annotations

from typing import Any

from stocksense.core.world_model_schemas import ScenarioBoardResult, ScenarioPath, ThesisClaim
from stocksense.db.supabase_client import get_supabase_admin_client


def build_scenario_board(thesis: dict[str, Any], claims: list[ThesisClaim]) -> ScenarioBoardResult:
    ticker = (thesis.get("ticker") or "").upper()
    impacted = [claim.claim_text for claim in claims[:3]]
    evidence_required = sorted({gap for claim in claims for gap in claim.evidence_needed})[:6]

    return ScenarioBoardResult(
        thesis_id=thesis["id"],
        ticker=ticker,
        scenarios=[
            ScenarioPath(
                scenario="bull",
                summary=f"{ticker} thesis strengthens because observable claims show improving evidence.",
                driver_changes=["Revenue and margin observables improve", "Contradictions narrow"],
                impacted_claims=impacted,
                evidence_required=evidence_required,
                confidence="medium",
            ),
            ScenarioPath(
                scenario="base",
                summary=f"{ticker} thesis remains monitorable while proof accumulates.",
                driver_changes=["Evidence is mixed", "Kill criteria remain untriggered"],
                impacted_claims=impacted,
                evidence_required=evidence_required,
                confidence="medium",
            ),
            ScenarioPath(
                scenario="bear",
                summary=f"{ticker} thesis weakens if core observables miss and kill criteria activate.",
                driver_changes=["Growth evidence stalls", "Margin or execution proof fails"],
                impacted_claims=impacted,
                evidence_required=evidence_required,
                confidence="medium",
            ),
        ],
    )


def persist_scenario_board(user_id: str, thesis_id: str, result: ScenarioBoardResult, run_id: str | None = None) -> None:
    client = get_supabase_admin_client()
    client.table("scenario_runs").insert(
        {
            "thesis_id": thesis_id,
            "user_id": user_id,
            "run_id": run_id,
            "final_result": result.model_dump(),
        }
    ).execute()
