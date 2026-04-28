"""
Authenticated Research Room routes.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from stocksense.api.auth_routes import get_current_user
from stocksense.core.validation import validate_ticker
from stocksense.db.run_controller import cancel_agent_run, get_agent_run_bundle
from stocksense.orchestration.research_room import run_research_room_stream

router = APIRouter(prefix="/api", tags=["Research Room"])


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.get("/research-room/{ticker}/stream")
async def stream_research_room(
    ticker: str,
    question: str = Query(..., min_length=4),
    user=Depends(get_current_user),
):
    ticker = ticker.upper().strip()
    is_valid, error_msg = validate_ticker(ticker, check_exists=False)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    async def generate():
        async for event in run_research_room_stream(
            user_id=user["id"],
            ticker=ticker,
            question=question,
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


@router.get("/research-room-runs/{run_id}")
async def get_research_room_run(run_id: str, user=Depends(get_current_user)):
    bundle = get_agent_run_bundle(user["id"], run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Research Room run not found")
    if bundle["run"].get("run_type") != "research_room":
        raise HTTPException(status_code=404, detail="Research Room run not found")
    return bundle


@router.post("/research-room-runs/{run_id}/cancel")
async def cancel_research_room_run(run_id: str, user=Depends(get_current_user)):
    cancel_agent_run(run_id, user["id"])
    return {"run_id": run_id, "status": "cancelled"}


@router.post("/research-room-runs/{run_id}/thesis-draft")
async def get_research_room_thesis_draft(run_id: str, user=Depends(get_current_user)):
    bundle = get_agent_run_bundle(user["id"], run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="Research Room run not found")
    if bundle["run"].get("run_type") != "research_room":
        raise HTTPException(status_code=404, detail="Research Room run not found")
    final_result = bundle["run"].get("final_result") or {}
    thesis_draft = final_result.get("thesis_draft")
    if not thesis_draft:
        raise HTTPException(status_code=404, detail="Thesis draft not available")
    return {"run_id": run_id, "thesis_draft": thesis_draft}
