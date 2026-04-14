# StockSense — Engineering Priority Master Document

> **Last updated:** 2026-04-15 (rev 2 — AI systems + finance domain gaps added)  
> **Architecture Score:** C+ (74%) — Real pipeline, critical reliability gaps  
> **Goal:** Fix to B+ (85%+) for recruiter demos. Then elevate to showcase-level AI engineering.

---

## Architecture Review Scorecard

| Dimension | Score | Weight | Weighted | Key Finding |
|-----------|-------|--------|----------|-------------|
| Structural Integrity | 2.5/5 | 20% | 0.500 | AgentState 50+ fields, JSON parsing copy-pasted 9x |
| Scalability | 3/5 | 18% | 0.540 | Stateless Cloud Run ✓, no caching, no pagination |
| Security | 3/5 | 18% | 0.540 | Supabase RLS ✓, rate limiting ✓, but no input sanitization |
| Performance | 3/5 | 17% | 0.510 | Async debate ✓, no connection pooling, blocking scheduler |
| Enterprise Readiness | 2.5/5 | 15% | 0.375 | No retries, no observability, alert table name mismatch |
| Operational Excellence | 3/5 | 7% | 0.210 | Cloud Run ✓, no health metrics, flaky tests |
| Data Architecture | 3/5 | 5% | 0.150 | No upsert, no pagination, brittle serialization |

**Overall: (0.500+0.540+0.540+0.510+0.375+0.210+0.150) / 5 × 100 = 74.5% → Grade C+**

---

## The Real Pipeline (What Actually Works)

```
Request → validate_ticker() → check Supabase cache
                                    ↓ (miss)
                         data_collectors.py
                         ├── NewsAPI → headlines[]
                         └── yfinance → price_data[], fundamentals{}
                                    ↓
                         react_flow.py (ReAct loop, max 10 iter)
                         ├── analyze_sentiment_tool → SentimentAnalysisResult ✓ REAL
                         ├── fetch_price_data_tool → OHLCV dict ✓ REAL
                         ├── fetch_news_tool → headlines ✓ REAL
                         ├── generate_skeptic_critique → ❌ BROKEN (analyzes mock data)
                         └── save_analysis_results → Supabase ✓ REAL
                                    ↓
                         Debate path (adversarial):
                         ├── BullAnalyst.analyze() ← asyncio.gather() ✓ PARALLEL
                         ├── BearAnalyst.analyze() ← asyncio.gather() ✓ PARALLEL
                         ├── BullAnalyst.generate_rebuttal() → ✓ REAL
                         ├── BearAnalyst.generate_rebuttal() → ✓ REAL
                         └── Synthesizer.synthesize() → SynthesizedVerdict ✓ REAL
                                    ↓
                         Response → Frontend (Vercel) via CORS
```

**~85% is real. The 15% broken touches the skeptic path specifically.**

---

## PHASE 1 — CRITICAL BUGS (Fix NOW, before any demo)

> These are production-breaking. A recruiter clicking "Analyze AAPL" will hit these.

### P1-A: Skeptic Analyzes Mock Empty Data
**File:** `stocksense/orchestration/react_flow.py:326-341`  
**Severity:** [S1] Critical — Core feature produces invalid output  
**What's broken:**
```python
# CURRENT (BROKEN) — skeptic always sees zeros and empty lists
mock_primary = SentimentAnalysisResult(
    overall_sentiment="",
    overall_confidence=0.0,
    headline_analyses=[],   # ← empty! skeptic has nothing to critique
    ...
)
skeptic_result = generate_skeptic_analysis(mock_primary, headlines, ticker)
```
**Fix:** Pass actual state sentiment result instead:
```python
# CORRECT — pass real sentiment from state
primary_result = state.get("sentiment_result")  # already in state from earlier tool call
if primary_result:
    skeptic_result = generate_skeptic_analysis(primary_result, headlines, ticker)
```
**Effort:** 30 minutes  
**Impact:** Skeptic analysis goes from invalid → genuine counter-perspective

---

### P1-B: JSON Parsing Fragile — 9 Identical Broken Patterns
**Files:** `bull_analyst.py:112,197` | `bear_analyst.py:116,203` | `synthesizer.py:356` | `monitor.py:117,203` | `analyzer.py:127` | `skeptic_agent.py:173`  
**Severity:** [S1] Critical — One malformed LLM response silently kills analysis  
**What's broken:**
```python
# CURRENT (BROKEN) — breaks on: ```json\n{}\n``` vs ```\n{}\n``` vs plain {}
content = content.split("```")[1]  
if content.startswith("json"):
    content = content[4:]
data = json.loads(content)
```
**Fix:** Create ONE shared utility, use everywhere:
```python
# stocksense/core/llm_parser.py
import json, re
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

def parse_llm_json(content: str, model: Type[T] | None = None) -> dict | T:
    """Robustly extract JSON from LLM response regardless of formatting."""
    # Try: extract from ```json ... ``` or ``` ... ```
    code_block = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', content, re.DOTALL)
    if code_block:
        raw = code_block.group(1)
    else:
        # Try: find first { to last }
        start = content.find('{')
        end = content.rfind('}')
        if start == -1 or end == -1:
            raise ValueError(f"No JSON found in LLM response: {content[:200]}")
        raw = content[start:end+1]
    
    parsed = json.loads(raw)
    if model:
        return model(**parsed)
    return parsed
```
Replace all 9 occurrences. Add `try/except json.JSONDecodeError` with proper logging.  
**Effort:** 2 hours  
**Impact:** Eliminates entire class of silent analysis failures

---

### P1-C: Kill Alerts Table Name Mismatch
**File:** `stocksense/api/auth_routes.py:375`  
**Severity:** [S1] Critical — DB error on every kill alert fetch  
**What's broken:**
```python
# auth_routes.py:375
response = client.table("kill_alerts")...  # ← table doesn't exist

# everywhere else:
response = client.table("alert_history")...  # ← actual table name
```
**Fix:** One-line change:
```python
response = client.table("alert_history")...
```
**Effort:** 5 minutes  

---

### P1-D: Ticker Validation Returns Valid on Exception
**File:** `stocksense/core/validation.py:76-79`  
**Severity:** [S2] High — Any ticker passes validation when yfinance errors  
**What's broken:**
```python
except Exception:
    return True, None  # ← wrong! should be False on error
```
**Fix:**
```python
except Exception as e:
    logger.warning(f"yfinance validation failed for {ticker}: {e}")
    return False, f"Could not validate ticker {ticker}. Try again."
```
**Effort:** 5 minutes  

---

### P1-E: Scheduler Cannot Create Alerts (Service Role Gap)
**File:** `stocksense/scheduler.py:66-71`  
**Severity:** [S2] High — Background thesis monitoring creates no alerts  
**What's broken:** Scheduler uses anon client, which is blocked by RLS from writing alerts on behalf of users.  
**Fix:** Use `get_supabase_admin_client()` (already imported) for alert writes:
```python
# scheduler.py — already imported, just use it
from stocksense.db.supabase_client import get_supabase_admin_client
admin_client = get_supabase_admin_client()
admin_client.table("alert_history").insert({...}).execute()
```
**Effort:** 1 hour (verify service key is set in Secret Manager — it is)  

---

## PHASE 2 — HIGH IMPACT IMPROVEMENTS (Do before recruiter shows)

> These turn "it works" into "this is impressive engineering."

### P2-A: Replace Retry-Less LLM Calls with Tenacity
**Files:** All files calling `llm.invoke()` (6 files)  
**Severity:** [S3] Medium — Single Gemini API hiccup kills analysis  
**Fix:** Add `@retry` decorator pattern:
```python
# stocksense/core/llm_client.py (new file)
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.api_core.exceptions

def llm_invoke_with_retry(llm, messages, **kwargs):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            google.api_core.exceptions.ResourceExhausted,
            google.api_core.exceptions.ServiceUnavailable,
        ))
    )
    def _invoke():
        return llm.invoke(messages, **kwargs)
    return _invoke()
```
**Effort:** 3 hours  
**Recruiter signal:** Shows production awareness — LLM APIs are unreliable, retry logic is non-negotiable  

---

### P2-B: Real Information Asymmetry in Debate
**File:** `stocksense/agents/base_agent.py:118-181`  
**Severity:** [S3] Medium — Bull and Bear see identical data, just reordered. Debate is hollow.  
**Current:** Both agents get full dataset, different key ordering  
**Fix — True Asymmetry:**
```python
# base_agent.py
class BullAnalyst(BaseAgent):
    def _filter_data_for_perspective(self, data: dict) -> dict:
        """Bull gets growth/momentum signals."""
        return {
            "price_trend": data.get("price_trend"),
            "revenue_growth": data.get("fundamentals", {}).get("revenueGrowth"),
            "analyst_upgrades": [h for h in data.get("headlines", []) 
                                  if any(w in h.lower() for w in ["upgrade", "buy", "outperform", "beat"])],
            "pe_ratio": data.get("fundamentals", {}).get("trailingPE"),
            "market_cap": data.get("fundamentals", {}).get("marketCap"),
        }

class BearAnalyst(BaseAgent):
    def _filter_data_for_perspective(self, data: dict) -> dict:
        """Bear gets risk/deterioration signals."""
        return {
            "debt_to_equity": data.get("fundamentals", {}).get("debtToEquity"),
            "analyst_downgrades": [h for h in data.get("headlines", [])
                                    if any(w in h.lower() for w in ["downgrade", "sell", "miss", "cut"])],
            "price_decline": data.get("price_trend"),
            "short_interest": data.get("fundamentals", {}).get("shortRatio"),
            "profit_margins": data.get("fundamentals", {}).get("profitMargins"),
        }
```
**Effort:** 4 hours  
**Recruiter signal:** Shows understanding of cognitive bias in LLM agents — real AI engineering insight  

---

### P2-C: Structured LLM Output (Pydantic) for All Agents
**Files:** `bull_analyst.py`, `bear_analyst.py`, `synthesizer.py`, `skeptic_agent.py`  
**Severity:** [S3] Medium — LangChain supports `with_structured_output()`, eliminates all JSON parsing  
**Current:** Raw text → fragile string split → json.loads  
**Fix:**
```python
# Use LangChain's structured output — eliminates ALL JSON parsing code
from langchain_google_genai import ChatGoogleGenerativeAI
from stocksense.core.schemas import BullCase

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
structured_llm = llm.with_structured_output(BullCase)  # ← no JSON parsing needed
result: BullCase = structured_llm.invoke(messages)
```
**Effort:** 6 hours (touch all agent files)  
**Recruiter signal:** Demonstrates LangChain expertise and production LLM patterns  

---

### P2-D: Observability — Structured Logging + Request Tracing
**Files:** `stocksense/main.py`, all agent files  
**Severity:** [S3] Medium — Currently impossible to debug production issues  
**Fix:** Add correlation IDs to all requests:
```python
# main.py — middleware
import uuid
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = str(uuid.uuid4())[:8]
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```
Add structured log fields: `ticker`, `correlation_id`, `agent_name`, `duration_ms`, `llm_tokens_used`  
**Effort:** 3 hours  
**Recruiter signal:** Shows production mindset — observability is table stakes for AI systems  

---

### P2-E: Analysis Caching with TTL (Currently No Cache Invalidation)
**File:** `stocksense/db/database.py`  
**Severity:** [S3] Medium — No upsert, creates duplicate rows, no TTL enforcement  
**Fix:** 
```python
def save_analysis(ticker: str, ...) -> str:
    """Upsert analysis — one row per ticker, updated on refresh."""
    client = get_supabase_client()
    data = {...}
    # Upsert on ticker column
    result = client.table("analysis_cache")\
        .upsert(data, on_conflict="ticker")\
        .execute()
    return result.data[0]["id"]

def get_latest_analysis(ticker: str, max_age_hours: int = 24) -> dict | None:
    """Return cached analysis only if within max_age_hours."""
    client = get_supabase_client()
    cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
    result = client.table("analysis_cache")\
        .select("*")\
        .eq("ticker", ticker)\
        .gte("updated_at", cutoff)\
        .single()\
        .execute()
    return result.data if result.data else None
```
**Effort:** 2 hours  

---

## PHASE 3 — ARCHITECTURE ELEVATIONS (Impress senior engineers)

> These are what differentiate "built an AI app" from "understands AI systems engineering."

### P3-A: Agent Memory — Persistent Context Across Analyses
**Concept:** Agents currently have zero memory. Each analysis starts cold.  
**What to build:** Store analyst "priors" per ticker in Supabase. When the same ticker is analyzed again, Bull/Bear agents get context: "Last time you said X was a risk. Has that materialized?"  
**Architecture:**
```
analyst_memory table:
  ticker | agent_type | prior_thesis | confidence | created_at | updated_at
  
BullAnalyst.analyze() → fetch_prior_memory(ticker, "bull") → inject into prompt
                      → after analysis → update_memory(ticker, "bull", new_thesis)
```
**Why impressive:** Multi-session agent memory is a hard, unsolved problem in AI engineering.  
**Effort:** 1 week  

---

### P3-B: LangGraph State Machine Cleanup
**File:** `stocksense/orchestration/react_flow.py`  
**Current:** `AgentState` TypedDict with 50+ fields mixed across 4 stages. A nightmare.  
**What to build:** Proper state machine with typed sub-states:
```python
class AnalysisState(TypedDict):
    # Input
    ticker: str
    raw_data: RawMarketData  # structured, not dict
    
    # Stage 1: Sentiment
    sentiment: SentimentAnalysisResult | None
    
    # Stage 2: Debate  
    debate: DebateResult | None
    
    # Stage 3: Synthesis
    verdict: SynthesizedVerdict | None
    
    # Meta
    errors: list[str]
    iterations: int
```
**Why impressive:** Shows LangGraph mastery — proper typed state machines are how real production agents are built.  
**Effort:** 3 days  

---

### P3-C: Evidence-Grounded Synthesis
**File:** `stocksense/agents/synthesizer.py:272-278`  
**Current:** `credibility = confidence * (1 - rebuttal_strength * 0.5)` — just math on scores  
**What to build:** Synthesizer verifies claims against raw data:
```python
def _verify_claim_against_data(self, claim: str, data: dict) -> float:
    """Check if a claim is supported by actual market data."""
    # Use LLM to check: "Does the price data support this claim?"
    # Returns 0.0-1.0 evidence score
    verification_prompt = f"""
    Claim: {claim}
    Actual price data: {data['price_data']}
    Actual fundamentals: {data['fundamentals']}
    
    Score 0.0-1.0: how well does the data support this claim?
    """
    return self.llm.invoke(verification_prompt)  # structured output float
```
**Why impressive:** Grounds LLM reasoning in verifiable data — reduces hallucination  
**Effort:** 2 days  

---

### P3-D: Streaming as True Progressive Rendering
**File:** `stocksense/orchestration/streaming.py`  
**Current:** Fake progress with `asyncio.sleep(0.1)` between hardcoded tool steps  
**What to build:** Real streaming using LangGraph's `astream_events`:
```python
async def run_streaming_analysis(ticker: str):
    async for event in graph.astream_events(
        {"ticker": ticker}, 
        version="v2"
    ):
        if event["event"] == "on_tool_start":
            yield StreamEvent(EventType.TOOL_STARTED, {"tool": event["name"]})
        elif event["event"] == "on_tool_end":
            yield StreamEvent(EventType.TOOL_COMPLETED, {"tool": event["name"], "result": event["data"]})
        elif event["event"] == "on_llm_stream":
            yield StreamEvent(EventType.TOKEN, {"token": event["data"]["chunk"]})
```
**Why impressive:** Real-time LLM token streaming is what users expect from modern AI apps.  
**Effort:** 2 days  

---

### P3-E: Test Suite — Replace Flaky Live API Tests with Proper Mocks
**Files:** `tests/test_tools.py`, `tests/test_api.py`  
**Current:** Tests call real NewsAPI and yfinance. CI fails when rate-limited.  
**What to build:**
```python
# tests/conftest.py
@pytest.fixture
def mock_newsapi(monkeypatch):
    def fake_get_headlines(ticker): 
        return ["Apple reports record earnings", "iPhone sales beat expectations"]
    monkeypatch.setattr("stocksense.core.data_collectors.get_news_headlines", fake_get_headlines)

@pytest.fixture  
def mock_yfinance(monkeypatch):
    def fake_get_price(ticker, period):
        return [{"date": "2026-01-01", "close": 185.5, "volume": 1000000}]
    monkeypatch.setattr("stocksense.core.data_collectors.get_price_data", fake_get_price)
```
Add integration tests that test the real pipeline end-to-end (not unit by unit).  
**Effort:** 1 day  

---

## PHASE 3-B — STAFF ENGINEER CONCERNS (Fix before calling this "production-grade")

> These are architectural debt items a staff engineer would flag in any serious code review.
> They don't block demos but expose gaps in AI systems understanding.

### P3F: LangGraph Is Cargo-Culted — Pipeline Isn't a True State Machine
**File:** `stocksense/orchestration/react_flow.py`  
**Severity:** [S3] Medium — LangGraph adds complexity with no benefit over sequential `await` calls  
**What's wrong:** The current "ReAct loop" calls tools in sequence, not based on state transitions. There are no conditional edges based on agent decisions. It's `tool_A() → tool_B() → tool_C()` — a function call chain with LangGraph as the wrapper.  
**What LangGraph is actually for:**
```
Real LangGraph usage:
  state["phase"] == "needs_more_data" → fetch_data_node
  state["phase"] == "ready_to_debate" → debate_node
  state["confidence"] < 0.4          → request_human_review_node
```
**Fix path:** Either (a) add real conditional routing that uses agent decisions to branch the graph, or (b) remove LangGraph entirely and use `asyncio.gather()` + sequential awaits — simpler, faster, more readable.  
**Effort:** 2 days for option (a), 1 day for option (b)  
**Recruiter signal:** A senior engineer will immediately ask "why LangGraph?" — have a real answer

---

### P3-G: ReAct Loop Is Not Machine-Parseable
**File:** `stocksense/orchestration/react_flow.py`  
**Severity:** [S3] Medium — "ReAct" without structured Thought/Action parsing is just prompted iteration  
**What's wrong:** True ReAct (Yao et al. 2022) requires the agent to output structured reasoning that the framework parses and routes. Currently the loop runs 10 iterations regardless of agent state, with no structured output like:
```xml
<Thought>I have price data but no sentiment yet. I should analyze headlines next.</Thought>
<Action>analyze_sentiment</Action>
<ActionInput>{"headlines": [...], "ticker": "AAPL"}</ActionInput>
```
**Fix:**
```python
class ReActStep(BaseModel):
    thought: str  # agent's reasoning
    action: Literal["analyze_sentiment", "fetch_price", "generate_skeptic", "finish"]
    action_input: dict
    observation: str | None = None  # filled after tool execution

# In the loop:
step: ReActStep = structured_llm.invoke(messages)
if step.action == "finish":
    break
result = await execute_tool(step.action, step.action_input)
step.observation = str(result)
```
**Effort:** 3 days  
**Why impressive:** Structured ReAct is how you build auditable, debuggable agents — each step is logged, queryable, replayable

---

### P3-H: Prompt Management — All Prompts Hardcoded, Zero Versioning
**Severity:** [S3] Medium — Can't A/B test prompts, can't roll back a bad prompt change  
**Where it hurts:** Bull/Bear/Skeptic/Synthesizer all have prompts embedded in f-strings inside methods. No central registry, no version tags, no diff visibility.  
**Fix:**
```python
# stocksense/core/prompts.py
PROMPTS = {
    "bull_analyst_v1": """You are a bullish equity analyst...""",
    "bear_analyst_v1": """You are a bearish equity analyst...""",
    "synthesizer_v2": """...""",  # v2 after improvement
}

def get_prompt(name: str, version: str = "latest") -> str:
    ...
```
Or use LangSmith Hub if going full production.  
**Effort:** 4 hours  
**Recruiter signal:** Production AI teams always have prompt management — it's where most quality improvements happen

---

### P3-I: Evidence Grader Formula Is Unjustified
**File:** `stocksense/agents/synthesizer.py:272-278`  
**Severity:** [S4] Low — `credibility = confidence * (1 - rebuttal_strength * 0.5)` is just invented math  
**What's wrong:** The `0.5` multiplier has no theoretical basis. Bayesian evidence weighting, debate scoring rubrics, or even simpler normalized averaging would be more defensible.  
**Fix:** Replace with explicit Bayesian update:
```python
def _update_credibility(self, prior: float, rebuttal_strength: float, evidence_quality: float) -> float:
    """
    Bayesian-inspired update: strong evidence + weak rebuttal = high posterior.
    prior: analyst's stated confidence (0-1)
    rebuttal_strength: how strong the counter-argument was (0-1)
    evidence_quality: how well data supports the claim (0-1)
    """
    # Posterior increases with evidence quality, decreases with rebuttal strength
    likelihood_ratio = evidence_quality / max(rebuttal_strength, 0.1)
    posterior = (prior * likelihood_ratio) / ((prior * likelihood_ratio) + (1 - prior))
    return round(posterior, 2)
```
**Effort:** 2 hours  

---

### P3-J: `_find_matching_rebuttal()` Uses 3-Word Substring Match
**File:** `stocksense/agents/synthesizer.py` (rebuttal matching function)  
**Severity:** [S4] Low — Naive substring match misses semantic equivalence, causes wrong rebuttal pairing  
**What's wrong:**
```python
# current (brittle)
for word in claim.split()[:3]:
    if word in rebuttal:
        return rebuttal
```
**Fix:** Use semantic similarity (already have Gemini — use embeddings):
```python
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

def _find_matching_rebuttal(self, claim: str, rebuttals: list[str]) -> str | None:
    claim_emb = embeddings.embed_query(claim)
    rebuttal_embs = embeddings.embed_documents(rebuttals)
    similarities = [cosine_similarity(claim_emb, r) for r in rebuttal_embs]
    best_idx = max(range(len(similarities)), key=lambda i: similarities[i])
    return rebuttals[best_idx] if similarities[best_idx] > 0.7 else None
```
**Effort:** 2 hours  
**Why impressive:** Semantic rebuttal matching is a real NLP problem — shows depth beyond basic LLM prompting

---

## PHASE 3-C — AI SYSTEMS ENGINEERING GAPS

> These are the gaps between "LLM app" and "AI system." Recruiters at AI-native companies look for exactly these.

### P3-K: No Evaluation Framework (No Evals = Flying Blind)
**Severity:** [S2] High — Cannot measure whether prompt changes improve or regress quality  
**What's missing:** There is no way to know if the agents are performing well. No benchmark, no golden test set, no regression tests against known-good outputs.  
**What to build:**
```python
# tests/evals/eval_runner.py
GOLDEN_SET = [
    {
        "ticker": "AAPL",
        "headlines": ["Apple beats Q4 earnings", "iPhone sales slow in China"],
        "expected": {
            "sentiment": "bullish_with_concerns",
            "confidence_range": (0.55, 0.75),
            "must_mention_risks": ["china", "iphone"],
        }
    },
    # 20-30 such cases
]

def run_evals(golden_set: list) -> EvalReport:
    for case in golden_set:
        result = run_analysis(case["ticker"], mock_data=case)
        score = evaluate_against_expected(result, case["expected"])
    return EvalReport(pass_rate=..., avg_confidence_error=..., risk_coverage=...)
```
Run evals before and after every prompt change. Gate deploys on eval regression.  
**Effort:** 3 days to build eval infrastructure  
**Recruiter signal:** This is what separates AI app developers from AI engineers — evals are the discipline

---

### P3-L: No Token Usage Tracking
**Severity:** [S3] Medium — No visibility into cost, latency, or per-analysis token consumption  
**What's missing:** Every `llm.invoke()` call burns tokens with no accounting. Can't optimize, can't bill users, can't cap runaway analyses.  
**Fix:**
```python
# stocksense/core/llm_client.py
from dataclasses import dataclass, field

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0  # Gemini Flash: $0.075/M input, $0.30/M output

class TrackedLLM:
    def __init__(self, llm, session_id: str):
        self.llm = llm
        self.session_id = session_id
        self.usage = TokenUsage()
    
    def invoke(self, messages, **kwargs):
        response = self.llm.invoke(messages, **kwargs)
        # Extract usage from response metadata
        if hasattr(response, "usage_metadata"):
            self.usage.prompt_tokens += response.usage_metadata.input_tokens
            self.usage.completion_tokens += response.usage_metadata.output_tokens
        return response
```
Surface per-analysis token cost in API response headers and in Supabase `analysis_cache`.  
**Effort:** 4 hours  

---

### P3-M: No Replay / Audit Trail
**Severity:** [S3] Medium — Cannot reproduce or debug a specific analysis run  
**What's missing:** Every analysis run is opaque. If an agent returns a bad verdict, you can't inspect what inputs it saw, what it reasoned, or which step went wrong.  
**What to build:**
```python
# Supabase table: analysis_traces
CREATE TABLE analysis_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    run_id TEXT NOT NULL,  -- correlation_id
    step_name TEXT,        -- "bull_analyst", "bear_analyst", "synthesizer"
    prompt_snapshot TEXT,  -- exact prompt sent
    response_snapshot TEXT,-- exact LLM response
    token_count INT,
    duration_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```
Log each agent step. Expose `/debug/trace/{run_id}` endpoint for inspection.  
**Effort:** 1 day  
**Recruiter signal:** Audit trails are required for any regulated use case (finance especially) — shows domain awareness

---

## PHASE 3-D — FINANCE/DOMAIN GAPS

> These matter for the product story. Current agents sound smart but miss fundamental finance concepts.

### P3-N: Price Data Collected But Never Used By Agents
**Severity:** [S2] High — yfinance fetches OHLCV data every analysis. Agents never see it.  
**Evidence:** `data_collectors.py` fetches price history. `react_flow.py:198` stores it in state. Agents' system prompts reference "fundamentals" but never "price_data" or "technicals."  
**What's missing:** Zero technical analysis. No trend detection, no volatility, no momentum signals.  
**Fix — Minimal Technical Analysis Layer:**
```python
# stocksense/core/technical_analysis.py
import pandas as pd

def compute_technical_signals(price_data: list[dict]) -> dict:
    """Compute basic TA signals from OHLCV data."""
    df = pd.DataFrame(price_data)
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["rsi"] = compute_rsi(df["close"], period=14)
    df["volatility_30d"] = df["close"].pct_change().rolling(30).std() * (252 ** 0.5)
    
    latest = df.iloc[-1]
    return {
        "trend": "uptrend" if latest["sma_20"] > latest["sma_50"] else "downtrend",
        "rsi": round(latest["rsi"], 1),
        "rsi_signal": "overbought" if latest["rsi"] > 70 else "oversold" if latest["rsi"] < 30 else "neutral",
        "annualized_volatility": round(latest["volatility_30d"], 3),
        "price_vs_sma20": round((df["close"].iloc[-1] / latest["sma_20"] - 1) * 100, 2),  # % above/below
    }
```
Inject `technical_signals` dict into Bull/Bear agent context alongside fundamentals.  
**Effort:** 4 hours  
**Recruiter signal:** Shows you understand what financial analysis actually requires — technical and fundamental, not just headlines

---

### P3-O: Sentiment Analysis Is Naive Lexical — No Magnitude, Credibility, or "Priced-In" Weighting
**File:** `stocksense/agents/analyzer.py`  
**Severity:** [S3] Medium — Current sentiment = positive/negative/neutral label + confidence score. That's it.  
**What's missing:**
1. **Magnitude**: "Apple earnings beat by $0.01" vs "Apple earnings beat by $1.50" — same sentiment label, wildly different signal
2. **Source credibility**: Reuters headline ≠ random blog post
3. **Priced-in assessment**: Strong positive earnings that were already priced in → no price movement
4. **Recency decay**: A week-old headline matters less than today's

**Fix — Enriched Sentiment Schema:**
```python
class HeadlineAnalysis(BaseModel):
    headline: str
    sentiment: Literal["bullish", "bearish", "neutral"]
    magnitude: float  # 0.0-1.0 — how significant is this news?
    credibility: float  # 0.0-1.0 — source quality
    likely_priced_in: bool  # was this expected by consensus?
    recency_weight: float  # 1.0 = today, 0.5 = 3 days ago
    
    @property
    def weighted_signal(self) -> float:
        base = 1.0 if self.sentiment == "bullish" else -1.0 if self.sentiment == "bearish" else 0.0
        surprise_factor = 1.0 if not self.likely_priced_in else 0.3
        return base * self.magnitude * self.credibility * self.recency_weight * surprise_factor
```
**Effort:** 1 day  

---

### P3-P: No Sector Context or Peer Comparison
**Severity:** [S3] Medium — Analyzing AAPL without reference to tech sector performance is weak analysis  
**What's missing:** An equity analyst always compares a stock to its peers. "AAPL down 5%" is very different news if the entire tech sector is down 8% vs. flat.  
**Fix — Sector Context Injection:**
```python
# stocksense/core/sector_context.py
SECTOR_ETFS = {
    "Technology": "XLK",
    "Healthcare": "XLV", 
    "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Discretionary": "XLY",
}

def get_sector_performance(ticker: str, period: str = "1mo") -> dict:
    """Get stock's sector ETF performance for relative comparison."""
    sector = get_sector_for_ticker(ticker)  # from yfinance .info
    etf = SECTOR_ETFS.get(sector, "SPY")
    
    stock_return = get_return(ticker, period)
    sector_return = get_return(etf, period)
    
    return {
        "sector": sector,
        "stock_return_1mo": stock_return,
        "sector_return_1mo": sector_return,
        "alpha": stock_return - sector_return,  # outperform/underperform
        "vs_sp500": stock_return - get_return("SPY", period),
    }
```
Inject `sector_context` into synthesizer prompt. Synthesizer should note whether the thesis is stock-specific or sector-wide.  
**Effort:** 3 hours  

---

## PHASE 4 — DEFERRED (Save for Later, Full Details Below)

> Too big for current sprint. Fully specced so future you can pick up immediately.

### P4-A: Multi-Ticker Portfolio Analysis
**What:** `/analyze/portfolio` endpoint accepts `["AAPL", "MSFT", "NVDA"]`, runs debate on each in parallel, synthesizes portfolio-level risk.  
**Architecture:**
- `asyncio.gather(*[run_debate_analysis(t) for t in tickers])` — already possible
- Add `PortfolioRisk` schema: correlation_risk, sector_concentration, overall_conviction
- Add portfolio Supabase table
**Effort:** 1 week  
**Recruiter signal:** Shows systems thinking — portfolio is the real use case

---

### P4-B: Agent Self-Evaluation Loop
**What:** After synthesis, a meta-agent evaluates the quality of the debate:  
- Did Bull and Bear actually disagree or did they converge?  
- Was the evidence used strong or speculative?  
- Confidence calibration score  
**Architecture:**
```
Debate → Synthesis → MetaEvaluator → confidence_adjustment
                                   → "This debate was low-quality because..."
```
**Effort:** 3 days  
**Recruiter signal:** Shows understanding of AI alignment — self-evaluation is how you make agents trustworthy

---

### P4-C: Webhook Alerts (Kill Criteria → Push Notifications)
**What:** When kill criteria trigger, send real-time alerts via webhooks (Slack, email)  
**Architecture:**
- `scheduler.py` detects trigger → POST to user's webhook URL
- Add `webhook_url` field to user profile in Supabase
- Add webhook validation (HMAC signature)
**Effort:** 2 days  

---

### P4-D: RAG on Earnings Transcripts
**What:** Feed quarterly earnings call transcripts as context to Bull/Bear agents  
**Architecture:**
- Use SEC EDGAR API (free) to fetch 10-Q/10-K filings
- Chunk + embed with `text-embedding-004`
- Store in Supabase pgvector
- Inject top-5 relevant chunks into agent context
**Why impressive:** RAG + agents is the production pattern. Shows you know both.  
**Effort:** 1 week  

---

### P4-E: Confidence Calibration Metrics
**What:** Track whether high-confidence predictions actually came true  
**Architecture:**
- After N days, fetch current price vs. predicted direction
- Calculate Brier score for confidence calibration
- Surface in `/calibration/{ticker}` endpoint
**Why impressive:** Shows statistical rigor — LLM confidence scores are usually uncalibrated  
**Effort:** 3 days  

---

## Execution Order (Sprint Plan)

```
Week 1 — Make it reliable (Phase 1 + quick wins):
  Day 1: P1-A (skeptic mock), P1-C (table name), P1-D (validation) — 2h total
  Day 2: P1-B (JSON parser utility) — 2h
  Day 3: P1-E (scheduler service role) — 1h
  Day 4: P2-A (retry logic with tenacity) — 3h
  Day 5: P2-C (structured output) → replaces P1-B after this (eliminate JSON parsing root cause)

Week 2 — Make it impressive (Phase 2 + Staff Engineer fixes):
  Day 1: P2-D (observability/correlation IDs) — 3h
  Day 2: P2-B (real information asymmetry) — 4h
  Day 3: P3-N (price data → technical analysis layer) — 4h  ← HIGH SIGNAL
  Day 4: P3-H (prompt versioning) + P3-I (evidence formula) — 6h
  Day 5: P3-K (eval framework — golden set + runner) — 1 day  ← HIRE signal

Week 3 — Elevate to AI systems grade:
  Day 1: P3-G (structured ReAct with Thought/Action parsing) — 3 days
  Day 2-3: P3-F (LangGraph real conditional routing or replace with asyncio) — 2 days
  Day 4: P3-L (token tracking) + P3-M (audit trail/replay) — 2 days
  Day 5: P3-O (enriched sentiment with magnitude/credibility) — 1 day

Week 4+ — Domain depth + architecture elevation:
  P3-J (semantic rebuttal matching with embeddings)
  P3-P (sector context + peer comparison)
  P3-B (LangGraph typed sub-states cleanup)
  P3-D (real streaming via astream_events)
  P3-E (test suite mocks)
  P3-A (agent memory — persistent priors)
  P3-C (evidence-grounded synthesis)
  P4-A through P4-E as time allows
```

---

## Architecture Score Projection

| Dimension | Now | After P1 | After P2 | After P3 (Full) |
|-----------|-----|----------|----------|-----------------|
| Structural Integrity | 2.5 | 3.0 | 4.0 | 4.5 |
| Scalability | 3.0 | 3.0 | 3.5 | 4.0 |
| Security | 3.0 | 3.5 | 3.5 | 4.0 |
| Performance | 3.0 | 3.0 | 3.5 | 4.0 |
| Enterprise Readiness | 2.5 | 3.5 | 4.0 | 4.5 |
| Operational Excellence | 3.0 | 3.5 | 4.0 | 4.5 |
| Data Architecture | 3.0 | 3.5 | 4.0 | 4.5 |
| **Overall** | **C+ 74%** | **B 81%** | **B+ 87%** | **A- 92%** |

> **A- requires:** Evals (P3-K), token tracking (P3-L), audit trail (P3-M), structured ReAct (P3-G), and real TA (P3-N). Not just polish — substantive engineering.

---

## What Recruiters/Engineers Will See

### After Phase 1 (bugs fixed):
- ReAct loop with genuine skeptic counter-analysis ✓
- Multi-agent adversarial debate with parallel execution ✓  
- Kill criteria monitoring with semantic matching ✓
- Investment thesis evolution tracking ✓

### After Phase 2 (improvements):
- Production LLM patterns (retry, structured output, correlation IDs) ✓
- True information asymmetry in debate (agents see different data) ✓
- Pydantic throughout — typed, validated, reliable ✓

### After Phase 3 (elevation):
- Agent memory across sessions ✓
- Real-time token streaming via LangGraph astream_events ✓
- Evidence-grounded synthesis ✓
- Clean typed state machine ✓

### After Phase 3-B and 3-C (Staff + AI Systems fixes):
- Structured ReAct loop: every agent step has Thought/Action/Observation — fully auditable ✓
- Eval framework: prompt changes gated by regression tests on golden set ✓
- Full token usage accounting per analysis run ✓
- Replay any past analysis by run ID ✓
- Prompt versioning — every deployed prompt is tagged and diffable ✓

### After Phase 3-D (Finance domain):
- Technical analysis layer: SMA/RSI/volatility injected into agent context ✓
- Enriched sentiment: magnitude + credibility + priced-in assessment ✓
- Sector context: stock alpha vs. sector ETF, not just absolute return ✓
- Semantic rebuttal matching via embeddings (not 3-word substring) ✓

### The story you tell (after Phase 3):
> "I built a multi-agent debate system where Bull and Bear analysts see intentionally asymmetric market data — each only gets the signals that favor their thesis. A Skeptic agent stress-tests the consensus using actual sentiment data, not mock inputs. Every agent step is structured ReAct: Thought → Action → Observation, fully logged and replayable by correlation ID. The system has an eval framework — I maintain a golden test set and gate every prompt change on regression. LLM outputs are Pydantic-validated, retried on transient failures, and traced. Users define investment theses with kill criteria; the system monitors them 24/7 against live price and news data, including technical signals and sector-relative performance."

That's a senior AI engineer talking. That's what gets you through the bar-raiser interview.
