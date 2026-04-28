"""
Fast deterministic evidence collection for thesis checks.

This module treats market data fetches as data collection, not agent work.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from stocksense.core.data_collectors import get_fundamental_data, get_news, get_price_history
from stocksense.core.thesis_forensics_schemas import EvidenceBundle, EvidenceItem, SourceStatus


async def _run_source(source_type: str, fn, *args, timeout_seconds: float) -> tuple[SourceStatus, Any]:
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=timeout_seconds)
        latency_ms = int((time.monotonic() - start) * 1000)
        is_empty = result is None or (isinstance(result, (list, dict)) and len(result) == 0)
        status = "empty" if is_empty else "ok"
        return SourceStatus(source_type=source_type, status=status, latency_ms=latency_ms), result
    except asyncio.TimeoutError:
        latency_ms = int((time.monotonic() - start) * 1000)
        return SourceStatus(
            source_type=source_type,
            status="timeout",
            latency_ms=latency_ms,
            error="source timed out",
        ), None
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return SourceStatus(
            source_type=source_type,
            status="failed",
            latency_ms=latency_ms,
            error=str(exc),
        ), None


def _news_to_evidence(headlines: list[str]) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            local_id=f"news_{index + 1:02d}",
            source_type="news",
            source_name="NewsAPI",
            title=headline,
            text=headline,
            reliability_tier="medium",
        )
        for index, headline in enumerate(headlines[:20])
    ]


def _fundamentals_to_evidence(fundamentals: dict) -> list[EvidenceItem]:
    info = fundamentals.get("info", {}) if fundamentals else {}
    if not info:
        return []

    facts = []
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
        EvidenceItem(
            local_id="fundamentals_01",
            source_type="fundamentals",
            source_name="Yahoo Finance",
            title="Current fundamentals snapshot",
            text="; ".join(facts),
            reliability_tier="medium",
            metadata={"info": info},
        )
    ]


def _price_to_evidence(price_history: Any) -> list[EvidenceItem]:
    if price_history is None:
        return []
    try:
        if price_history.empty:
            return []
        first_close = float(price_history["Close"].iloc[0])
        last_close = float(price_history["Close"].iloc[-1])
        pct_change = ((last_close - first_close) / first_close) * 100
        return [
            EvidenceItem(
                local_id="price_01",
                source_type="price",
                source_name="Yahoo Finance",
                title="Recent price movement",
                text=(
                    f"Close moved from {first_close:.2f} to {last_close:.2f}, "
                    f"a {pct_change:.2f}% change over the fetched period."
                ),
                reliability_tier="medium",
                metadata={
                    "first_close": first_close,
                    "last_close": last_close,
                    "pct_change": round(pct_change, 2),
                },
            )
        ]
    except Exception as exc:
        return [
            EvidenceItem(
                local_id="price_01",
                source_type="price",
                source_name="Yahoo Finance",
                title="Price data parsing warning",
                text=f"Price data was returned but could not be summarized: {exc}",
                reliability_tier="low",
            )
        ]


async def collect_evidence_for_ticker(ticker: str) -> EvidenceBundle:
    ticker = ticker.upper().strip()

    news_task = _run_source("news", get_news, ticker, 7, timeout_seconds=4.0)
    price_task = _run_source("price", get_price_history, ticker, "1mo", timeout_seconds=4.0)
    fundamentals_task = _run_source("fundamentals", get_fundamental_data, ticker, timeout_seconds=6.0)

    news_result, price_result, fundamentals_result = await asyncio.gather(
        news_task,
        price_task,
        fundamentals_task,
    )

    source_statuses = [news_result[0], price_result[0], fundamentals_result[0]]
    evidence: list[EvidenceItem] = []
    evidence.extend(_news_to_evidence(news_result[1] or []))
    evidence.extend(_price_to_evidence(price_result[1]))
    evidence.extend(_fundamentals_to_evidence(fundamentals_result[1] or {}))

    return EvidenceBundle(ticker=ticker, source_statuses=source_statuses, evidence=evidence)
