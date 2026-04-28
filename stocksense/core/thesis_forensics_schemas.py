"""
Typed contracts for the fast thesis-check workflow.

These models intentionally keep v1 small:
- deterministic evidence collection
- deterministic memory retrieval
- one adversarial LLM evaluation
- one conviction synthesis
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field


SourceType = Literal[
    "news",
    "price",
    "fundamentals",
    "cached_analysis",
    "prior_run",
    "alert_history",
]
SourceRunStatus = Literal["pending", "ok", "empty", "failed", "timeout", "skipped"]
ReliabilityTier = Literal["high", "medium", "low"]
ConvictionVerdict = Literal["hold", "revise", "monitor", "invalidate", "insufficient_evidence"]
ConfidenceBand = Literal["low", "medium", "high"]
ClaimStance = Literal["supports", "weakens", "contradicts", "unsupported"]


class SourceStatus(BaseModel):
    source_type: SourceType
    status: SourceRunStatus
    latency_ms: int = Field(default=0, ge=0)
    error: str | None = None


class EvidenceItem(BaseModel):
    local_id: str | None = None
    source_type: SourceType
    source_name: str
    title: str
    text: str
    url: str | None = None
    published_at: str | None = None
    reliability_tier: ReliabilityTier = "medium"
    metadata: dict = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    ticker: str
    source_statuses: list[SourceStatus] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)

    @computed_field
    @property
    def has_partial_failure(self) -> bool:
        return any(status.status in {"failed", "timeout"} for status in self.source_statuses)

    @computed_field
    @property
    def available_source_types(self) -> list[str]:
        seen: list[str] = []
        for item in self.evidence:
            if item.source_type not in seen:
                seen.append(item.source_type)
        return seen


class MemorySnapshot(BaseModel):
    prior_run_found: bool = False
    prior_alerts_count: int = 0
    thesis_history_count: int = 0
    latest_cached_analysis_found: bool = False
    latest_prior_run_id: str | None = None
    latest_prior_verdict: str | None = None
    latest_prior_evidence_hash: str | None = None
    latest_prior_thesis_hash: str | None = None
    user_corrections: list[str] = Field(default_factory=list)
    notable_prior_changes: list[str] = Field(default_factory=list)


class ClaimAssessment(BaseModel):
    claim: str
    stance: ClaimStance
    confidence: ConfidenceBand
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: str


class AdversarialEvaluation(BaseModel):
    support: list[str] = Field(default_factory=list)
    opposition: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    human_review_items: list[str] = Field(default_factory=list)
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)


class ConvictionDiff(BaseModel):
    verdict: ConvictionVerdict
    confidence: ConfidenceBand
    strengthened_claims: list[str] = Field(default_factory=list)
    weakened_claims: list[str] = Field(default_factory=list)
    broken_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    summary: str
    next_actions: list[str] = Field(default_factory=list)
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)


class ThesisCheckFinal(BaseModel):
    run_id: str
    thesis_id: str
    ticker: str
    evidence_hash: str
    memory: MemorySnapshot
    evaluation: AdversarialEvaluation
    conviction: ConvictionDiff
    source_statuses: list[SourceStatus] = Field(default_factory=list)
    cache_hit: bool = False
    run_mode: str = "normal"
    thesis_hash: str | None = None


class ThesisCheckStreamEvent(BaseModel):
    type: Literal[
        "started",
        "source_started",
        "source_completed",
        "memory_completed",
        "preflight_completed",
        "evaluation_started",
        "evaluation_completed",
        "synthesis_started",
        "completed",
        "cancelled",
        "error",
    ]
    run_id: str
    thesis_id: str
    ticker: str
    phase: str
    progress: float = Field(ge=0.0, le=1.0)
    message: str
    data: dict = Field(default_factory=dict)
