from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from stocksense.api.auth_routes import get_current_user
from stocksense.core.calibration import brier_score
from stocksense.core.world_model_schemas import FalsifiabilityCompileResult, ForecastQuestion, ThesisClaim
from stocksense.db.supabase_client import get_supabase_admin_client
from stocksense.orchestration.falsifiability_compiler import compile_thesis_to_world_model, persist_world_model
from stocksense.orchestration.scenario_simulator import build_scenario_board, persist_scenario_board

router = APIRouter(prefix="/api", tags=["World Model"])


class ForecastResolveRequest(BaseModel):
    outcome: bool
    probability: float | None = Field(default=None, ge=0, le=1)


def _load_user_thesis(user_id: str, thesis_id: str) -> dict:
    client = get_supabase_admin_client()
    response = (
        client.table("theses")
        .select("*")
        .eq("id", thesis_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Thesis not found")
    return response.data


def _load_claims(thesis_id: str, user_id: str) -> list[ThesisClaim]:
    client = get_supabase_admin_client()
    claims_response = (
        client.table("thesis_claims")
        .select("*")
        .eq("thesis_id", thesis_id)
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    claims: list[ThesisClaim] = []
    for row in claims_response.data or []:
        observables_response = (
            client.table("claim_observables")
            .select("*")
            .eq("claim_id", row["id"])
            .execute()
        )
        claims.append(
            ThesisClaim(
                id=row["id"],
                claim_text=row["claim_text"],
                claim_type=row["claim_type"],
                metric_hint=row.get("metric_hint"),
                time_horizon=row.get("time_horizon"),
                status=row.get("status", "active"),
                confidence=row.get("confidence", "medium"),
                evidence_needed=row.get("evidence_needed") or [],
                observables=observables_response.data or [],
            )
        )
    return claims


def _load_forecast_questions(thesis_id: str, user_id: str) -> list[ForecastQuestion]:
    client = get_supabase_admin_client()
    response = (
        client.table("forecast_questions")
        .select("*")
        .eq("thesis_id", thesis_id)
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )
    return [
        ForecastQuestion(
            id=row.get("id"),
            claim_id=row.get("claim_id"),
            question=row["question"],
            resolution_criteria=row["resolution_criteria"],
            due_date=row.get("due_date"),
            probability=row.get("probability"),
            status=row.get("status", "open"),
            resolved_outcome=row.get("resolved_outcome"),
            brier_score=row.get("brier_score"),
        )
        for row in response.data or []
    ]


def _existing_world_model(thesis: dict, user_id: str) -> FalsifiabilityCompileResult | None:
    claims = _load_claims(thesis["id"], user_id)
    if not claims:
        return None
    return FalsifiabilityCompileResult(
        thesis_id=thesis["id"],
        ticker=(thesis.get("ticker") or "").upper(),
        claims=claims,
        forecast_questions=_load_forecast_questions(thesis["id"], user_id),
        kill_criteria=thesis.get("kill_criteria") or [],
    )


@router.post("/theses/{thesis_id}/compile")
async def compile_thesis_world_model(thesis_id: str, user=Depends(get_current_user)):
    thesis = _load_user_thesis(user["id"], thesis_id)
    existing = _existing_world_model(thesis, user["id"])
    if existing:
        return existing.model_dump()
    result = compile_thesis_to_world_model(thesis)
    persisted = persist_world_model(user["id"], thesis_id, result)
    return persisted.model_dump()


@router.post("/theses/{thesis_id}/scenarios")
async def run_thesis_scenarios(thesis_id: str, user=Depends(get_current_user)):
    thesis = _load_user_thesis(user["id"], thesis_id)
    claims = _load_claims(thesis_id, user["id"])
    if not claims:
        claims = compile_thesis_to_world_model(thesis).claims
    result = build_scenario_board(thesis, claims)
    persist_scenario_board(user["id"], thesis_id, result)
    return result.model_dump()


@router.post("/forecast-questions/{forecast_id}/resolve")
async def resolve_forecast_question(forecast_id: str, payload: ForecastResolveRequest, user=Depends(get_current_user)):
    client = get_supabase_admin_client()
    response = (
        client.table("forecast_questions")
        .select("*")
        .eq("id", forecast_id)
        .eq("user_id", user["id"])
        .single()
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Forecast question not found")
    probability = payload.probability if payload.probability is not None else response.data.get("probability")
    if probability is None:
        raise HTTPException(status_code=400, detail="Forecast probability required for calibration")
    score = brier_score(float(probability), payload.outcome)
    update_payload = {
        "status": "resolved",
        "resolved_outcome": payload.outcome,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "probability": probability,
        "brier_score": score,
    }
    client.table("forecast_questions").update(update_payload).eq("id", forecast_id).eq("user_id", user["id"]).execute()
    return {"forecast_id": forecast_id, "status": "resolved", "brier_score": score}
