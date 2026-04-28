# Stock Research Agent Idea

Date: 2026-04-28
Working name: StockSense Research Room

## Direct Answer

Yes, StockSense can absolutely do stock research.

It should not position itself as an autonomous trading bot or "buy/sell" recommender. That is legally risky, product-generic, and technically weak. The stronger version is:

> An AI analyst room that researches a stock like a serious junior analyst team: filings, earnings, fundamentals, peers, news, contradiction checks, scenario risks, and an evidence-backed memo.

The product can say:

- here is what changed
- here is what the company actually filed
- here is what management said
- here is what the numbers imply
- here is what the bull case needs to be true
- here is what the bear case is watching
- here is what evidence is missing

The product should not say:

- buy this now
- guaranteed upside
- autonomous trading
- price target with no model

## Research Signals

- AI finance platforms in 2026 are moving toward multi-document synthesis, sentence-level citations, workflow automation, and proprietary data integrations. Hebbia and AlphaSense are the clearest enterprise references. Source: https://www.hebbia.com/resources/financial-research-platforms
- Retail and independent investors are still cobbling together Finviz, SEC filings, ChatGPT/Claude/Perplexity, filing readers, and spreadsheets. Firecrawl surfaced Reddit threads from 2026 around stock research stacks, AI filing readers, and the gap between retail and institutional tools.
- SEC EDGAR APIs provide official company submissions and extracted XBRL facts, making free filing and fundamental research realistic. Source: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- FinAgentBench shows the hard part is not generic summarization. Finance research needs agentic retrieval: first identify the right document type, then find the right passage. Source: https://dl.acm.org/doi/10.1145/3768292.3770362
- Current benchmarks and market commentary suggest LLMs are better at extraction/retrieval than forecasting or investment judgment. That means StockSense should expose evidence and uncertainty instead of pretending to be a perfect stock picker.

## The Cool Product

Build a `Research Room` for any ticker.

The user types:

> Research AMD. I want to know if the AI server thesis is real or just narrative.

StockSense opens a multi-agent research room:

1. Filing Agent reads recent 10-K, 10-Q, and 8-K filings.
2. Fundamentals Agent extracts revenue, margin, cash flow, debt, valuation, and segment signals.
3. Earnings Agent reads transcript snippets or uploaded transcripts.
4. News Agent checks recent events and filters noise.
5. Peer Agent compares against NVDA, INTC, AVGO, ARM, or relevant peers.
6. Bull Agent builds the strongest case.
7. Bear Agent builds the strongest case.
8. Referee Agent rejects uncited claims.
9. Memo Agent produces the final research memo.

The user sees lanes, not a chat blob:

- `Company Snapshot`
- `What Changed`
- `Filing Receipts`
- `Key Metrics`
- `Bull Case`
- `Bear Case`
- `Open Questions`
- `Thesis Draft`
- `Evidence`

## Signature Feature

### "Find The Lie In The Narrative"

This is the feature that feels different.

Most stock tools summarize the company. StockSense should pressure-test the narrative.

For example:

> "AMD is winning AI server share."

The system asks:

- Did management say this directly?
- Do segment numbers support it?
- Are gross margins improving or weakening?
- Are customers named or vague?
- Do peers show the opposite trend?
- Are analysts/news repeating the same narrative without new evidence?
- What metric would prove it next quarter?

Output:

```text
Narrative: AMD is gaining AI server traction.
Verdict: Partially supported, not proven.
Supported by: management commentary and data center revenue growth.
Weakened by: margin pressure and limited named customer evidence.
Missing proof: shipment volume, AI accelerator revenue breakout, customer concentration.
Next watch item: data center growth and gross margin trend next quarter.
```

This is cooler than "stock summary" because it feels like the AI is doing real analytical work.

## MVP Features

### 1. Ticker Research Room

User enters ticker and research question.

Implementation:

- Add `/api/research-room/{ticker}/stream`.
- Use SSE like existing thesis checks.
- Return structured lane events.

Agents:

- Research Planner
- Filing Agent
- Fundamentals Agent
- News Agent
- Referee Agent
- Memo Agent

### 2. Filing Receipts

Every conclusion cites a filing, fact, transcript line, or data source.

Implementation:

- Add SEC EDGAR company submissions and company facts collector.
- Store evidence items with source URL, source type, excerpt, accession number, period, and filing type.

Agents:

- Filing Agent selects document type.
- Passage Agent extracts relevant chunk.
- Referee validates citations.

### 3. Narrative Truth Test

User writes or selects a market narrative. StockSense tests it against filings, fundamentals, peers, and news.

Implementation:

- Add `narrative_tests` table.
- Store narrative, claims, supporting evidence, contradicting evidence, missing proof, and next watch item.

Agents:

- Narrative Decomposer
- Evidence Hunter
- Skeptic
- Referee

### 4. Peer Contrast

For any stock, show why the thesis is stronger or weaker than peers.

Implementation:

- Start with manually selected peers or yfinance sector peers.
- Compare revenue growth, margins, valuation, price performance, and filing commentary.

Agents:

- Peer Selector
- Peer Analyst

### 5. Thesis Draft Button

After research, click `Draft thesis`.

Output:

- thesis summary
- 3-5 claims
- kill criteria
- forecast questions
- evidence needed

Implementation:

- Connect Research Room output to existing thesis creation flow.

Agents:

- Thesis Compiler

### 6. Contradiction Radar

Find where story and numbers diverge.

Examples:

- management says demand is strong, but inventory rises
- revenue grows, but margins compress
- company says AI is strategic, but capex/R&D does not move
- news is bullish, but filings add risk language

Implementation:

- Deterministic metric checks plus LLM summary.
- Store contradiction cards as evidence items.

Agents:

- Fundamentals Agent
- Filing Agent
- Contradiction Agent

## Buildable 2-3 Week Version

### Fully Build

- Research Room streaming endpoint.
- SEC submissions/facts collector.
- Research lane UI.
- Narrative Truth Test.
- Evidence receipts.
- Draft Thesis handoff.

### Fake Or Seed

- Earnings transcripts if no transcript API is available.
- Peer list quality for first version.
- Advanced estimate data.
- Options-implied expectations.

### Do Not Build Yet

- brokerage execution
- portfolio optimization
- real-time trading bot
- paid data integrations
- autonomous buy/sell decisions

## Technical Shape

Backend:

- FastAPI
- Pydantic structured outputs
- asyncio parallel collectors
- Supabase persistence
- SSE streaming

Data sources:

- SEC EDGAR APIs for filings and XBRL facts
- yfinance for basic market/fundamental data
- NewsAPI or web search for current news
- user-uploaded transcript text for demo
- later: Financial Modeling Prep, Polygon, Tiingo, or Fiscal.ai-style transcript/fundamental APIs

Tables:

```sql
research_room_runs
research_room_steps
research_evidence_items
narrative_tests
narrative_claims
peer_comparisons
research_memos
```

## Demo

Ticker: `AMD`

Prompt:

> Is AMD's AI server thesis real, or is the market over-narrating it?

Demo flow:

1. Open `Research Room`.
2. Type `AMD` and the question.
3. Lanes stream:
   - Filing Agent
   - Fundamentals Agent
   - News Agent
   - Peer Agent
   - Bull/Bear
   - Referee
4. Show `Narrative Truth Test`.
5. Open an evidence receipt from a filing or metric.
6. Show contradiction card.
7. Click `Draft thesis`.
8. Save it into Conviction Desk for monitoring.

This gives StockSense a clear stock-research workflow and connects naturally into the existing thesis system.

## Recommendation

Build `Research Room` before the more abstract `Conviction World Model`.

Reason:

- It answers the immediate "can we research stocks?" question.
- It uses the existing ReAct, debate, thesis, evidence, and streaming foundations.
- It is demoable in 2-3 weeks.
- It creates the raw material for stronger thesis monitoring.

Positioning:

> StockSense does not pick stocks. It builds evidence-backed stock research rooms that test whether a market narrative is actually supported.
