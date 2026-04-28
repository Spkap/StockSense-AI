from __future__ import annotations

import re
from typing import Any

from stocksense.core.world_model_schemas import (
    ClaimObservable,
    FalsifiabilityCompileResult,
    ForecastQuestion,
    ThesisClaim,
)
from stocksense.db.supabase_client import get_supabase_admin_client


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _claim_type(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["revenue", "growth", "demand"]):
        return "growth"
    if any(term in lowered for term in ["margin", "profit", "cash flow", "free cash"]):
        return "margin"
    if any(term in lowered for term in ["competition", "share", "moat"]):
        return "competitive"
    if any(term in lowered for term in ["valuation", "multiple", "price"]):
        return "valuation"
    if any(term in lowered for term in ["risk", "kill", "fails", "decline"]):
        return "risk"
    return "execution"


def _metric_hint(text: str) -> str | None:
    lowered = text.lower()
    for metric in ["revenue", "gross margin", "operating income", "free cash flow", "debt", "market share"]:
        if metric in lowered:
            return metric
    return None


def _observable_for_claim(claim_text: str, claim_type: str, horizon: str | None) -> ClaimObservable:
    metric = _metric_hint(claim_text)
    if not metric and claim_type == "growth":
        metric = "revenue"
    if not metric and claim_type == "margin":
        metric = "operating margin"
    return ClaimObservable(
        observable_name=f"Track {metric or claim_type} evidence",
        source_type="sec_company_facts",
        metric_key=(metric or claim_type).replace(" ", "_"),
        threshold_operator=None,
        threshold_value=None,
        period=horizon,
    )


def compile_thesis_to_world_model(thesis: dict[str, Any]) -> FalsifiabilityCompileResult:
    summary = thesis.get("thesis_summary") or ""
    ticker = (thesis.get("ticker") or "").upper()
    thesis_id = thesis["id"]
    horizon = thesis.get("time_horizon")

    sentences = [part.strip() for part in SENTENCE_SPLIT_RE.split(summary) if len(part.strip()) > 20]
    claim_texts = sentences[:4] or [summary.strip()]
    for criterion in thesis.get("kill_criteria") or []:
        if len(claim_texts) >= 7:
            break
        claim_texts.append(f"Kill criterion to monitor: {criterion}")

    claims: list[ThesisClaim] = []
    for claim_text in claim_texts[:7]:
        claim_type = _claim_type(claim_text)
        metric_hint = _metric_hint(claim_text)
        claims.append(
            ThesisClaim(
                claim_text=claim_text,
                claim_type=claim_type,
                metric_hint=metric_hint,
                time_horizon=horizon,
                confidence=thesis.get("conviction_level", "medium"),
                evidence_needed=[f"Direct evidence for: {claim_text[:90]}"],
                observables=[_observable_for_claim(claim_text, claim_type, horizon)],
            )
        )

    forecast_questions = [
        ForecastQuestion(
            question=f"Will evidence validate this claim for {ticker}: {claim.claim_text[:100]}?",
            resolution_criteria="Resolve using SEC filings, company facts, or explicitly cited source evidence.",
            probability={"low": 0.35, "medium": 0.55, "high": 0.7}.get(claim.confidence, 0.55),
        )
        for claim in claims
    ]

    return FalsifiabilityCompileResult(
        thesis_id=thesis_id,
        ticker=ticker,
        claims=claims,
        forecast_questions=forecast_questions,
        kill_criteria=thesis.get("kill_criteria") or [],
    )


def persist_world_model(user_id: str, thesis_id: str, result: FalsifiabilityCompileResult) -> FalsifiabilityCompileResult:
    client = get_supabase_admin_client()
    persisted_claims: list[ThesisClaim] = []
    persisted_forecasts: list[ForecastQuestion] = []
    claim_id_by_index: dict[int, str] = {}

    for index, claim in enumerate(result.claims):
        claim_payload = {
            "thesis_id": thesis_id,
            "user_id": user_id,
            "claim_text": claim.claim_text,
            "claim_type": claim.claim_type,
            "metric_hint": claim.metric_hint,
            "time_horizon": claim.time_horizon,
            "status": claim.status,
            "confidence": claim.confidence,
            "evidence_needed": claim.evidence_needed,
        }
        claim_response = client.table("thesis_claims").insert(claim_payload).execute()
        claim_id = claim_response.data[0]["id"]
        claim_id_by_index[index] = claim_id
        persisted = claim.model_copy(update={"id": claim_id}, deep=True)
        persisted_claims.append(persisted)
        if claim.observables:
            client.table("claim_observables").insert(
                [
                    {
                        "claim_id": claim_id,
                        "observable_name": observable.observable_name,
                        "source_type": observable.source_type,
                        "metric_key": observable.metric_key,
                        "threshold_operator": observable.threshold_operator,
                        "threshold_value": observable.threshold_value,
                        "period": observable.period,
                    }
                    for observable in claim.observables
                ]
            ).execute()

    for index, forecast in enumerate(result.forecast_questions):
        claim_id = claim_id_by_index.get(index)
        forecast_response = client.table("forecast_questions").insert(
            {
                "thesis_id": thesis_id,
                "claim_id": claim_id,
                "user_id": user_id,
                "question": forecast.question,
                "resolution_criteria": forecast.resolution_criteria,
                "due_date": forecast.due_date,
                "probability": forecast.probability,
                "status": forecast.status,
            }
        ).execute()
        persisted_row = (forecast_response.data or [{}])[0]
        persisted_forecasts.append(
            forecast.model_copy(
                update={
                    "id": persisted_row.get("id"),
                    "claim_id": claim_id,
                },
                deep=True,
            )
        )

    return result.model_copy(update={"claims": persisted_claims, "forecast_questions": persisted_forecasts}, deep=True)
