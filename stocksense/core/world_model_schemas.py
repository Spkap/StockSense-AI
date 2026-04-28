from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ClaimType = Literal["growth", "margin", "competitive", "valuation", "execution", "risk", "capital_allocation"]
ClaimStatus = Literal["active", "watching", "validated", "invalidated"]
ConfidenceBand = Literal["low", "medium", "high"]
ScenarioName = Literal["bull", "base", "bear"]


class ClaimObservable(BaseModel):
    observable_name: str
    source_type: str
    metric_key: str | None = None
    threshold_operator: Literal[">", ">=", "<", "<=", "=", "!="] | None = None
    threshold_value: float | None = None
    period: str | None = None


class ThesisClaim(BaseModel):
    id: str | None = None
    claim_text: str
    claim_type: ClaimType
    metric_hint: str | None = None
    time_horizon: str | None = None
    status: ClaimStatus = "active"
    confidence: ConfidenceBand = "medium"
    evidence_needed: list[str] = Field(default_factory=list)
    observables: list[ClaimObservable] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_observable_or_gap(self):
        if not self.observables and not self.evidence_needed:
            raise ValueError("claim requires at least one observable or evidence gap")
        return self


class ForecastQuestion(BaseModel):
    id: str | None = None
    claim_id: str | None = None
    question: str
    resolution_criteria: str
    due_date: str | None = None
    probability: float | None = Field(default=None, ge=0, le=1)
    status: Literal["open", "resolved"] = "open"
    resolved_outcome: bool | None = None
    brier_score: float | None = Field(default=None, ge=0, le=1)


class FalsifiabilityCompileResult(BaseModel):
    thesis_id: str
    ticker: str
    claims: list[ThesisClaim] = Field(default_factory=list, min_length=1, max_length=7)
    forecast_questions: list[ForecastQuestion] = Field(default_factory=list)
    kill_criteria: list[str] = Field(default_factory=list)


class ScenarioPath(BaseModel):
    scenario: ScenarioName
    summary: str
    driver_changes: list[str] = Field(default_factory=list)
    impacted_claims: list[str] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    confidence: ConfidenceBand = "medium"


class ScenarioBoardResult(BaseModel):
    thesis_id: str
    ticker: str
    scenarios: list[ScenarioPath]
