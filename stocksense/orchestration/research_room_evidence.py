"""
Deterministic evidence collection for Research Room.

Collectors are data plumbing, not agent work. They run independently and emit
source statuses so the UI can show gaps before any memo is generated.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from stocksense.core.data_collectors import get_fundamental_data, get_news, get_price_history
from stocksense.core.evidence_indexing import build_evidence_local_id
from stocksense.core.research_schemas import ResearchEvidenceBundle, ResearchEvidenceItem, SourceStatus
from stocksense.core.sec_edgar import (
    extract_company_fact_metrics,
    fetch_company_facts,
    fetch_company_submissions,
    resolve_cik_for_ticker,
    select_recent_filings,
)


async def _run_source(source_type: str, fn, *args, timeout_seconds: float) -> tuple[SourceStatus, Any]:
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout_seconds)
        latency_ms = int((time.monotonic() - start) * 1000)
        is_empty = result is None or (isinstance(result, (list, dict)) and len(result) == 0)
        status = "empty" if is_empty else "ok"
        return SourceStatus(source_type=source_type, status=status, latency_ms=latency_ms), result
    except asyncio.TimeoutError:
        return SourceStatus(
            source_type=source_type,
            status="timeout",
            latency_ms=int((time.monotonic() - start) * 1000),
            error="source timed out",
        ), None
    except Exception as exc:
        return SourceStatus(
            source_type=source_type,
            status="failed",
            latency_ms=int((time.monotonic() - start) * 1000),
            error=str(exc),
        ), None


def _fetch_sec_submissions_for_ticker(ticker: str) -> dict[str, Any] | None:
    cik = resolve_cik_for_ticker(ticker)
    if not cik:
        return None
    submissions = fetch_company_submissions(cik)
    filings = select_recent_filings(submissions, limit=6)
    return {"cik": cik, "submissions": submissions, "filings": [filing.model_dump() for filing in filings]}


def _fetch_sec_facts_for_ticker(ticker: str) -> dict[str, Any] | None:
    cik = resolve_cik_for_ticker(ticker)
    if not cik:
        return None
    facts = fetch_company_facts(cik)
    metrics = extract_company_fact_metrics(facts)
    return {"cik": cik, "facts": facts, "metrics": metrics}


def _sec_filings_to_evidence(ticker: str, result: dict[str, Any] | None) -> list[ResearchEvidenceItem]:
    if not result:
        return []
    evidence: list[ResearchEvidenceItem] = []
    for index, filing in enumerate(result.get("filings") or [], start=1):
        filing_type = filing.get("filing_type")
        local_id = build_evidence_local_id("sec", index, filing_type=filing_type)
        text = (
            f"{ticker.upper()} filed {filing_type} on {filing.get('filing_date')}. "
            f"Report date: {filing.get('report_date') or 'not provided'}. "
            f"Accession number: {filing.get('accession_number')}."
        )
        evidence.append(
            ResearchEvidenceItem(
                local_id=local_id,
                source_type="sec_filing",
                source_name="SEC EDGAR",
                title=f"{ticker.upper()} {filing_type} filing",
                text=text,
                url=filing.get("filing_url"),
                accession_number=filing.get("accession_number"),
                filing_type=filing_type,
                published_at=filing.get("filing_date"),
                period=filing.get("report_date"),
                reliability_tier="high",
                metadata=filing,
            )
        )
    return evidence


def _sec_facts_to_evidence(ticker: str, result: dict[str, Any] | None) -> list[ResearchEvidenceItem]:
    if not result:
        return []
    evidence: list[ResearchEvidenceItem] = []
    for index, metric in enumerate(result.get("metrics") or [], start=1):
        metric_key = metric.get("metric_key", "metric")
        value = metric.get("value")
        unit = metric.get("unit")
        period = metric.get("period")
        evidence.append(
            ResearchEvidenceItem(
                local_id=build_evidence_local_id("fact", 1, filing_type=metric_key),
                source_type="sec_company_facts",
                source_name="SEC Company Facts",
                title=f"{ticker.upper()} {metric.get('label', metric_key)}",
                text=f"{metric.get('label', metric_key)} was {value} {unit or ''} for period ending {period}.",
                accession_number=metric.get("accession_number"),
                filing_type=metric.get("form"),
                metric_name=metric_key,
                metric_value=value,
                period=period,
                published_at=metric.get("filed_at"),
                reliability_tier="high",
                metadata=metric,
            )
        )
    return evidence


def _news_to_evidence(headlines: list[str]) -> list[ResearchEvidenceItem]:
    return [
        ResearchEvidenceItem(
            local_id=f"news_{index + 1:02d}",
            source_type="news",
            source_name="NewsAPI",
            title=headline,
            text=headline,
            reliability_tier="medium",
        )
        for index, headline in enumerate((headlines or [])[:20])
        if headline
    ]


def _price_to_evidence(price_history: Any) -> list[ResearchEvidenceItem]:
    if price_history is None:
        return []
    try:
        if price_history.empty:
            return []
        first_close = float(price_history["Close"].iloc[0])
        last_close = float(price_history["Close"].iloc[-1])
        pct_change = ((last_close - first_close) / first_close) * 100
        return [
            ResearchEvidenceItem(
                local_id="price_01",
                source_type="price",
                source_name="Yahoo Finance",
                title="Recent price movement",
                text=f"Close moved from {first_close:.2f} to {last_close:.2f}, a {pct_change:.2f}% change.",
                reliability_tier="medium",
                metadata={"first_close": first_close, "last_close": last_close, "pct_change": round(pct_change, 2)},
            )
        ]
    except Exception as exc:
        return [
            ResearchEvidenceItem(
                local_id="price_01",
                source_type="price",
                source_name="Yahoo Finance",
                title="Price data parsing warning",
                text=f"Price data returned but could not be summarized: {exc}",
                reliability_tier="low",
            )
        ]


def _fundamentals_to_evidence(fundamentals: dict | None) -> list[ResearchEvidenceItem]:
    info = (fundamentals or {}).get("info", {})
    facts: list[str] = []
    for key in [
        "market_cap",
        "pe_ratio",
        "forward_pe",
        "peg_ratio",
        "profit_margins",
        "revenue_growth",
        "debt_to_equity",
        "free_cashflow",
        "recommendation_mean",
    ]:
        value = info.get(key)
        if value is not None:
            facts.append(f"{key}: {value}")
    if not facts:
        return []
    return [
        ResearchEvidenceItem(
            local_id="fundamentals_01",
            source_type="fundamentals",
            source_name="Yahoo Finance",
            title="Current fundamentals snapshot",
            text="; ".join(facts),
            reliability_tier="medium",
            metadata={"info": info},
        )
    ]


async def collect_research_evidence(ticker: str, question: str) -> ResearchEvidenceBundle:
    ticker = ticker.upper().strip()

    results = await asyncio.gather(
        _run_source("sec_submissions", _fetch_sec_submissions_for_ticker, ticker, timeout_seconds=10.0),
        _run_source("sec_company_facts", _fetch_sec_facts_for_ticker, ticker, timeout_seconds=10.0),
        _run_source("price", get_price_history, ticker, "1mo", timeout_seconds=4.0),
        _run_source("fundamentals", get_fundamental_data, ticker, timeout_seconds=6.0),
        _run_source("news", get_news, ticker, 14, timeout_seconds=4.0),
    )

    statuses = [status for status, _ in results]
    sec_submissions = results[0][1]
    sec_facts = results[1][1]

    evidence: list[ResearchEvidenceItem] = []
    evidence.extend(_sec_filings_to_evidence(ticker, sec_submissions))
    evidence.extend(_sec_facts_to_evidence(ticker, sec_facts))
    evidence.extend(_price_to_evidence(results[2][1]))
    evidence.extend(_fundamentals_to_evidence(results[3][1]))
    evidence.extend(_news_to_evidence(results[4][1] or []))

    company_snapshot = {
        "ticker": ticker,
        "question": question,
        "cik": (sec_submissions or sec_facts or {}).get("cik"),
        "filing_count": len((sec_submissions or {}).get("filings") or []),
        "fact_metric_count": len((sec_facts or {}).get("metrics") or []),
        "sec_gap": any(status.source_type.startswith("sec") and status.status in {"failed", "timeout", "empty"} for status in statuses),
    }

    return ResearchEvidenceBundle(
        ticker=ticker,
        company_snapshot=company_snapshot,
        source_statuses=statuses,
        evidence=evidence,
    )
