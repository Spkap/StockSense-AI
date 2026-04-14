# StockSense — Engineering Priority Master Document

> **Last updated:** 2026-04-15  
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
Week 1 — Make it reliable (Phase 1 + 2A/2B/2C):
  Day 1: P1-A (skeptic mock), P1-C (table name), P1-D (validation) — 2h total
  Day 2: P1-B (JSON parser utility) — 2h
  Day 3: P1-E (scheduler service role) — 1h
  Day 4: P2-A (retry logic with tenacity) — 3h
  Day 5: P2-C (structured output) — 6h

Week 2 — Make it impressive (Phase 2D-2E + Phase 3):
  Day 1: P2-D (observability/correlation IDs) — 3h
  Day 2: P2-B (real information asymmetry) — 4h
  Day 3: P3-B (LangGraph state cleanup) — 1 day
  Day 4: P3-D (real streaming) — 2 days
  Day 5: P3-E (test suite mocks) — 1 day

Week 3+ — Deferred (P4-A through P4-E as time allows)
```

---

## Architecture Score After Phase 1+2

| Dimension | Before | After Phase 1 | After Phase 2 |
|-----------|--------|---------------|---------------|
| Structural Integrity | 2.5 | 3.0 | 4.0 |
| Scalability | 3.0 | 3.0 | 3.5 |
| Security | 3.0 | 3.5 | 3.5 |
| Performance | 3.0 | 3.0 | 3.5 |
| Enterprise Readiness | 2.5 | 3.5 | 4.0 |
| Operational Excellence | 3.0 | 3.5 | 4.0 |
| Data Architecture | 3.0 | 3.5 | 4.0 |
| **Overall** | **C+ 74%** | **B 81%** | **B+ 87%** |

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

### The story you tell:
> "I built a multi-agent debate system where a Bull and Bear analyst argue using different subsets of market data. A Synthesizer grades evidence quality and produces probability-weighted verdicts. Users define investment theses with kill criteria — the system monitors them 24/7 and alerts when the thesis is invalidated. Every LLM output is Pydantic-validated, retried on failure, and traced with correlation IDs."

That's a B+ engineer talking. After Phase 3, it's A-level.
