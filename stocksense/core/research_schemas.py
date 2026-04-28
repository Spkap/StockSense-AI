"""
Research Room schemas.

Research Room outputs are stricter than ordinary chat answers: every grounded
claim must point at evidence ids that the UI can render as receipts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


ResearchSourceType = Literal[
    "sec_filing",
    "sec_company_facts",
    "price",
    "fundamentals",
    "news",
    "retrieval",
    "prior_run",
    "manual",
]
ResearchSourceStatusType = Literal["sec_submissions", "sec_company_facts", "price", "fundamentals", "news"]
SourceRunStatus = Literal["pending", "ok", "empty", "failed", "timeout", "skipped"]
ReliabilityTier = Literal["high", "medium", "low"]
NarrativeVerdict = Literal["supported", "weakened", "contradicted", "mixed", "unsupported", "insufficient_evidence"]
ClaimStance = Literal["supports", "weakens", "contradicts", "unsupported"]
ConfidenceBand = Literal["low", "medium", "high"]
SeverityBand = Literal["low", "medium", "high"]


class SourceStatus(BaseModel):
    source_type: ResearchSourceStatusType
    status: SourceRunStatus
    latency_ms: int = Field(default=0, ge=0)
    error: str | None = None


class ResearchEvidenceItem(BaseModel):
    local_id: str
    source_type: ResearchSourceType
    source_name: str
    title: str
    text: str
    url: str | None = None
    published_at: str | None = None
    accession_number: str | None = None
    filing_type: str | None = None
    metric_name: str | None = None
    metric_value: str | float | int | None = None
    period: str | None = None
    reliability_tier: ReliabilityTier = "medium"
    metadata: dict = Field(default_factory=dict)


class MetricEvidence(BaseModel):
    metric: str
    value: str | float | int
    period: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    interpretation: str = ""

    @model_validator(mode="after")
    def require_metric_receipt(self):
        if not self.evidence_refs:
            raise ValueError("metric evidence requires at least one evidence ref")
        return self


class ClaimAssessment(BaseModel):
    claim: str
    stance: ClaimStance
    confidence: ConfidenceBand = "medium"
    evidence_refs: list[str] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def require_refs_for_grounded_claims(self):
        if self.stance != "unsupported" and not self.evidence_refs:
            raise ValueError("supported, weakened, and contradicted claims require evidence refs")
        if self.stance == "unsupported" and self.evidence_refs:
            raise ValueError("unsupported claims must not cite evidence refs")
        return self


class NarrativeTruthTest(BaseModel):
    verdict: NarrativeVerdict
    confidence: ConfidenceBand = "medium"
    answer: str
    supported: list[ClaimAssessment] = Field(default_factory=list)
    weakened: list[ClaimAssessment] = Field(default_factory=list)
    contradicted: list[ClaimAssessment] = Field(default_factory=list)
    missing_proof: list[str] = Field(default_factory=list)
    next_watch_items: list[str] = Field(default_factory=list)


class ContradictionCard(BaseModel):
    title: str
    contradiction: str
    severity: SeverityBand = "medium"
    evidence_refs: list[str] = Field(default_factory=list)
    why_it_matters: str

    @model_validator(mode="after")
    def require_contradiction_receipt(self):
        if not self.evidence_refs:
            raise ValueError("contradiction cards require evidence refs")
        return self


class ResearchMemo(BaseModel):
    verdict: NarrativeVerdict
    executive_summary: str
    supported_points: list[str] = Field(default_factory=list)
    weakened_points: list[str] = Field(default_factory=list)
    missing_proof: list[str] = Field(default_factory=list)
    next_watch_items: list[str] = Field(default_factory=list)


class ResearchThesisDraft(BaseModel):
    ticker: str
    thesis_summary: str
    conviction_level: ConfidenceBand = "medium"
    kill_criteria: list[str] = Field(default_factory=list)
    time_horizon: Literal["short", "medium", "long"] = "medium"
    thesis_type: Literal["growth", "value", "income", "turnaround", "special_situation"] = "growth"
    evidence_refs: list[str] = Field(default_factory=list)


class ResearchEvidenceBundle(BaseModel):
    ticker: str
    company_snapshot: dict = Field(default_factory=dict)
    source_statuses: list[SourceStatus] = Field(default_factory=list)
    evidence: list[ResearchEvidenceItem] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    focus_areas: list[str] = Field(default_factory=list)
    source_queries: list[str] = Field(default_factory=list)
    missing_sources_to_watch: list[str] = Field(default_factory=list)


class ResearchAnalystBrief(BaseModel):
    company_snapshot: dict = Field(default_factory=dict)
    key_metrics: list[MetricEvidence] = Field(default_factory=list)
    bull_case: list[ClaimAssessment] = Field(default_factory=list)
    bear_case: list[ClaimAssessment] = Field(default_factory=list)


class ContradictionReview(BaseModel):
    contradiction_cards: list[ContradictionCard] = Field(default_factory=list)


class ResearchMemoPackage(BaseModel):
    narrative_test: NarrativeTruthTest
    memo: ResearchMemo
    thesis_draft: ResearchThesisDraft


class ResearchRoomFinal(BaseModel):
    run_id: str
    ticker: str
    question: str
    company_snapshot: dict = Field(default_factory=dict)
    narrative_test: NarrativeTruthTest
    key_metrics: list[MetricEvidence] = Field(default_factory=list)
    contradiction_cards: list[ContradictionCard] = Field(default_factory=list)
    bull_case: list[ClaimAssessment] = Field(default_factory=list)
    bear_case: list[ClaimAssessment] = Field(default_factory=list)
    evidence: list[ResearchEvidenceItem] = Field(default_factory=list)
    memo: ResearchMemo
    thesis_draft: ResearchThesisDraft
    source_statuses: list[SourceStatus] = Field(default_factory=list)


class SecFilingMetadata(BaseModel):
    cik: str
    ticker: str
    accession_number: str
    filing_type: str
    filing_date: str
    report_date: str | None = None
    primary_document: str | None = None
    filing_url: str | None = None
