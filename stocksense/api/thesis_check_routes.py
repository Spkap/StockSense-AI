"""
Authenticated thesis-check routes.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from stocksense.api.auth_routes import get_current_user
from stocksense.db.thesis_forensics import (
    cancel_thesis_check_run,
    get_latest_thesis_check_run_bundle,
    get_thesis_check_run_bundle,
    save_thesis_correction,
)
from stocksense.db.supabase_client import get_supabase_client
from stocksense.orchestration.thesis_check import run_thesis_check_stream

router = APIRouter(prefix="/api", tags=["Thesis Checks"])


class ThesisCorrectionRequest(BaseModel):
    correction_type: str = Field(..., min_length=2)
    correction_text: str | None = None
    claim: str | None = None
    evidence_local_id: str | None = None


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _load_user_thesis(user_id: str, access_token: str, thesis_id: str) -> dict:
    client = get_supabase_client()
    client.postgrest.auth(access_token)
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


@router.get("/theses/{thesis_id}/check/stream")
async def stream_thesis_check(thesis_id: str, user=Depends(get_current_user)):
    thesis = _load_user_thesis(user["id"], user["access_token"], thesis_id)

    async def generate():
        async for event in run_thesis_check_stream(
            user_id=user["id"],
            access_token=user["access_token"],
            thesis_id=thesis_id,
            ticker=thesis["ticker"],
            thesis_text=thesis["thesis_summary"],
        ):
            yield _sse(event.model_dump())

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/theses/{thesis_id}/check/latest")
async def latest_thesis_check(thesis_id: str, user=Depends(get_current_user)):
    _load_user_thesis(user["id"], user["access_token"], thesis_id)
    bundle = get_latest_thesis_check_run_bundle(user["id"], thesis_id)
    if not bundle:
        return {"run": None, "steps": [], "evidence": []}
    return bundle


@router.get("/thesis-runs/{run_id}")
async def get_thesis_run(run_id: str, user=Depends(get_current_user)):
    bundle = get_thesis_check_run_bundle(user["id"], run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Thesis run not found")
    return bundle


@router.post("/thesis-runs/{run_id}/cancel")
async def cancel_thesis_run(run_id: str, user=Depends(get_current_user)):
    cancel_thesis_check_run(run_id, user["id"])
    return {"run_id": run_id, "status": "cancelled"}


@router.post("/thesis-runs/{run_id}/corrections")
async def add_thesis_run_correction(
    run_id: str,
    correction: ThesisCorrectionRequest,
    user=Depends(get_current_user),
):
    bundle = get_thesis_check_run_bundle(user["id"], run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Thesis run not found")

    saved = save_thesis_correction(
        user_id=user["id"],
        thesis_id=bundle["run"]["thesis_id"],
        run_id=run_id,
        correction_type=correction.correction_type,
        correction_text=correction.correction_text,
        claim=correction.claim,
        evidence_local_id=correction.evidence_local_id,
    )
    return {"correction": saved}
