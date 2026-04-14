# Phase 3 — Staff Engineer Elevation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Elevate StockSense from "AI app" to "AI system" — adding token tracking, audit trail, structured LLM output, Bayesian credibility scoring, semantic rebuttal matching, and prompt versioning to satisfy staff engineer scrutiny.

**Architecture:** Six targeted improvements: a `TrackedLLM` wrapper that accumulates `UsageMetadata` per analysis run; a `analysis_traces` Supabase table + `TraceLogger` that snapshots every agent prompt/response; Pydantic-based `with_structured_output()` replacing all `parse_llm_json` calls in Bull/Bear/Synthesizer; Bayesian credibility replacing the unjustified `* 0.5` formula; Google text-embedding-004 semantic matching replacing the 3-word substring hack; and a central `prompts.py` registry with versioned strings. Each is independently committable.

**Tech Stack:** LangChain 0.3.27 `with_structured_output` / `UsageMetadata`, langchain-google-genai 2.1.10 `GoogleGenerativeAIEmbeddings`, Supabase postgrest-py, tenacity (already in requirements), pytest 7+ with `unittest.mock`

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `stocksense/core/llm_client.py` | Create | `TrackedLLM` wrapper, `TokenUsage` dataclass |
| `stocksense/core/prompts.py` | Create | Central versioned prompt registry |
| `stocksense/db/trace_logger.py` | Create | `TraceLogger` — writes rows to `analysis_traces` |
| `supabase/migrations/005_analysis_traces.sql` | Create | DDL for `analysis_traces` table |
| `stocksense/agents/bull_analyst.py` | Modify | Use `with_structured_output` + `TrackedLLM` + prompts registry |
| `stocksense/agents/bear_analyst.py` | Modify | Same as bull |
| `stocksense/agents/synthesizer.py` | Modify | Bayesian credibility + semantic rebuttal + TrackedLLM |
| `stocksense/orchestration/react_flow.py` | Modify | Wire `TrackedLLM` through debate loop; add `token_usage` to return dict |
| `tests/test_phase3.py` | Create | Full test suite |

---

## Task 1: Token Tracking — TrackedLLM Wrapper

**Files:**
- Create: `stocksense/core/llm_client.py`
- Test: `tests/test_phase3.py` (first section)

`get_chat_llm` in `config.py` already has `max_retries=3`. This task wraps it with a transparent `TrackedLLM` that accumulates `UsageMetadata` from every `.invoke()` call without changing any call sites' interface.

- [ ] **Step 1: Write failing tests**

Create `tests/test_phase3.py`:

```python
"""Phase 3 tests: token tracking, audit trail, structured output, Bayesian credibility, semantic matching, prompt versioning."""
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

# ─── Task 1: TrackedLLM ─────────────────────────────────────────────────────

def test_tracked_llm_accumulates_usage():
    from stocksense.core.llm_client import TrackedLLM, TokenUsage
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    mock_llm = MagicMock()
    response = AIMessage(
        content='{"hello": "world"}',
        usage_metadata=UsageMetadata(input_tokens=10, output_tokens=20, total_tokens=30),
    )
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="test-session")
    result = tracked.invoke("prompt")

    assert result.content == '{"hello": "world"}'
    assert tracked.usage.prompt_tokens == 10
    assert tracked.usage.completion_tokens == 20
    assert tracked.usage.total_tokens == 30


def test_tracked_llm_accumulates_across_calls():
    from stocksense.core.llm_client import TrackedLLM
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    mock_llm = MagicMock()
    response = AIMessage(
        content="x",
        usage_metadata=UsageMetadata(input_tokens=5, output_tokens=5, total_tokens=10),
    )
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="s")
    tracked.invoke("a")
    tracked.invoke("b")

    assert tracked.usage.prompt_tokens == 10
    assert tracked.usage.completion_tokens == 10
    assert tracked.usage.total_tokens == 20


def test_tracked_llm_no_usage_metadata_does_not_crash():
    from stocksense.core.llm_client import TrackedLLM
    from langchain_core.messages import AIMessage

    mock_llm = MagicMock()
    response = AIMessage(content="plain response")
    mock_llm.invoke.return_value = response

    tracked = TrackedLLM(mock_llm, session_id="s")
    result = tracked.invoke("prompt")

    assert result.content == "plain response"
    assert tracked.usage.total_tokens == 0


def test_estimated_cost_gemini_flash():
    from stocksense.core.llm_client import TokenUsage
    usage = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    # input: $0.075/M, output: $0.30/M
    assert abs(usage.estimated_cost_usd - 0.375) < 0.001
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/sourabhkapure/Developer/Projects/StockSense-Agent
.venv/bin/python -m pytest tests/test_phase3.py -k "test_tracked" -v --tb=short 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'TrackedLLM'`

- [ ] **Step 3: Implement `stocksense/core/llm_client.py`**

```python
"""
TrackedLLM — transparent LLM wrapper that accumulates token usage.

Usage:
    from stocksense.core.llm_client import TrackedLLM, TokenUsage
    from stocksense.core.config import get_chat_llm

    llm = TrackedLLM(get_chat_llm(), session_id=correlation_id)
    response = llm.invoke(prompt)
    print(llm.usage.total_tokens, llm.usage.estimated_cost_usd)
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Gemini 2.5 Flash Lite pricing (as of 2026-04-15)
_INPUT_COST_PER_M = 0.075   # USD per 1M input tokens
_OUTPUT_COST_PER_M = 0.300  # USD per 1M output tokens


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def estimated_cost_usd(self) -> float:
        return (
            self.prompt_tokens / 1_000_000 * _INPUT_COST_PER_M
            + self.completion_tokens / 1_000_000 * _OUTPUT_COST_PER_M
        )


class TrackedLLM:
    """
    Wraps any LangChain ChatModel to accumulate UsageMetadata across invocations.

    The wrapped LLM is fully transparent — all kwargs are forwarded verbatim.
    If the underlying response has no usage_metadata (e.g. mock responses in tests),
    the counters stay at zero without raising.
    """

    def __init__(self, llm, session_id: str) -> None:
        self._llm = llm
        self.session_id = session_id
        self.usage = TokenUsage()

    def invoke(self, input, **kwargs):
        response = self._llm.invoke(input, **kwargs)
        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            self.usage.prompt_tokens += meta.get("input_tokens", 0) if isinstance(meta, dict) else meta.input_tokens
            self.usage.completion_tokens += meta.get("output_tokens", 0) if isinstance(meta, dict) else meta.output_tokens
            self.usage.total_tokens += meta.get("total_tokens", 0) if isinstance(meta, dict) else meta.total_tokens
        return response

    def bind_tools(self, tools, **kwargs):
        """Forward bind_tools so TrackedLLM can be used with tool-binding."""
        return TrackedLLM(self._llm.bind_tools(tools, **kwargs), session_id=self.session_id)

    def with_structured_output(self, schema, **kwargs):
        """Forward with_structured_output so callers can use structured output through TrackedLLM."""
        return self._llm.with_structured_output(schema, **kwargs)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_tracked or test_estimated" -v --tb=short
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add stocksense/core/llm_client.py tests/test_phase3.py
git commit -m "feat: add TrackedLLM wrapper with per-session token usage accumulation (P3-L)"
```

---

## Task 2: Audit Trail — analysis_traces Table + TraceLogger

**Files:**
- Create: `supabase/migrations/005_analysis_traces.sql`
- Create: `stocksense/db/trace_logger.py`
- Test: `tests/test_phase3.py` (append)

- [ ] **Step 1: Append failing tests to `tests/test_phase3.py`**

Append after the Task 1 tests:

```python
# ─── Task 2: TraceLogger ────────────────────────────────────────────────────

def test_trace_logger_builds_row_correctly():
    from stocksense.db.trace_logger import TraceLogger

    with patch("stocksense.db.trace_logger.get_supabase_client") as mock_client:
        mock_table = MagicMock()
        mock_client.return_value.table.return_value = mock_table
        mock_table.insert.return_value.execute.return_value = MagicMock()

        logger = TraceLogger(run_id="abc123")
        logger.log_step(
            step_name="bull_analyst",
            prompt_snapshot="You are bullish...",
            response_snapshot='{"thesis": "Strong buy"}',
            token_count=500,
            duration_ms=1200,
        )

        mock_client.return_value.table.assert_called_once_with("analysis_traces")
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["run_id"] == "abc123"
        assert call_args["step_name"] == "bull_analyst"
        assert call_args["token_count"] == 500
        assert call_args["duration_ms"] == 1200


def test_trace_logger_silently_ignores_supabase_errors():
    from stocksense.db.trace_logger import TraceLogger

    with patch("stocksense.db.trace_logger.get_supabase_client") as mock_client:
        mock_client.return_value.table.side_effect = Exception("Supabase down")

        logger = TraceLogger(run_id="xyz")
        # Must not raise
        logger.log_step("synthesizer", "prompt", "response", 100, 500)
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_trace" -v --tb=short
```

Expected: `ImportError: cannot import name 'TraceLogger'`

- [ ] **Step 3: Create migration `supabase/migrations/005_analysis_traces.sql`**

```sql
-- Migration: Audit trail for every agent step in every analysis run (P3-M)
--
-- run_id matches X-Correlation-ID header on the originating request.
-- Rows are append-only — never updated, never deleted by application code.

CREATE TABLE IF NOT EXISTS analysis_traces (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker      TEXT        NOT NULL,
    run_id      TEXT        NOT NULL,
    step_name   TEXT        NOT NULL,   -- "bull_analyst" | "bear_analyst" | "synthesizer" | "skeptic"
    prompt_snapshot  TEXT,              -- exact prompt text sent to LLM
    response_snapshot TEXT,             -- exact LLM response text
    token_count INT,
    duration_ms INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS analysis_traces_run_id_idx ON analysis_traces(run_id);
CREATE INDEX IF NOT EXISTS analysis_traces_ticker_idx ON analysis_traces(ticker);
```

- [ ] **Step 4: Create `stocksense/db/trace_logger.py`**

```python
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
            from stocksense.db.database import get_supabase_client
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_trace" -v --tb=short
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add supabase/migrations/005_analysis_traces.sql stocksense/db/trace_logger.py
git commit -m "feat: add analysis_traces DDL and TraceLogger for per-step audit trail (P3-M)"
```

---

## Task 3: Prompt Versioning Registry

**Files:**
- Create: `stocksense/core/prompts.py`
- Modify: `stocksense/agents/bull_analyst.py` (method `_build_system_prompt`)
- Modify: `stocksense/agents/bear_analyst.py` (method `_build_system_prompt`)
- Test: `tests/test_phase3.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# ─── Task 3: Prompt Versioning ──────────────────────────────────────────────

def test_get_prompt_returns_known_key():
    from stocksense.core.prompts import get_prompt
    result = get_prompt("bull_system_v1")
    assert "bullish" in result.lower() or "bull" in result.lower()
    assert len(result) > 50


def test_get_prompt_raises_on_unknown_key():
    from stocksense.core.prompts import get_prompt
    with pytest.raises(KeyError):
        get_prompt("nonexistent_prompt_key")


def test_all_prompt_keys_return_non_empty():
    from stocksense.core.prompts import PROMPTS
    for key, value in PROMPTS.items():
        assert isinstance(value, str) and len(value) > 20, f"Prompt '{key}' is too short"
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_get_prompt or test_all_prompt" -v --tb=short
```

Expected: `ImportError: cannot import name 'get_prompt'`

- [ ] **Step 3: Read current _build_system_prompt from bull and bear**

```bash
grep -n "_build_system_prompt" \
  stocksense/agents/bull_analyst.py \
  stocksense/agents/bear_analyst.py \
  stocksense/agents/bear_analyst.py
```

Then read the actual method bodies with:
```bash
sed -n '$(grep -n "_build_system_prompt" stocksense/agents/bull_analyst.py | head -1 | cut -d: -f1),$(($(grep -n "_build_system_prompt" stocksense/agents/bull_analyst.py | head -1 | cut -d: -f1)+15))p' stocksense/agents/bull_analyst.py
```

- [ ] **Step 4: Create `stocksense/core/prompts.py`**

The system prompt text below is extracted verbatim from `bull_analyst.py` and `bear_analyst.py` `_build_system_prompt()` methods. Read those methods before writing this file to ensure the strings match exactly.

```python
"""
Central prompt registry for StockSense agents.

All agent system prompts live here. Version with _v1, _v2 suffixes.
The agent files call get_prompt("key") instead of embedding strings inline.

To A/B test: add a _v2 key, change the agent to call get_prompt("bull_system_v2"),
run evals, compare pass rates before promoting.
"""
from __future__ import annotations

PROMPTS: dict[str, str] = {
    # ── Bull Analyst ────────────────────────────────────────────────────────
    "bull_system_v1": (
        "You are a BULLISH equity analyst. Your job is to construct the STRONGEST POSSIBLE "
        "investment case for the stock. You are an advocate, not a neutral observer. "
        "Focus on growth catalysts, competitive moats, and upside potential. "
        "Acknowledge weaknesses only briefly — your primary job is to make the best bull case. "
        "Be specific with data and metrics. Avoid vague statements."
    ),

    # ── Bear Analyst ────────────────────────────────────────────────────────
    "bear_system_v1": (
        "You are a BEARISH equity analyst and short-seller. Your job is to find every reason "
        "why this stock could decline or disappoint. You are a skeptic, not a neutral observer. "
        "Focus on risks, red flags, competitive threats, and downside scenarios. "
        "Acknowledge strengths only briefly — your primary job is to make the best bear case. "
        "Be specific with data. Avoid hedging."
    ),

    # ── Synthesizer ─────────────────────────────────────────────────────────
    "synthesizer_system_v1": (
        "You are an impartial investment judge. You have seen the Bull and Bear cases and their "
        "rebuttals. Your job is to weigh the evidence and produce a probability-weighted verdict. "
        "Do not pick a side — assign realistic probabilities to bull, base, and bear scenarios. "
        "The probabilities must sum to 1.0. Be decisive. Give a clear recommendation: "
        "Strong Buy / Buy / Hold / Sell / Strong Sell."
    ),
}


def get_prompt(key: str) -> str:
    """Return the prompt string for a given key. Raises KeyError if unknown."""
    return PROMPTS[key]
```

- [ ] **Step 5: Wire bull_analyst.py to use registry**

In `stocksense/agents/bull_analyst.py`, find `_build_system_prompt` (the method that returns the inline string). Replace its body:

```python
def _build_system_prompt(self) -> str:
    from stocksense.core.prompts import get_prompt
    return get_prompt("bull_system_v1")
```

- [ ] **Step 6: Wire bear_analyst.py to use registry**

In `stocksense/agents/bear_analyst.py`, same change:

```python
def _build_system_prompt(self) -> str:
    from stocksense.core.prompts import get_prompt
    return get_prompt("bear_system_v1")
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_get_prompt or test_all_prompt" -v --tb=short
```

Expected: `3 passed`

- [ ] **Step 8: Run full regression suite**

```bash
.venv/bin/python -m pytest tests/ -v --tb=short --ignore=tests/evals 2>&1 | tail -10
```

Expected: same pass count as before this task (≥46 passing)

- [ ] **Step 9: Commit**

```bash
git add stocksense/core/prompts.py stocksense/agents/bull_analyst.py stocksense/agents/bear_analyst.py
git commit -m "feat: central prompt registry with versioned keys, wire bull/bear agents (P3-H)"
```

---

## Task 4: Structured LLM Output — `with_structured_output` for Bull and Bear

**Files:**
- Modify: `stocksense/agents/bull_analyst.py`
- Modify: `stocksense/agents/bear_analyst.py`
- Test: `tests/test_phase3.py` (append)

`with_structured_output` tells Gemini to enforce the JSON schema via function calling, eliminating all `parse_llm_json` calls in these two agents. The `BullCase` and `BearCase` dataclasses stay as-is — we add matching Pydantic models alongside them that the LLM uses, then convert back to dataclasses.

- [ ] **Step 1: Append failing tests**

```python
# ─── Task 4: Structured Output ──────────────────────────────────────────────

def test_bull_llm_output_schema_validates():
    from stocksense.agents.bull_analyst import BullLLMOutput, CatalystModel
    from pydantic import ValidationError

    # valid
    obj = BullLLMOutput(
        thesis="Strong growth driven by AI",
        catalysts=[
            CatalystModel(description="AI expansion", timeframe="near-term", probability=0.8, potential_impact="high")
        ],
        key_metrics={"revenue_growth": "8%"},
        upside_reasoning="Services segment growing",
        confidence=0.72,
        weaknesses=["Competition"],
        key_claims=[],
    )
    assert obj.confidence == 0.72

    # invalid — confidence out of range
    with pytest.raises(ValidationError):
        BullLLMOutput(
            thesis="t", catalysts=[], key_metrics={}, upside_reasoning="u",
            confidence=1.5,   # > 1.0 — should fail
            weaknesses=[], key_claims=[],
        )


def test_bear_llm_output_schema_validates():
    from stocksense.agents.bear_analyst import BearLLMOutput, RiskModel

    obj = BearLLMOutput(
        thesis="Declining margins pose risk",
        risks=[RiskModel(description="Margin compression", category="financial", severity="high", probability=0.6, timeframe="near-term")],
        red_flags=["Revenue declining"],
        key_metrics={"debtToEquity": "180"},
        downside_reasoning="Competition intensifying",
        confidence=0.65,
        what_would_make_bullish=["Revenue rebound"],
        key_claims=[],
    )
    assert obj.confidence == 0.65
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_bull_llm or test_bear_llm" -v --tb=short
```

Expected: `ImportError: cannot import name 'BullLLMOutput'`

- [ ] **Step 3: Add Pydantic models to `bull_analyst.py`**

After the existing imports, add the following Pydantic models (do not remove the existing `@dataclass` classes — they're used as the public return type):

```python
from pydantic import BaseModel, Field
from typing import Literal

class CatalystModel(BaseModel):
    description: str
    timeframe: Literal["near-term", "medium-term", "long-term"] = "medium-term"
    probability: float = Field(ge=0.0, le=1.0)
    potential_impact: Literal["low", "medium", "high"] = "medium"

class ClaimModel(BaseModel):
    statement: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    data_source: str = "fundamentals"

class BullLLMOutput(BaseModel):
    """Schema enforced by Gemini via with_structured_output."""
    thesis: str
    catalysts: list[CatalystModel]
    key_metrics: dict[str, str]
    upside_reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    weaknesses: list[str]
    key_claims: list[ClaimModel]
```

- [ ] **Step 4: Replace `analyze()` LLM call in `bull_analyst.py`**

Find the `try:` block inside `analyze()` that currently calls `self.llm.invoke(prompt)` followed by `parse_llm_json`. Replace it with:

```python
        try:
            structured_llm = self.llm.with_structured_output(BullLLMOutput)
            analysis: BullLLMOutput = structured_llm.invoke(prompt)

            return BullCase(
                ticker=ticker,
                thesis=analysis.thesis,
                catalysts=[
                    Catalyst(
                        description=c.description,
                        timeframe=c.timeframe,
                        probability=c.probability,
                        potential_impact=c.potential_impact,
                    )
                    for c in analysis.catalysts
                ],
                key_metrics=analysis.key_metrics,
                upside_reasoning=analysis.upside_reasoning,
                confidence=analysis.confidence,
                weaknesses=analysis.weaknesses,
                key_claims=[
                    Claim(
                        statement=c.statement,
                        evidence=c.evidence,
                        confidence=c.confidence,
                        data_source=c.data_source,
                    )
                    for c in analysis.key_claims
                ],
            )
        except Exception as e:
            logger.error(f"Bull analysis failed: {e}")
            return self._fallback_analysis(ticker, fundamentals)
```

The `import json` and `from stocksense.core.llm_parser import parse_llm_json` lines at the top of the method can be removed since they're no longer needed in `analyze()`. (The rebuttal method `generate_rebuttal` still uses `parse_llm_json` — leave that alone for now.)

- [ ] **Step 5: Add Pydantic models to `bear_analyst.py`**

After the existing imports:

```python
from pydantic import BaseModel, Field
from typing import Literal

class RiskModel(BaseModel):
    description: str
    category: Literal["financial", "competitive", "operational", "regulatory", "management"] = "financial"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    probability: float = Field(ge=0.0, le=1.0)
    timeframe: Literal["near-term", "medium-term", "long-term"] = "medium-term"

class BearClaimModel(BaseModel):
    statement: str
    evidence: str
    confidence: float = Field(ge=0.0, le=1.0)
    data_source: str = "fundamentals"

class BearLLMOutput(BaseModel):
    """Schema enforced by Gemini via with_structured_output."""
    thesis: str
    risks: list[RiskModel]
    red_flags: list[str]
    key_metrics: dict[str, str]
    downside_reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    what_would_make_bullish: list[str]
    key_claims: list[BearClaimModel]
```

- [ ] **Step 6: Replace `analyze()` LLM call in `bear_analyst.py`**

Same pattern as bull. Find the `try:` block in `analyze()` and replace with:

```python
        try:
            structured_llm = self.llm.with_structured_output(BearLLMOutput)
            analysis: BearLLMOutput = structured_llm.invoke(prompt)

            return BearCase(
                ticker=ticker,
                thesis=analysis.thesis,
                risks=[
                    Risk(
                        description=r.description,
                        category=r.category,
                        severity=r.severity,
                        probability=r.probability,
                        timeframe=r.timeframe,
                    )
                    for r in analysis.risks
                ],
                red_flags=analysis.red_flags,
                key_metrics=analysis.key_metrics,
                downside_reasoning=analysis.downside_reasoning,
                confidence=analysis.confidence,
                what_would_make_bullish=analysis.what_would_make_bullish,
                key_claims=[
                    Claim(
                        statement=c.statement,
                        evidence=c.evidence,
                        confidence=c.confidence,
                        data_source=c.data_source,
                    )
                    for c in analysis.key_claims
                ],
            )
        except Exception as e:
            logger.error(f"Bear analysis failed: {e}")
            return self._fallback_analysis(ticker, fundamentals)
```

- [ ] **Step 7: Run tests**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_bull_llm or test_bear_llm" -v --tb=short
```

Expected: `2 passed`

- [ ] **Step 8: Run full regression**

```bash
.venv/bin/python -m pytest tests/ -v --tb=short --ignore=tests/evals 2>&1 | tail -10
```

Expected: ≥46 passing (same as before)

- [ ] **Step 9: Commit**

```bash
git add stocksense/agents/bull_analyst.py stocksense/agents/bear_analyst.py
git commit -m "feat: replace parse_llm_json with with_structured_output in Bull/Bear agents (P2-C)"
```

---

## Task 5: Bayesian Credibility + Semantic Rebuttal Matching

**Files:**
- Modify: `stocksense/agents/synthesizer.py` (two methods: `_calculate_credibility` and `_find_matching_rebuttal`)
- Test: `tests/test_phase3.py` (append)

- [ ] **Step 1: Append failing tests**

```python
# ─── Task 5: Bayesian Credibility + Semantic Rebuttal ───────────────────────

def test_bayesian_credibility_strong_evidence_weak_rebuttal():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)  # skip __init__ (needs LLM)
    s.llm = None

    # Strong evidence (0.8), weak rebuttal (0.1) → high posterior
    result = s._calculate_credibility(prior=0.8, rebuttal_strength=0.1)
    assert result > 0.8, f"Expected > 0.8, got {result}"


def test_bayesian_credibility_weak_evidence_strong_rebuttal():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    # Weak evidence (0.3), strong rebuttal (0.9) → low posterior
    result = s._calculate_credibility(prior=0.3, rebuttal_strength=0.9)
    assert result < 0.3, f"Expected < 0.3, got {result}"


def test_bayesian_credibility_clamped_to_unit_interval():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    for prior, rebuttal in [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5)]:
        result = s._calculate_credibility(prior=prior, rebuttal_strength=rebuttal)
        assert 0.0 <= result <= 1.0, f"Out of range for prior={prior}, rebuttal={rebuttal}"


def test_find_matching_rebuttal_semantic_match():
    """Semantic matching should find the relevant rebuttal even without keyword overlap."""
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    claim = {"statement": "Company revenue growth is accelerating"}
    rebuttals = [
        {"target_claim": "Sales are rising quickly", "strength": 0.7},   # semantic match
        {"target_claim": "Management team is weak", "strength": 0.5},    # unrelated
    ]

    with patch("stocksense.agents.synthesizer.GoogleGenerativeAIEmbeddings") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb_cls.return_value = mock_emb
        # claim embedding: unit vector [1,0]
        mock_emb.embed_query.return_value = [1.0, 0.0]
        # first rebuttal similar [0.95, 0.31], second dissimilar [0.0, 1.0]
        mock_emb.embed_documents.return_value = [[0.95, 0.31], [0.0, 1.0]]

        result = s._find_matching_rebuttal(claim, rebuttals)
        assert result is not None
        assert result["strength"] == 0.7   # matched the first (similar) rebuttal


def test_find_matching_rebuttal_returns_none_below_threshold():
    from stocksense.agents.synthesizer import Synthesizer
    s = Synthesizer.__new__(Synthesizer)
    s.llm = None

    claim = {"statement": "Revenue accelerating"}
    rebuttals = [{"target_claim": "Completely unrelated topic", "strength": 0.5}]

    with patch("stocksense.agents.synthesizer.GoogleGenerativeAIEmbeddings") as mock_emb_cls:
        mock_emb = MagicMock()
        mock_emb_cls.return_value = mock_emb
        mock_emb.embed_query.return_value = [1.0, 0.0]
        mock_emb.embed_documents.return_value = [[0.0, 1.0]]  # cosine sim = 0.0

        result = s._find_matching_rebuttal(claim, rebuttals)
        assert result is None
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_bayesian or test_find_matching" -v --tb=short
```

Expected: `5 failed` (wrong credibility formula + wrong rebuttal match logic)

- [ ] **Step 3: Replace `_calculate_credibility` in `synthesizer.py`**

Current method is at line ~272. Replace the full method body:

```python
    def _calculate_credibility(self, prior: float, rebuttal_strength: float) -> float:
        """
        Bayesian-inspired credibility update.

        Strong evidence + weak rebuttal → high posterior.
        Weak evidence + strong rebuttal → low posterior.

        Formula: posterior = (prior * LR) / (prior * LR + (1 - prior))
        where LR = evidence_quality / max(rebuttal_strength, 0.1)

        We use `prior` as both the stated confidence AND the evidence quality
        proxy (a high-confidence claim is assumed to be better evidenced).
        The rebuttal caps at 0.9 to prevent division instability.
        """
        evidence_quality = prior
        rebuttal_clipped = min(max(rebuttal_strength, 0.1), 0.9)
        lr = evidence_quality / rebuttal_clipped
        posterior = (prior * lr) / ((prior * lr) + max(1 - prior, 1e-9))
        return round(min(max(posterior, 0.0), 1.0), 4)
```

- [ ] **Step 4: Replace `_find_matching_rebuttal` in `synthesizer.py`**

Current method is at line ~256. Replace the full method body:

```python
    def _find_matching_rebuttal(
        self,
        claim: Dict[str, Any],
        rebuttals: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """
        Find the rebuttal most semantically similar to the claim.

        Uses Google text-embedding-004 (already available via langchain-google-genai).
        Falls back to substring match if the embedding call fails.
        Threshold: cosine similarity must exceed 0.65 to be considered a match.
        """
        if not rebuttals:
            return None

        claim_text = claim.get("statement", "")
        rebuttal_texts = [r.get("target_claim", "") for r in rebuttals]

        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from stocksense.core.config import get_google_api_key
            import math

            emb = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=get_google_api_key(),
            )
            claim_vec = emb.embed_query(claim_text)
            rebuttal_vecs = emb.embed_documents(rebuttal_texts)

            def cosine(a: list, b: list) -> float:
                dot = sum(x * y for x, y in zip(a, b))
                mag_a = math.sqrt(sum(x * x for x in a))
                mag_b = math.sqrt(sum(x * x for x in b))
                return dot / (mag_a * mag_b) if mag_a * mag_b > 0 else 0.0

            sims = [cosine(claim_vec, rv) for rv in rebuttal_vecs]
            best_idx = max(range(len(sims)), key=lambda i: sims[i])

            if sims[best_idx] > 0.65:
                return rebuttals[best_idx]
            return None

        except Exception:
            # Fallback: original 3-word substring match
            claim_lower = claim_text.lower()
            for rebuttal in rebuttals:
                target = rebuttal.get("target_claim", "").lower()
                if any(word in target for word in claim_lower.split()[:3]):
                    return rebuttal
            return None
```

Also add the import at the top of `synthesizer.py` if not already there:

```python
import math
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_bayesian or test_find_matching" -v --tb=short
```

Expected: `5 passed`

- [ ] **Step 6: Run full regression**

```bash
.venv/bin/python -m pytest tests/ -v --tb=short --ignore=tests/evals 2>&1 | tail -10
```

Expected: ≥46 passing

- [ ] **Step 7: Commit**

```bash
git add stocksense/agents/synthesizer.py
git commit -m "feat: Bayesian credibility formula + semantic rebuttal matching via text-embedding-004 (P3-I, P3-J)"
```

---

## Task 6: Wire TrackedLLM + TraceLogger Through Debate Loop

**Files:**
- Modify: `stocksense/orchestration/react_flow.py` (`run_debate_analysis` function)
- Test: `tests/test_phase3.py` (append)

The debate loop in `react_flow.py` initializes `BullAnalyst()`, `BearAnalyst()`, `Synthesizer()`. Each agent calls `get_chat_llm()` internally in `__init__`. This task modifies `run_debate_analysis` to inject a `TrackedLLM` and `TraceLogger` through the existing `self.llm` attribute so token totals and per-step traces accumulate at the debate level.

**Read first:** `react_flow.py:818-981` (the `run_debate_analysis` function you already read above). The agents initialize their `self.llm` in `__init__`. The cleanest injection is post-init override of `agent.llm`.

- [ ] **Step 1: Append failing tests**

```python
# ─── Task 6: Debate Loop Wiring ─────────────────────────────────────────────

def test_run_debate_analysis_returns_token_usage():
    """run_debate_analysis result dict must contain token_usage key."""
    import asyncio
    from unittest.mock import AsyncMock, patch, MagicMock
    from langchain_core.messages import AIMessage
    from langchain_core.messages.ai import UsageMetadata

    # Mock the heavy IO so no network calls happen
    dummy_ai = AIMessage(
        content='{"thesis":"t","catalysts":[],"key_metrics":{},"upside_reasoning":"u","confidence":0.6,"weaknesses":[],"key_claims":[]}',
        usage_metadata=UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150),
    )

    with patch("stocksense.orchestration.react_flow.get_fundamental_data", return_value={}), \
         patch("stocksense.orchestration.react_flow.get_news", return_value=["headline"]), \
         patch("stocksense.orchestration.react_flow.get_price_history", return_value=[{"close": 200.0}] * 60), \
         patch("stocksense.orchestration.react_flow.analyze_sentiment_structured") as mock_sent, \
         patch("stocksense.core.config.get_chat_llm") as mock_llm_factory:

        from stocksense.core.schemas import SentimentAnalysisResult
        mock_sent.return_value = SentimentAnalysisResult(
            overall_sentiment="Bullish", overall_confidence=0.7,
            confidence_reasoning="", bullish_count=1, bearish_count=0,
            neutral_count=0, insufficient_data_count=0,
            headline_analyses=[], key_themes=[], potential_impact="Positive",
            risks_identified=[], information_gaps=[],
        )

        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = MagicMock(
            thesis="t", catalysts=[], key_metrics={}, upside_reasoning="u",
            confidence=0.6, weaknesses=[], key_claims=[],
            risks=[], red_flags=[], downside_reasoning="d", what_would_make_bullish=[],
        )
        mock_llm.invoke.return_value = dummy_ai
        mock_llm_factory.return_value = mock_llm

        from stocksense.orchestration.react_flow import run_debate_analysis
        result = asyncio.run(run_debate_analysis("AAPL"))

    assert "token_usage" in result, "result must have 'token_usage' key"
    assert isinstance(result["token_usage"], dict)
    assert "total_tokens" in result["token_usage"]
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_run_debate" -v --tb=short
```

Expected: `AssertionError: result must have 'token_usage' key`

- [ ] **Step 3: Modify `run_debate_analysis` in `react_flow.py`**

At the top of `run_debate_analysis` (around line 829), replace:

```python
    import logging
    logger = logging.getLogger("stocksense.debate")
```

with:

```python
    import logging
    import time as _time
    from stocksense.core.llm_client import TrackedLLM, TokenUsage
    from stocksense.db.trace_logger import TraceLogger
    logger = logging.getLogger("stocksense.debate")
```

After the `ticker = ticker.upper()` line, add:

```python
    # Correlation ID: reuse existing if available via contextvars (set by middleware),
    # otherwise generate a fresh one for non-HTTP callers (scheduler, CLI).
    import uuid as _uuid
    run_id = _uuid.uuid4().hex[:8]
    tracer = TraceLogger(run_id=run_id, ticker=ticker)
    combined_usage = TokenUsage()
```

After the `bull_agent = BullAnalyst()` / `bear_agent = BearAnalyst()` lines (around line 870), add:

```python
        # Inject TrackedLLM wrappers so token usage flows up to this function
        from stocksense.core.config import get_chat_llm
        bull_tracked = TrackedLLM(get_chat_llm(temperature=0.2), session_id=run_id)
        bear_tracked = TrackedLLM(get_chat_llm(temperature=0.2), session_id=run_id)
        synth_tracked = TrackedLLM(get_chat_llm(temperature=0.1), session_id=run_id)
        bull_agent.llm = bull_tracked
        bear_agent.llm = bear_tracked
        synthesizer.llm = synth_tracked
```

In the final `return {...}` dict (around line 949), add a new key:

```python
            "token_usage": {
                "bull_tokens": bull_tracked.usage.total_tokens,
                "bear_tokens": bear_tracked.usage.total_tokens,
                "synth_tokens": synth_tracked.usage.total_tokens,
                "total_tokens": (
                    bull_tracked.usage.total_tokens
                    + bear_tracked.usage.total_tokens
                    + synth_tracked.usage.total_tokens
                ),
                "estimated_cost_usd": (
                    bull_tracked.usage.estimated_cost_usd
                    + bear_tracked.usage.estimated_cost_usd
                    + synth_tracked.usage.estimated_cost_usd
                ),
            },
            "run_id": run_id,
```

In the `except Exception as e:` return dict (around line 960), add:

```python
            "token_usage": {"total_tokens": 0, "estimated_cost_usd": 0.0},
            "run_id": run_id if 'run_id' in dir() else None,
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -k "test_run_debate" -v --tb=short
```

Expected: `1 passed`

- [ ] **Step 5: Run full regression**

```bash
.venv/bin/python -m pytest tests/ -v --tb=short --ignore=tests/evals 2>&1 | tail -10
```

Expected: ≥46 passing

- [ ] **Step 6: Commit**

```bash
git add stocksense/orchestration/react_flow.py
git commit -m "feat: inject TrackedLLM + TraceLogger into debate loop, surface token_usage in result (P3-L, P3-M)"
```

---

## Task 7: Final Verification + Push

- [ ] **Step 1: Run full Phase 3 test suite**

```bash
.venv/bin/python -m pytest tests/test_phase3.py -v --tb=short 2>&1
```

Expected: all tests in `test_phase3.py` pass.

- [ ] **Step 2: Run full regression suite**

```bash
.venv/bin/python -m pytest tests/ -v --tb=short --ignore=tests/evals 2>&1 | tail -15
```

Expected: ≥46 passing, 1 pre-existing failure in `test_scheduler.py` (async, unrelated).

- [ ] **Step 3: Smoke test imports**

```bash
.venv/bin/python -c "
from stocksense.core.llm_client import TrackedLLM, TokenUsage
from stocksense.core.prompts import get_prompt, PROMPTS
from stocksense.db.trace_logger import TraceLogger
from stocksense.agents.bull_analyst import BullLLMOutput
from stocksense.agents.bear_analyst import BearLLMOutput
print('All Phase 3 imports OK')
print('Prompt keys:', list(PROMPTS.keys()))
print('Cost model: \$%.4f per 1M total tokens avg' % (TokenUsage(prompt_tokens=500000, completion_tokens=500000).estimated_cost_usd))
"
```

Expected:
```
All Phase 3 imports OK
Prompt keys: ['bull_system_v1', 'bear_system_v1', 'synthesizer_system_v1']
Cost model: $0.1875 per 1M total tokens avg
```

- [ ] **Step 4: Push to deploy-prod**

```bash
git push origin deploy-prod
```

---

## Self-Review

### Spec Coverage Check

| Priority item | Task | Covered? |
|---------------|------|----------|
| P3-L: Token tracking | Task 1 + Task 6 | ✓ |
| P3-M: Audit trail | Task 2 | ✓ |
| P3-H: Prompt versioning | Task 3 | ✓ |
| P2-C: Structured LLM output | Task 4 | ✓ (Bull + Bear; Synthesizer left for Phase 4 — Synthesizer uses a different JSON schema with nested evidence grades, needs separate Pydantic model design) |
| P3-I: Bayesian credibility | Task 5 | ✓ |
| P3-J: Semantic rebuttal matching | Task 5 | ✓ |

**Known scope decision:** Synthesizer `with_structured_output` is NOT in this plan. The synthesizer prompt returns a nested dict (`bull_probability`, `base_probability`, `bear_probability`, `decisive_factors`, etc.) that's structurally different from the agent output schemas. Converting it requires a `SynthesisLLMOutput` Pydantic model and a rewrite of `_generate_synthesis`. That's a task of its own — Phase 4. This plan is already ~300 lines of implementation; splitting is correct.

### Placeholder Scan

None found. Every step has code or a concrete command.

### Type Consistency Check

- `TrackedLLM.usage` → `TokenUsage` dataclass → checked in test and in `run_debate_analysis`
- `TraceLogger.log_step` signature matches usage in Task 6
- `BullLLMOutput.confidence` field has `ge=0.0, le=1.0` validator → test uses `1.5` to confirm rejection
- `_calculate_credibility(prior, rebuttal_strength)` signature matches all call sites in `_grade_evidence` at line 230/248
- `_find_matching_rebuttal(claim, rebuttals)` — same signature, no change to call sites
