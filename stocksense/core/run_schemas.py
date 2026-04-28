"""
Typed contracts for generic agent runs.

These schemas are intentionally separate from the existing thesis-check
contracts. New product surfaces can share run persistence, step logging, and
SSE events without forcing a migration of the current thesis-check hot path.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RunType = Literal[
    "research_room",
    "narrative_test",
    "thesis_check",
    "scenario_simulation",
    "research_bounty",
    "watchlist_monitor",
]
RunStatus = Literal["queued", "running", "completed", "completed_cached", "failed", "cancelled"]
RunEventType = Literal[
    "started",
    "plan_started",
    "plan_completed",
    "source_started",
    "source_completed",
    "index_completed",
    "retrieval_completed",
    "agent_started",
    "agent_completed",
    "referee_completed",
    "memo_completed",
    "completed",
    "cancelled",
    "error",
]


class RunStreamEvent(BaseModel):
    type: RunEventType
    run_id: str
    run_type: RunType
    ticker: str | None = None
    phase: str
    progress: float = Field(ge=0.0, le=1.0)
    message: str
    data: dict = Field(default_factory=dict)


class RunRecord(BaseModel):
    id: str | None = None
    user_id: str
    run_type: RunType
    status: RunStatus = "running"
    ticker: str | None = None
    thesis_id: str | None = None
    question: str | None = None
    phase: str | None = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    idempotency_key: str | None = None
    input_hash: str | None = None
    evidence_hash: str | None = None
    cache_hit: bool = False
    final_result: dict | None = None
    error_message: str | None = None


class RunStepRecord(BaseModel):
    id: str | None = None
    run_id: str
    step_name: str
    phase: str
    status: RunStatus | Literal["started", "completed", "skipped"] = "running"
    event_type: RunEventType | None = None
    latency_ms: int = Field(default=0, ge=0)
    data: dict = Field(default_factory=dict)
    error_message: str | None = None
    retry_count: int = Field(default=0, ge=0)
    model: str | None = None
    prompt_version: str | None = None
    input_token_estimate: int | None = Field(default=None, ge=0)
    output_token_estimate: int | None = Field(default=None, ge=0)
    cost_estimate_usd: float | None = Field(default=None, ge=0)
    validation_errors: list[str] = Field(default_factory=list)
