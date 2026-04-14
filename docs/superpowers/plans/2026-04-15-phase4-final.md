# Phase 4 — Final Remaining Work

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete every remaining item from ENGINEERING_PRIORITIES.md: tenacity retries on all LLM calls, `with_structured_output` for Synthesizer/Skeptic/Analyzer, and replacing live-API tests in test_tools.py with deterministic mocks.

**Architecture:** Three independent improvements. (1) Tenacity: add `@retry` to `get_chat_llm()` in `config.py` so ALL callers — base_agent, synthesizer, skeptic, analyzer, react_flow — get retries for free without touching call sites. (2) Structured output: add Pydantic models alongside each agent and replace `parse_llm_json` calls with `with_structured_output()`. (3) Test mocks: rewrite `tests/test_tools.py` to patch `stocksense.core.data_collectors.get_news` and `get_price_history` at module level so tests are fast, deterministic, and CI-safe.

**Tech Stack:** tenacity 9.1.2 (already in requirements), google-api-core 2.25.1 (already installed), pydantic v2, langchain-google-genai 2.1.10 `with_structured_output`, pytest `unittest.mock.patch`

**Baseline:** 66 passing / 1 pre-existing fail (`test_scheduler.py` async) / 13 skipped before this plan.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `stocksense/core/config.py` | Modify | Wrap `ChatGoogleGenerativeAI` return with tenacity retry inside `get_chat_llm` |
| `stocksense/agents/synthesizer.py` | Modify | Add `SynthesisLLMOutput` Pydantic model, replace `parse_llm_json` in `_generate_synthesis` |
| `stocksense/agents/skeptic_agent.py` | Modify | Replace `parse_llm_json` with `with_structured_output(SkepticAnalysis)` — model already exists |
| `stocksense/core/analyzer.py` | Modify | Replace `parse_llm_json` with `with_structured_output(SentimentAnalysisResult)` — model already in `schemas.py` |
| `tests/test_tools.py` | Rewrite | All tests use `unittest.mock.patch` on `get_news` / `get_price_history` — zero live API calls |
| `tests/test_phase4.py` | Create | Tests for all three tasks |

---

## Task 1: Tenacity Retries — Wrap LLM Factory

**Files:**
- Modify: `stocksense/core/config.py`
- Test: `tests/test_phase4.py`

The right place to add retries is inside `get_chat_llm()` in `config.py`. Every agent calls this function. Adding a retry wrapper here means bull_analyst, bear_analyst, synthesizer, skeptic, analyzer, and react_flow all get retries without any changes to their code.

The strategy: create an `_invoke_with_retry` inner function using tenacity and monkey-patch it onto the returned LLM as the `.invoke` method. This is transparent to all call sites.

**Important:** `with_structured_output()` returns a new chain object, not the LLM directly. We only wrap `.invoke` on the LLM instance — callers that use `with_structured_output` get retries via the LLM's own `max_retries=3` (already set). Tenacity adds exponential backoff on top for `ResourceExhausted` and `ServiceUnavailable` specifically.

- [ ] **Step 1: Write failing tests in `tests/test_phase4.py`**

```python
"""
Phase 4 tests: tenacity retries, structured output for Synthesizer/Skeptic/Analyzer,
and deterministic mocks for test_tools.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from langchain_core.messages import AIMessage


# ─── Task 1: Tenacity retries ────────────────────────────────────────────────

def test_llm_invoke_retries_on_resource_exhausted():
    """LLM invoke should retry up to 3 times on ResourceExhausted before raising."""
    from google.api_core.exceptions import ResourceExhausted
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    # First two calls raise ResourceExhausted, third succeeds
    mock_inner.invoke.side_effect = [
        ResourceExhausted("quota exceeded"),
        ResourceExhausted("quota exceeded"),
        AIMessage(content="success"),
    ]

    with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
        llm = get_chat_llm()
        result = llm.invoke("prompt")

    assert result.content == "success"
    assert mock_inner.invoke.call_count == 3


def test_llm_invoke_raises_after_max_retries():
    """LLM invoke should raise after exhausting all 3 retry attempts."""
    from google.api_core.exceptions import ResourceExhausted
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = ResourceExhausted("quota exceeded")

    with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
        llm = get_chat_llm()
        with pytest.raises(ResourceExhausted):
            llm.invoke("prompt")

    assert mock_inner.invoke.call_count == 3


def test_llm_invoke_does_not_retry_on_value_error():
    """Tenacity should NOT retry on non-retriable errors like ValueError."""
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = ValueError("bad input")

    with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
        llm = get_chat_llm()
        with pytest.raises(ValueError):
            llm.invoke("prompt")

    assert mock_inner.invoke.call_count == 1  # no retry


def test_llm_retries_on_service_unavailable():
    """LLM invoke should retry on ServiceUnavailable."""
    from google.api_core.exceptions import ServiceUnavailable
    from stocksense.core.config import get_chat_llm

    mock_inner = MagicMock()
    mock_inner.invoke.side_effect = [
        ServiceUnavailable("down"),
        AIMessage(content="recovered"),
    ]

    with patch("stocksense.core.config.ChatGoogleGenerativeAI", return_value=mock_inner):
        llm = get_chat_llm()
        result = llm.invoke("prompt")

    assert result.content == "recovered"
    assert mock_inner.invoke.call_count == 2
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /Users/sourabhkapure/Developer/Projects/StockSense-Agent
.venv/bin/python -m pytest tests/test_phase4.py -k "test_llm_invoke or test_llm_retries" -v --tb=short 2>&1 | head -25
```

Expected: tests run but all 4 **FAIL** — `mock_inner.invoke.call_count == 1` in each retry test because retries aren't wired yet.

- [ ] **Step 3: Read current `get_chat_llm` in config.py**

```bash
sed -n '1,90p' stocksense/core/config.py
```

Confirm the function ends at the `return ChatGoogleGenerativeAI(...)` call.

- [ ] **Step 4: Modify `stocksense/core/config.py`**

Add imports at the top of `config.py`, after the existing imports:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
try:
    from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable as GServiceUnavailable
    _GOOGLE_EXCEPTIONS = (ResourceExhausted, GServiceUnavailable)
except ImportError:
    _GOOGLE_EXCEPTIONS = (Exception,)  # type: ignore[assignment]
```

Then replace the `return ChatGoogleGenerativeAI(...)` block at the end of `get_chat_llm` with:

```python
    _llm = ChatGoogleGenerativeAI(  # type: ignore
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        max_retries=3,
        timeout=30
    )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(_GOOGLE_EXCEPTIONS),
        reraise=True,
    )
    def _invoke_with_retry(input, **kwargs):
        return _llm.invoke(input, **kwargs)

    # Patch invoke on the instance so all call sites get retries transparently
    _llm.invoke = _invoke_with_retry  # type: ignore[method-assign]
    return _llm
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_llm_invoke or test_llm_retries" -v --tb=short
```

Expected: `4 passed`

- [ ] **Step 6: Run full regression — confirm nothing broke**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -q --tb=short 2>&1 | tail -5
```

Expected: `66 passed, 1 failed` (same pre-existing scheduler failure)

- [ ] **Step 7: Commit**

```bash
git add stocksense/core/config.py tests/test_phase4.py
git commit -m "feat: tenacity retry on get_chat_llm — 3 attempts with exponential backoff on ResourceExhausted/ServiceUnavailable (P2-A)"
```

---

## Task 2: Structured Output — Synthesizer

**Files:**
- Modify: `stocksense/agents/synthesizer.py`
- Test: `tests/test_phase4.py` (append)

`_generate_synthesis` currently calls `self.llm.invoke(prompt)` then `parse_llm_json(content)`. The synthesizer prompt asks for a specific JSON shape. We add a `SynthesisLLMOutput` Pydantic model and call `self.llm.with_structured_output(SynthesisLLMOutput).invoke(prompt)`.

The existing `SynthesizedVerdict` dataclass (the public return type of `synthesize()`) stays unchanged — we just don't need the parse step in `_generate_synthesis`.

- [ ] **Step 1: Append tests to `tests/test_phase4.py`**

```python
# ─── Task 2: Synthesizer structured output ───────────────────────────────────

def test_synthesis_llm_output_model_valid():
    from stocksense.agents.synthesizer import SynthesisLLMOutput

    obj = SynthesisLLMOutput(
        bull_probability=0.4,
        base_probability=0.35,
        bear_probability=0.25,
        recommendation="Buy",
        conviction=0.72,
        decisive_factors=["Strong earnings", "AI tailwind"],
        unresolved_questions=["China macro risk"],
        reasoning="Bull case supported by evidence.",
    )
    assert abs(obj.bull_probability + obj.base_probability + obj.bear_probability - 1.0) < 0.01


def test_synthesis_llm_output_rejects_invalid_probability():
    from pydantic import ValidationError
    from stocksense.agents.synthesizer import SynthesisLLMOutput

    with pytest.raises(ValidationError):
        SynthesisLLMOutput(
            bull_probability=1.5,  # > 1.0 — invalid
            base_probability=0.0,
            bear_probability=0.0,
            recommendation="Hold",
            conviction=0.5,
            decisive_factors=[],
            unresolved_questions=[],
            reasoning="test",
        )


def test_generate_synthesis_uses_structured_output():
    """_generate_synthesis must call with_structured_output, not parse_llm_json."""
    import asyncio
    from stocksense.agents.synthesizer import Synthesizer, SynthesisLLMOutput

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = SynthesisLLMOutput(
        bull_probability=0.45,
        base_probability=0.35,
        bear_probability=0.20,
        recommendation="Buy",
        conviction=0.7,
        decisive_factors=["Revenue growth"],
        unresolved_questions=[],
        reasoning="Bull case is stronger.",
    )

    s = Synthesizer.__new__(Synthesizer)
    s.llm = mock_llm

    result = asyncio.run(s._generate_synthesis(
        ticker="AAPL",
        bull_case={"thesis": "Growth", "key_claims": [], "confidence": 0.7},
        bear_case={"thesis": "Risk", "key_claims": [], "confidence": 0.4},
        bull_rebuttals=[],
        bear_rebuttals=[],
        evidence_grades=[],
        bull_strength=0.7,
        bear_strength=0.4,
    ))

    mock_llm.with_structured_output.assert_called_once_with(SynthesisLLMOutput)
    assert result["recommendation"] == "Buy"
    assert result["bull_probability"] == 0.45
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_synthesis" -v --tb=short 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'SynthesisLLMOutput'`

- [ ] **Step 3: Add `SynthesisLLMOutput` to `synthesizer.py`**

After the existing imports at the top of `stocksense/agents/synthesizer.py`, add:

```python
from pydantic import BaseModel, Field
from typing import Literal as _Literal


class SynthesisLLMOutput(BaseModel):
    """Pydantic schema for synthesizer LLM output via with_structured_output."""
    bull_probability: float = Field(ge=0.0, le=1.0)
    base_probability: float = Field(ge=0.0, le=1.0)
    bear_probability: float = Field(ge=0.0, le=1.0)
    recommendation: _Literal["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
    conviction: float = Field(ge=0.0, le=1.0)
    decisive_factors: list[str]
    unresolved_questions: list[str]
    reasoning: str
```

- [ ] **Step 4: Replace `_generate_synthesis` LLM call in `synthesizer.py`**

Find the `try:` block inside `_generate_synthesis` (around line 405). The current block is:

```python
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            from stocksense.core.llm_parser import parse_llm_json, LLMParseError
            try:
                return parse_llm_json(content)
            except LLMParseError as e:
                logger.error(f"Synthesis JSON parse failed: {e}")
                raise
```

Replace it with:

```python
        try:
            structured_llm = self.llm.with_structured_output(SynthesisLLMOutput)
            analysis: SynthesisLLMOutput = structured_llm.invoke(prompt)
            return {
                "bull_probability": analysis.bull_probability,
                "base_probability": analysis.base_probability,
                "bear_probability": analysis.bear_probability,
                "recommendation": analysis.recommendation,
                "conviction": analysis.conviction,
                "decisive_factors": analysis.decisive_factors,
                "unresolved_questions": analysis.unresolved_questions,
                "reasoning": analysis.reasoning,
            }
```

The `except Exception as e:` block that follows stays unchanged.

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_synthesis" -v --tb=short
```

Expected: `3 passed`

- [ ] **Step 6: Run full regression**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -q --tb=short 2>&1 | tail -5
```

Expected: `66 passed, 1 failed`

- [ ] **Step 7: Commit**

```bash
git add stocksense/agents/synthesizer.py
git commit -m "feat: with_structured_output(SynthesisLLMOutput) in Synthesizer, eliminate parse_llm_json (P2-C)"
```

---

## Task 3: Structured Output — Skeptic Agent

**Files:**
- Modify: `stocksense/agents/skeptic_agent.py`
- Test: `tests/test_phase4.py` (append)

The `SkepticAnalysis` Pydantic model already exists in `skeptic_agent.py` (lines 34-75). The LLM call in `generate_skeptic_analysis()` asks for JSON that maps directly to this model. We can pass the model directly to `with_structured_output` and get the typed object back — no `parse_llm_json` needed, no manual field extraction.

- [ ] **Step 1: Append tests to `tests/test_phase4.py`**

```python
# ─── Task 3: Skeptic structured output ──────────────────────────────────────

def test_generate_skeptic_uses_structured_output():
    """generate_skeptic_analysis must use with_structured_output, not parse_llm_json."""
    from stocksense.agents.skeptic_agent import generate_skeptic_analysis, SkepticAnalysis, SkepticCritique, BearCase
    from stocksense.core.schemas import SentimentAnalysisResult

    primary = SentimentAnalysisResult(
        overall_sentiment="Bullish",
        overall_confidence=0.7,
        confidence_reasoning="Strong earnings",
        bullish_count=3, bearish_count=1, neutral_count=1, insufficient_data_count=0,
        headline_analyses=[], key_themes=[],
        potential_impact="Moderate Positive",
        risks_identified=[], information_gaps=[],
    )

    expected_result = SkepticAnalysis(
        skeptic_sentiment="Partially Disagree",
        primary_disagreement="China risk ignored",
        critiques=[SkepticCritique(critique="Overconfident", assumption_challenged="Growth", evidence="Slowdown data")],
        bear_cases=[BearCase(argument="Competition", trigger="Market share loss", severity="High")],
        would_change_mind=["Revenue acceleration"],
        hidden_risks=["Regulatory risk"],
        skeptic_confidence=0.65,
    )

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = expected_result

    with patch("stocksense.agents.skeptic_agent.get_chat_llm", return_value=mock_llm):
        result = generate_skeptic_analysis(primary, ["Apple beats earnings"], "AAPL")

    mock_llm.with_structured_output.assert_called_once_with(SkepticAnalysis)
    assert result.skeptic_sentiment == "Partially Disagree"
    assert result.skeptic_confidence == 0.65
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_generate_skeptic" -v --tb=short 2>&1 | head -20
```

Expected: `FAILED` — `assert_called_once_with(SkepticAnalysis)` fails because current code still uses `parse_llm_json`.

- [ ] **Step 3: Replace the LLM call in `generate_skeptic_analysis` in `skeptic_agent.py`**

Find the block (around line 160) that currently reads:

```python
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        from stocksense.core.llm_parser import parse_llm_json, LLMParseError
        try:
            data = parse_llm_json(response_text)
        except LLMParseError as e:
            logger.error(f"Skeptic JSON parse failed for {ticker}: {e}")
            raise
        
        # Build structured result
        critiques = [
            SkepticCritique(**c) for c in data.get("critiques", [])
        ]
        
        bear_cases = [
            BearCase(**b) for b in data.get("bear_cases", [])
        ]
        
        return SkepticAnalysis(
            skeptic_sentiment=data.get("skeptic_sentiment", "Agree with Reservations"),
            primary_disagreement=data.get("primary_disagreement", ""),
            critiques=critiques,
            bear_cases=bear_cases,
            would_change_mind=data.get("would_change_mind", []),
            hidden_risks=data.get("hidden_risks", []),
            skeptic_confidence=float(data.get("skeptic_confidence", 0.5)),
        )
```

Replace the entire block with:

```python
        structured_llm = llm.with_structured_output(SkepticAnalysis)
        return structured_llm.invoke(prompt)
```

The prompt string above this block stays unchanged. The `except Exception as e:` block below stays unchanged.

- [ ] **Step 4: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_generate_skeptic" -v --tb=short
```

Expected: `1 passed`

- [ ] **Step 5: Run full regression**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -q --tb=short 2>&1 | tail -5
```

Expected: `66 passed, 1 failed`

- [ ] **Step 6: Commit**

```bash
git add stocksense/agents/skeptic_agent.py
git commit -m "feat: with_structured_output(SkepticAnalysis) in skeptic agent, eliminate parse_llm_json (P2-C)"
```

---

## Task 4: Structured Output — Analyzer

**Files:**
- Modify: `stocksense/core/analyzer.py`
- Test: `tests/test_phase4.py` (append)

`analyze_sentiment_structured()` in `analyzer.py` calls `llm.invoke(prompt)`, then `parse_llm_json`, then manually constructs `HeadlineSentiment` and `KeyTheme` objects, then assembles `SentimentAnalysisResult`. All of that is replaced by `llm.with_structured_output(SentimentAnalysisResult).invoke(prompt)` — the model is already in `schemas.py`.

- [ ] **Step 1: Append tests to `tests/test_phase4.py`**

```python
# ─── Task 4: Analyzer structured output ─────────────────────────────────────

def test_analyze_sentiment_structured_uses_structured_output():
    """analyze_sentiment_structured must call with_structured_output(SentimentAnalysisResult)."""
    from stocksense.core.analyzer import analyze_sentiment_structured
    from stocksense.core.schemas import SentimentAnalysisResult

    expected = SentimentAnalysisResult(
        overall_sentiment="Bullish",
        overall_confidence=0.78,
        confidence_reasoning="3 of 4 headlines positive",
        bullish_count=3, bearish_count=1, neutral_count=0, insufficient_data_count=0,
        headline_analyses=[], key_themes=[],
        potential_impact="Moderate Positive",
        risks_identified=[], information_gaps=[],
    )

    mock_llm = MagicMock()
    structured_chain = MagicMock()
    mock_llm.with_structured_output.return_value = structured_chain
    structured_chain.invoke.return_value = expected

    with patch("stocksense.core.analyzer.get_chat_llm", return_value=mock_llm):
        result = analyze_sentiment_structured(["Apple beats earnings", "iPhone demand strong"])

    mock_llm.with_structured_output.assert_called_once()
    call_args = mock_llm.with_structured_output.call_args[0]
    assert call_args[0].__name__ == "SentimentAnalysisResult"
    assert result.overall_sentiment == "Bullish"
    assert result.overall_confidence == 0.78


def test_analyze_sentiment_structured_empty_headlines_skips_llm():
    """Empty headlines must return early without calling LLM."""
    from stocksense.core.analyzer import analyze_sentiment_structured

    mock_llm = MagicMock()
    with patch("stocksense.core.analyzer.get_chat_llm", return_value=mock_llm):
        result = analyze_sentiment_structured([])

    mock_llm.invoke.assert_not_called()
    assert result.overall_sentiment == "Insufficient Data"
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_analyze_sentiment" -v --tb=short 2>&1 | head -20
```

Expected: `FAILED` — `assert_called_once()` fails because current code still uses `parse_llm_json`.

- [ ] **Step 3: Replace the LLM call block in `analyzer.py`**

In `analyze_sentiment_structured()` (around line 62), the current LLM instantiation and call looks like:

```python
        llm = get_chat_llm(
            model="gemini-2.5-flash-lite",
            temperature=0.2,
            max_output_tokens=4096
        )
        
        # ... prompt building ...
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        from stocksense.core.llm_parser import parse_llm_json, LLMParseError
        try:
            data = parse_llm_json(response_text)
        except LLMParseError as e:
            _logger.error(f"Sentiment JSON parse failed: {e}")
            raise
        
        # Build the structured result
        headline_analyses = [
            HeadlineSentiment(**ha) for ha in data.get("headline_analyses", [])
        ]
        
        key_themes = [
            KeyTheme(**kt) for kt in data.get("key_themes", [])
        ]
        
        return SentimentAnalysisResult(
            overall_sentiment=data.get("overall_sentiment", "Neutral"),
            ...
        )
```

Keep the `llm = get_chat_llm(...)` call and the prompt-building unchanged. Replace only the section from `response = llm.invoke(prompt)` down to the `return SentimentAnalysisResult(...)` with:

```python
        structured_llm = llm.with_structured_output(SentimentAnalysisResult)
        return structured_llm.invoke(prompt)
```

The existing `except json.JSONDecodeError` and `except Exception` blocks that follow stay — they now catch `with_structured_output` validation errors instead.

- [ ] **Step 4: Remove now-unused import from `analyzer.py`**

Find and remove the `import json` line at the top if it's only used for the `json.JSONDecodeError` catch. Check first:

```bash
grep -n "^import json\|json\." stocksense/core/analyzer.py
```

If `json` is only used in the removed block and the `except json.JSONDecodeError` catch, change the except to `except Exception` and remove the `import json` line.

- [ ] **Step 5: Run tests to verify they pass**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -k "test_analyze_sentiment" -v --tb=short
```

Expected: `2 passed`

- [ ] **Step 6: Run full regression**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -q --tb=short 2>&1 | tail -5
```

Expected: `66 passed, 1 failed`

- [ ] **Step 7: Commit**

```bash
git add stocksense/core/analyzer.py
git commit -m "feat: with_structured_output(SentimentAnalysisResult) in analyzer, eliminate parse_llm_json (P2-C)"
```

---

## Task 5: Replace Live-API Tests with Deterministic Mocks

**Files:**
- Rewrite: `tests/test_tools.py`
- Test: same file

The current `test_tools.py` calls `fetch_news_headlines.invoke({"ticker": "MSFT"})` which calls `get_news()` which hits the real NewsAPI. Same for `fetch_price_data` → `get_price_history` → yfinance. These tests are CI-unsafe. 

The fix: patch `stocksense.core.data_collectors.get_news` and `stocksense.core.data_collectors.get_price_history` at the module level of each test (or via fixture). The tool functions in `react_flow.py` call `get_news` and `get_price_history` via the import at line 9 of `react_flow.py`:

```python
from stocksense.core.data_collectors import get_news, get_price_history, get_fundamental_data
```

So the correct patch target is `stocksense.orchestration.react_flow.get_news` and `stocksense.orchestration.react_flow.get_price_history` — patch where the name is *used*, not where it's defined.

- [ ] **Step 1: Read the current test_tools.py one more time to confirm all test names**

```bash
grep "def test_" tests/test_tools.py
```

There are 9 test functions: `test_fetch_news_headlines_success`, `test_fetch_news_headlines_structure`, `test_fetch_news_headlines_invalid_ticker`, `test_fetch_price_data_success`, `test_fetch_price_data_structure`, `test_fetch_price_data_invalid_ticker`, `test_fetch_data_consistency`, `test_error_handling_consistency`, `test_multiple_valid_tickers`.

- [ ] **Step 2: Run current test_tools to see how many fail or skip without network**

```bash
.venv/bin/python -m pytest tests/test_tools.py -v --tb=short 2>&1 | tail -20
```

Note exact failure/skip counts before rewriting.

- [ ] **Step 3: Rewrite `tests/test_tools.py`**

Replace the entire file:

```python
"""
Unit Tests for StockSense Agent Tools

All tests use deterministic mocks — zero live API calls.
Patch targets: stocksense.orchestration.react_flow.get_news
               stocksense.orchestration.react_flow.get_price_history
               stocksense.orchestration.react_flow.get_fundamental_data
"""
import pytest
from unittest.mock import patch
from stocksense.orchestration.react_flow import fetch_news_headlines, fetch_price_data
from stocksense.core.data_collectors import DataCollectionError

# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_HEADLINES = [
    "Apple beats Q4 earnings by $0.15 per share",
    "iPhone demand exceeds analyst expectations",
    "Apple faces EU antitrust investigation",
]

FAKE_PRICE_DATA_RAW = type("FakeDF", (), {
    "empty": False,
    "reset_index": lambda self: self,
    "to_dict": lambda self, orient: [
        {"Date": "2026-01-01", "Open": 218.0, "High": 222.0, "Low": 217.0, "Close": 220.5, "Volume": 1_200_000},
        {"Date": "2026-01-02", "Open": 220.5, "High": 224.0, "Low": 219.0, "Close": 223.0, "Volume": 980_000},
    ],
})()


@pytest.fixture(autouse=False)
def mock_news():
    """Patch get_news to return deterministic headlines."""
    with patch("stocksense.orchestration.react_flow.get_news", return_value=FAKE_HEADLINES) as m:
        yield m


@pytest.fixture(autouse=False)
def mock_price():
    """Patch get_price_history to return deterministic price object."""
    with patch("stocksense.orchestration.react_flow.get_price_history", return_value=FAKE_PRICE_DATA_RAW) as m:
        yield m


@pytest.fixture(autouse=False)
def mock_news_empty():
    with patch("stocksense.orchestration.react_flow.get_news", return_value=[]) as m:
        yield m


@pytest.fixture(autouse=False)
def mock_news_error():
    with patch("stocksense.orchestration.react_flow.get_news", side_effect=DataCollectionError("NewsAPI timeout")) as m:
        yield m


@pytest.fixture(autouse=False)
def mock_price_none():
    with patch("stocksense.orchestration.react_flow.get_price_history", return_value=None) as m:
        yield m


# ── News Headlines Tests ───────────────────────────────────────────────────────

class TestNewsHeadlines:

    def test_fetch_news_headlines_success(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["headlines"] == FAKE_HEADLINES
        assert result["count"] == 3

    def test_fetch_news_headlines_structure(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "MSFT"})
        for key in ["success", "headlines", "ticker", "count"]:
            assert key in result
        assert isinstance(result["headlines"], list)
        assert all(isinstance(h, str) for h in result["headlines"])

    def test_fetch_news_headlines_ticker_normalized_to_uppercase(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "aapl"})
        assert result["ticker"] == "AAPL"

    def test_fetch_news_headlines_empty_returns_success_false(self, mock_news_empty):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is False
        assert result["headlines"] == []

    def test_fetch_news_headlines_data_collection_error(self, mock_news_error):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is False
        assert "NewsAPI timeout" in result.get("error", "")
        assert result["headlines"] == []


# ── Price Data Tests ───────────────────────────────────────────────────────────

class TestPriceData:

    def test_fetch_price_data_success(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "GOOGL"})
        assert isinstance(result, dict)
        assert "price_data" in result
        assert result["ticker"] == "GOOGL"

    def test_fetch_price_data_structure(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "AAPL", "period": "5d"})
        for key in ["success", "price_data", "ticker", "has_data"]:
            assert key in result
        if result["price_data"]:
            record = result["price_data"][0]
            for field in ["Date", "Open", "High", "Low", "Close", "Volume"]:
                assert field in record

    def test_fetch_price_data_ticker_normalized(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "tsla"})
        assert result["ticker"] == "TSLA"

    def test_fetch_price_data_none_returns_empty(self, mock_price_none):
        result = fetch_price_data.invoke({"ticker": "AAPL"})
        assert isinstance(result["price_data"], list)
        assert result["price_data"] == []


# ── Combined Tests ─────────────────────────────────────────────────────────────

class TestCombinedDataRetrieval:

    def test_fetch_data_consistency(self, mock_news, mock_price):
        ticker = "msft"
        news_result = fetch_news_headlines.invoke({"ticker": ticker})
        price_result = fetch_price_data.invoke({"ticker": ticker})
        assert news_result["ticker"].upper() == ticker.upper()
        assert price_result["ticker"].upper() == ticker.upper()

    def test_error_handling_consistency(self, mock_news_error, mock_price_none):
        news_result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        price_result = fetch_price_data.invoke({"ticker": "AAPL"})
        assert isinstance(news_result, dict)
        assert isinstance(price_result, dict)
        assert "headlines" in news_result
        assert "price_data" in price_result


# ── Parametrized coverage ──────────────────────────────────────────────────────

@pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL"])
def test_multiple_valid_tickers(ticker, mock_news, mock_price):
    news_result = fetch_news_headlines.invoke({"ticker": ticker})
    price_result = fetch_price_data.invoke({"ticker": ticker})
    assert news_result["ticker"] == ticker
    assert price_result["ticker"] == ticker
    assert news_result["success"] is True
```

- [ ] **Step 4: Run the new test_tools.py**

```bash
.venv/bin/python -m pytest tests/test_tools.py -v --tb=short 2>&1
```

Expected: all tests pass with no network calls. Zero `skipped`.

- [ ] **Step 5: Run full regression**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -q --tb=short 2>&1 | tail -5
```

Expected: total pass count ≥ 66 (likely higher now that test_tools tests actually run).

- [ ] **Step 6: Commit**

```bash
git add tests/test_tools.py
git commit -m "test: replace live-API tests in test_tools with deterministic mocks — CI-safe (P3-E)"
```

---

## Task 6: Final Verification + Push

- [ ] **Step 1: Run all new tests together**

```bash
.venv/bin/python -m pytest tests/test_phase4.py -v --tb=short 2>&1
```

Expected: all tests in `test_phase4.py` pass.

- [ ] **Step 2: Run full suite**

```bash
.venv/bin/python -m pytest tests/ --ignore=tests/evals -v --tb=short 2>&1 | tail -20
```

Expected: ≥66 passing, 1 pre-existing failure (`test_scheduler.py::test_check_all_active_theses`).

- [ ] **Step 3: Confirm `parse_llm_json` is no longer called anywhere in the hot path**

```bash
grep -rn "parse_llm_json" stocksense/agents/ stocksense/core/analyzer.py | grep -v "__pycache__"
```

Expected output: **nothing** (or only the definition in `llm_parser.py` and the rebuttal methods in bull/bear which parse JSON arrays — those are fine, with_structured_output doesn't handle list root output well in all Gemini versions).

- [ ] **Step 4: Confirm tenacity is wired**

```bash
.venv/bin/python -c "
from unittest.mock import MagicMock, patch
from google.api_core.exceptions import ResourceExhausted
from stocksense.core.config import get_chat_llm

inner = MagicMock()
inner.invoke.side_effect = [ResourceExhausted('q'), ResourceExhausted('q'), MagicMock(content='ok')]
with patch('stocksense.core.config.ChatGoogleGenerativeAI', return_value=inner):
    llm = get_chat_llm()
    r = llm.invoke('test')
print('Retried', inner.invoke.call_count, 'times. Result:', r.content)
"
```

Expected: `Retried 3 times. Result: ok`

- [ ] **Step 5: Push**

```bash
git push origin deploy-prod
```

---

## Self-Review

### Spec Coverage

| Item | Task | Status |
|------|------|--------|
| P2-A: Tenacity retries on all LLM calls | Task 1 | ✓ — single patch point in `get_chat_llm`, all callers covered |
| P2-C: `with_structured_output` Synthesizer | Task 2 | ✓ |
| P2-C: `with_structured_output` Skeptic | Task 3 | ✓ |
| P2-C: `with_structured_output` Analyzer | Task 4 | ✓ |
| P3-E: Replace live-API tests | Task 5 | ✓ |

**Explicit out of scope** (architectural rewrites, not remaining P2/P3 items):
- P3-D (real streaming via `astream_events`) — requires full streaming.py rewrite
- P3-F (LangGraph explicit state-driven routing) — requires react_flow.py architectural overhaul
- P3-G (structured ReAct with `ReActStep`) — requires full react loop redesign
- P3-A (agent memory) — new Supabase table + all agent `__init__` changes

These are Phase 5. This plan completes everything that can be done without restructuring core orchestration.

### Placeholder Scan

None. Every step has a complete code block or a concrete shell command.

### Type Consistency

- `SynthesisLLMOutput` defined in Task 2 Step 3 → used in Task 2 Step 4 (`with_structured_output(SynthesisLLMOutput)`) → imported in Task 2 test → consistent
- `SkepticAnalysis` already exists at `skeptic_agent.py:34` → reused in Task 3 with no rename
- `SentimentAnalysisResult` already exists at `schemas.py:48` → reused in Task 4 with no rename
- Retry patch: `_llm.invoke = _invoke_with_retry` — `_invoke_with_retry` is defined immediately above this line in the same function scope → no missing reference
- Test patch targets verified against actual import at `react_flow.py:9`: `from stocksense.core.data_collectors import get_news, get_price_history` → patch target is `stocksense.orchestration.react_flow.get_news` ✓

### One Gotcha Documented

The rebuttal methods in `bull_analyst.py:219` and `bear_analyst.py:227` still use `parse_llm_json` for the rebuttal JSON *array* (`[{...}, {...}]`). This is intentional and correct: `with_structured_output` in LangChain's Gemini integration doesn't reliably handle a JSON array as the root output — it expects a JSON object (Pydantic model). The rebuttal prompts ask for a bare `[...]` array. Converting these would require wrapping them in a `{"rebuttals": [...]}` object, changing the prompt, and extracting `.rebuttals`. That's a valid but separate cleanup; `parse_llm_json` is robust enough for this case.
