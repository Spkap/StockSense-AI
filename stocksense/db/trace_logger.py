"""
TraceLogger — append-only audit trail for each agent step in an analysis run.

Usage:
    tracer = TraceLogger(run_id=correlation_id, ticker="AAPL")
    t0 = time.monotonic()
    response = llm.invoke(prompt)
    tracer.log_step(
        step_name="bull_analyst",
        prompt_snapshot=str(prompt),
        response_snapshot=response.content,
        token_count=tracked_llm.usage.total_tokens,
        duration_ms=int((time.monotonic() - t0) * 1000),
    )

Errors are swallowed — observability must never crash the hot path.
"""
from __future__ import annotations

import logging

try:
    from stocksense.db.supabase_client import get_supabase_client
except Exception:
    get_supabase_client = None  # type: ignore[assignment]

logger = logging.getLogger("stocksense.trace")


class TraceLogger:
    def __init__(self, run_id: str, ticker: str = "") -> None:
        self.run_id = run_id
        self.ticker = ticker

    def log_step(
        self,
        step_name: str,
        prompt_snapshot: str,
        response_snapshot: str,
        token_count: int,
        duration_ms: int,
    ) -> None:
        try:
            client = get_supabase_client()
            client.table("analysis_traces").insert({
                "ticker": self.ticker,
                "run_id": self.run_id,
                "step_name": step_name,
                "prompt_snapshot": prompt_snapshot[:4000],   # cap at 4K chars
                "response_snapshot": response_snapshot[:4000],
                "token_count": token_count,
                "duration_ms": duration_ms,
            }).execute()
        except Exception as exc:
            logger.warning("trace log failed (non-fatal): %s", exc)
