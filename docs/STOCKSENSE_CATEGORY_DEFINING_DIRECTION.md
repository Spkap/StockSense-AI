# StockSense Category-Defining Direction

Date: 2026-04-28
Working name: StockSense Conviction World Model

## Executive Break

The current direction is good, but still too normal.

`Conviction Desk` is a serious thesis monitor. It checks evidence, updates claims, and gives the user a more trustworthy research workflow.

That is not enough to be category-defining.

The step-change is this:

> StockSense should become a market conviction simulator: a system that turns a user's investment belief into a living causal model, continuously stress-tests it against evidence, forecasts what would have to happen next, and tracks whether the user is becoming better calibrated over time.

This moves the product from "AI research assistant" to "belief debugging infrastructure for investors."

The product stops asking:

> What does the AI think about NVDA?

It starts asking:

> What future would make my thesis wrong, what evidence would reveal it early, and how calibrated am I becoming as an investor?

That is a much sharper product category.

## Research Signals

The research pass used Firecrawl-led MCP search, GitHub MCP search, and targeted current web lookup. The important signals were not "more agents." They were state, simulation, forecasting, retrieval accuracy, and calibration.

- Production agent writing in 2026 keeps converging on typed tools, explicit state machines, layered memory, trace-level observability, trajectory evals, and policy gates. Source: https://andriifurmanets.com/blogs/ai-agents-2026-practical-architecture-tools-memory-evals-guardrails
- Agent observability has moved from logs to decision-level traces, session replay, graph views, eval promotion, and OpenTelemetry/OpenInference style portability. Source: https://arize.com/blog/best-ai-observability-tools-for-autonomous-agents-in-2026/
- Finance AI products like Hebbia, AlphaSense, Rogo, and Verity mostly compete on document search, multi-document synthesis, proprietary content, citations, and workflow automation. They do not center the individual investor's living belief model. Sources: https://www.hebbia.com/resources/financial-research-platforms and https://www.alpha-sense.com/resources/research-articles/ai-tools-for-financial-research/
- FinAgentBench shows that finance retrieval is not solved by generic RAG. Document-type selection and chunk-level evidence selection are separate hard problems. Chunk ranking remains much harder than document ranking. Source: https://dl.acm.org/doi/full/10.1145/3768292.3770362
- 2025-2026 finance-agent research is exploring multi-agent investment management, portfolio construction, and simulated markets, but open reviews still flag weak deployment-risk handling, lack of theory, and limited interpretability. Source: https://openreview.net/forum?id=NNpE9iiPNR
- Prediction markets are becoming a live testbed for AI forecasting, but direct AI trading is still unreliable; recent public coverage reports frontier models losing money in realistic prediction-market tests. Source: https://finance.yahoo.com/markets/crypto/articles/ai-traders-already-testing-prediction-120637507.html
- Forecasting platforms are shifting away from gambling toward calibration, track records, hybrid human-AI judgment, and future-event evaluation. Source: https://www.forbes.com/sites/charliefink/2026/03/24/ai-turns-polls-prediction-markets-into-a-new-battleground/
- World-model discussion in 2026 is less about pretty generation and more about action-conditioned simulation, counterfactual rollouts, closed-loop evaluation, and controllability. Source: https://medium.com/@graison/beyond-the-video-hype-why-world-models-feel-different-in-2026-88486a295fe3
- GitHub MCP search surfaced active open-source prediction-market and forecasting-agent work, including `gnosis/prediction-market-agent`, `rapturt9/agent-forecaster`, and Kalshi bot implementations. The public builder energy is around autonomous forecasting loops, but the product gap is trust, calibration, and decision UX.
- Firecrawl search also surfaced X/Twitter discussion patterns around "everyone has AI but no one has execution" and finance stacks still being ChatGPT/Claude/Perplexity plus scattered research tools. The actionable signal is that differentiation comes from workflow ownership, not model wrapping.

## Why The Current System Is Still Basic

The current system is impressive for a project, but not yet surprising for a product.

1. It monitors evidence, but does not model causality.
   - It can say "claim weakened."
   - It cannot say "the margin claim now depends mostly on memory prices and Blackwell ramp yields."

2. It updates conviction, but does not expose future paths.
   - It can say "monitor."
   - It cannot show three futures where the thesis survives, breaks, or becomes crowded.

3. It uses agents to analyze, but not to simulate.
   - Bull/bear/debate agents are now common.
   - A world model of the thesis is not common.

4. It cites evidence, but does not grade the user's forecasting skill.
   - It can say whether the thesis changed.
   - It cannot say whether the user is systematically overconfident on margins, TAM, management guidance, or macro sensitivity.

5. It has run traces, but not a "belief ledger."
   - CTOs will like the infrastructure.
   - Founders and product leaders will remember the product if it makes their own thinking visible.

6. It still resembles financial AI research platforms.
   - Hebbia and AlphaSense already own "search across documents and synthesize."
   - StockSense should own "turn my belief into a falsifiable future model."

## New Product Category

### Category

Conviction intelligence.

### Product

An evidence-backed world model for investment beliefs.

### User Promise

StockSense does not tell you what to buy.

It tells you what you believe, what would make you wrong, what changed today, what future paths are plausible, and whether your judgment is improving.

### Sharp User

The first beachhead is not "retail investors."

The first beachhead is:

- self-directed investors with 5-30 serious theses
- founder/operator/investor types who think in narratives and catalysts
- analyst candidates who want a repeatable research process
- small fund or angel-style users who cannot afford institutional tools

They do not need another summary. They need a system that makes their reasoning inspectable.

## The Unexpected Paradigm

### The Conviction World Model

Each thesis becomes a small, explicit, editable world model.

It contains:

- claims
- causal drivers
- evidence sources
- forecast questions
- trigger thresholds
- scenario paths
- current probabilities
- user confidence
- agent disagreement
- time windows
- calibration history

This is not a full market simulator. That would be fake.

It is a bounded thesis simulator: a structured environment where agents can ask "if this driver changes, which claims move, what evidence would detect it, and what action should the user consider?"

The new interaction is not chat.

It is a "what-if cockpit" for belief:

- user drags a scenario knob
- agents recalculate which claims become fragile
- evidence receipts show what supports each path
- forecast cards turn vague beliefs into testable questions
- the user's calibration score updates over time

This feels unfair because most tools summarize the past. StockSense helps the user rehearse the future.

## High-Leverage Features

### 1. Falsifiability Compiler

What it unlocks:

Turns any messy thesis into a set of testable claims, forecast questions, and invalidation rules.

Example:

> NVDA inference demand is underestimated.

Becomes:

- `Q1`: Will data center revenue growth stay above X percent next quarter?
- `Q2`: Will gross margin remain above 70 percent through Blackwell ramp?
- `Q3`: Will hyperscaler capex commentary remain expansionary?
- `Kill`: Two consecutive quarters of decelerating data center revenue plus margin compression below threshold.

Why it is powerful:

Most users cannot write falsifiable theses. This makes the product feel like it upgrades their thinking immediately.

How agents enable it:

The Thesis Compiler agent decomposes narrative into claim nodes, observable metrics, time windows, and evidence requirements. A deterministic validator rejects claims with no observable proxy.

Implementation:

- Add `forecast_questions` table.
- Add `claim_observables` table.
- Extend thesis creation flow with `Compile thesis`.
- Use structured LLM output plus validation that every claim has at least one observable.

Buildability:

Fully build in 2-3 weeks.

### 2. Scenario Simulator

What it unlocks:

The user can ask:

- What future breaks this thesis?
- What future makes this a high-conviction thesis?
- What changes first if the bear case is right?

Why it is powerful:

This is the step-change. The product becomes an imagination engine for investment judgment, not a reporting tool.

How agents enable it:

Specialist agents build bull/base/bear trajectories using only the claim graph and evidence receipts. A Scenario Referee rejects unsupported causal leaps.

Implementation:

- Add `scenario_runs`, `scenario_nodes`, and `scenario_edges`.
- Store paths as ordered driver changes, claim impacts, evidence requirements, and forecast probabilities.
- UI: three scenario columns with driver chips and probability sliders.

Buildability:

Core version is buildable. Do not claim predictive accuracy. Present as "decision rehearsal" and "evidence-backed scenario generation."

### 3. Belief Ledger

What it unlocks:

Tracks the user's predictions and shows where they are calibrated or overconfident.

Why it is powerful:

This creates a personal compounding loop. The product becomes more valuable the longer it is used.

How agents enable it:

The Calibration Judge compares resolved forecast questions against prior confidence, then summarizes blind spots:

- too optimistic on management guidance
- too slow to update on margins
- strong on regulatory risk
- weak on valuation compression

Implementation:

- Add `belief_forecasts`, `forecast_resolutions`, and `calibration_scores`.
- Store Brier-style scores where outcomes are binary.
- Use LLM only for human-readable pattern summary, not scoring.

Buildability:

Fully build for manually resolved forecast cards. Automated resolution can come later.

### 4. Anti-Consensus Hunter

What it unlocks:

Finds what the user's thesis is not thinking about.

Examples:

- A supplier bottleneck.
- A related company warning.
- A change in customer capex commentary.
- A regulatory clause buried in filings.
- A market-implied probability that conflicts with the user's confidence.

Why it is powerful:

The best investor tool is not the one that agrees with the user. It is the one that finds the silent assumption.

How agents enable it:

An Anti-Consensus agent searches adjacent evidence spaces and asks "what would a smart skeptic monitor that is missing from the claim graph?"

Implementation:

- Add `blind_spot_findings`.
- Use existing evidence collectors plus targeted query generation.
- Show findings as `Missing from thesis` cards, not as generic alerts.

Buildability:

Build a high-quality demo version using SEC/news/price/fundamentals plus user-provided transcript snippets.

### 5. Evidence Time Machine

What it unlocks:

The user can backtest their thesis process:

> If I had held this belief on January 1, what evidence would StockSense have surfaced by each key date, and when should I have revised?

Why it is powerful:

This is a killer demo and an actual product differentiator. It makes the user's reasoning process auditable over time.

How agents enable it:

The Counterfactual Backtester reconstructs a historical evidence timeline, runs the same claim graph at checkpoints, and produces a "missed update" report.

Implementation:

- Add `backtest_runs`.
- Start with seeded historical evidence JSON for 1-2 demo tickers.
- Reuse the thesis check orchestrator with `as_of_date`.
- UI: timeline with "evidence available then" versus "actual outcome later."

Buildability:

Fake the data ingestion for demo, fully build the orchestration and UI.

### 6. Agent Investment Committee

What it unlocks:

A user's thesis is reviewed by a small committee of agent personas with different mandates:

- Fundamental Analyst
- Skeptic
- Macro/Rates Analyst
- Technical/Flow Analyst
- Customer/Industry Analyst
- Risk Officer
- Evidence Referee

Why it is powerful:

This gives multi-agent work a product reason. It is not "agents chatting." It is a structured IC meeting with votes, dissent, and receipts.

How agents enable it:

Each persona receives scoped tools and a narrow decision rubric. The committee produces votes, dissent reasons, and "what would change my vote" triggers.

Implementation:

- Add `committee_runs` and `agent_votes`.
- Use 5-7 agents, not 100.
- Persist each vote with evidence refs and confidence.
- Show a vote board, not chat transcripts.

Buildability:

Buildable if scoped to Deep Review. Keep normal checks fast.

### 7. Forecast Market Mirror

What it unlocks:

Compares the user's implied probabilities against public market expectations and prediction-style signals where available.

Examples:

- options-implied move around earnings
- analyst estimate revision direction
- prediction-market probability for macro or regulatory events
- sector ETF relative move

Why it is powerful:

This exposes hidden disagreement: "you are 80 percent confident, but market-implied evidence behaves like 55 percent."

How agents enable it:

The Forecast Mirror agent maps thesis claims to comparable external expectation proxies and explains mismatch.

Implementation:

- Start without live prediction-market trading APIs.
- Use options/implied move if available, analyst estimate deltas if available, or seeded external forecast data for demo.
- Store `external_expectation_signals`.

Buildability:

Partially fake. Fully build the UI and comparison engine; seed external data for demo.

### 8. Research Bounties

What it unlocks:

The user can create a background job:

> Find the strongest evidence that would disprove my margin claim.

The job returns later with receipts, not a chat reply.

Why it is powerful:

This turns agents into workers with durable tasks and visible output. It also maps to real investor workflow: "go investigate this."

How agents enable it:

A Bounty Planner decomposes the task, assigns collectors, runs a bounded search, and hands results to an Evidence Referee.

Implementation:

- Add `research_bounties`.
- States: queued, collecting, reviewing, needs_user_input, completed, failed.
- UI: inbox lane for active bounties.
- Use FastAPI background task first; move to durable queue later.

Buildability:

Fully build for bounded sources.

### 9. Thesis Mutation Alerts

What it unlocks:

Detects when the user's thesis has quietly changed.

Example:

The user started with "margin durability" but over time keeps accepting weaker margin evidence and shifting emphasis to TAM expansion. StockSense flags:

> Your thesis has mutated from margin durability to long-term TAM optionality. Confirm or split thesis.

Why it is powerful:

Investors often move goalposts. This product catches it.

How agents enable it:

The Thesis Historian compares claim graph versions, corrections, dismissals, and forecast updates, then identifies narrative drift.

Implementation:

- Use existing thesis history.
- Add `thesis_mutations`.
- LLM summarizes drift; deterministic diff identifies changed/deleted claims.

Buildability:

Fully buildable because existing thesis history already exists.

## System Upgrade

### New System Shape

StockSense should be organized around five run types:

1. `CHECK`
   - Fast evidence update against existing claims.

2. `SIMULATE`
   - Build scenario paths and claim impacts.

3. `FORECAST`
   - Create or update forecast questions and probabilities.

4. `BACKTEST`
   - Replay historical evidence as of prior dates.

5. `BOUNTY`
   - Long-running background research task.

The current `thesis_check` pipeline becomes the foundation, not the whole product.

### Agents To Add

#### Thesis Compiler

Input: user thesis text.

Output: claims, observables, forecast questions, kill criteria.

Uses: LLM structured output plus deterministic validation.

#### Causal Graph Builder

Input: claim graph and evidence bundle.

Output: driver nodes and causal links.

Uses: LLM for graph proposal, deterministic schema validation.

#### Scenario Simulator

Input: causal graph, evidence, user-chosen scenario.

Output: bull/base/bear paths, claim impacts, early-warning signals.

Uses: LLM rollouts constrained to explicit drivers.

#### Forecast Compiler

Input: claim and observable.

Output: binary or range forecast question, resolution criteria, due date.

Uses: LLM for phrasing, deterministic validation for measurability.

#### Calibration Judge

Input: resolved forecasts.

Output: Brier-style scores and pattern summary.

Uses: deterministic scoring plus LLM narrative.

#### Anti-Consensus Hunter

Input: thesis graph and current evidence.

Output: missing drivers, adjacent risks, outside-view checks.

Uses: targeted query generation and evidence search.

#### Counterfactual Backtester

Input: thesis, historical checkpoints, as-of evidence.

Output: what should have changed when.

Uses: existing thesis evaluator with an `as_of_date` state.

#### Committee Chair

Input: specialist agent votes.

Output: dissent map and final decision memo.

Uses: aggregation, not free-form debate.

### Agents To Remove Or Downgrade

- Downgrade the generic ReAct ticker agent to research intake only.
- Do not make Bull/Bear agents default. They are committee participants in Deep Review.
- Remove any agent that produces uncited narrative.
- Avoid "autonomous trading agent" framing. It creates regulatory and trust problems and is not needed for product wow.

### Orchestration

Do not jump straight to a heavy framework.

Core 2-3 week version:

- FastAPI run controller.
- `run_type` enum.
- Pydantic state objects.
- Supabase persistence for every run state.
- SSE streaming for UI lanes.
- `asyncio.gather` for bounded parallel collectors.
- deterministic reducers for state transitions.

Later:

- LangGraph if resume/branching becomes complex.
- Temporal only when background bounties and scheduled monitors must survive crashes and long waits.

### Memory Upgrade

Current memory stores prior runs, corrections, alerts, and cached analysis. That is useful but incomplete.

Add five memory ledgers:

1. Belief Ledger
   - forecasts, probabilities, resolutions, calibration.

2. Causal Ledger
   - claim-driver graph versions.

3. Source Trust Ledger
   - source freshness, source failures, user dismissals, stale sources.

4. Agent Vote Ledger
   - committee persona votes and dissent over time.

5. Mutation Ledger
   - thesis drift, deleted claims, changed kill criteria, shifting rationale.

This makes memory product-native, not just context for prompts.

## Technical Data Model

Minimum new tables:

```sql
thesis_claims
claim_observables
forecast_questions
forecast_resolutions
calibration_scores
causal_driver_nodes
causal_driver_edges
scenario_runs
scenario_paths
agent_votes
research_bounties
backtest_runs
thesis_mutations
external_expectation_signals
```

Key design rule:

The LLM proposes. The database remembers. Deterministic validators decide whether a result is admissible.

## UX Model

### Main Screen

Rename the default workspace from `Thesis Inbox` to `Conviction Map`.

The user sees:

- theses needing review
- active forecasts nearing resolution
- scenarios that changed
- bounties completed
- calibration score trend
- thesis mutations

### Thesis Detail

Tabs:

1. `Now`
   - current conviction diff, alerts, evidence.

2. `World`
   - causal graph and scenario paths.

3. `Forecasts`
   - active forecast cards and due dates.

4. `Committee`
   - agent votes and dissent.

5. `History`
   - belief ledger, calibration, mutations, backtests.

### Core Interaction

The signature interaction should be:

1. User opens thesis.
2. Clicks `What Would Break This?`
3. StockSense generates three break paths:
   - margin compression path
   - demand deceleration path
   - market multiple compression path
4. User clicks one path.
5. Agents show:
   - which claims fail first
   - which evidence would detect it
   - what forecast question to track
   - what source is missing
6. User adds the path to monitoring.

This is the demo moment.

## What To Build In 2-3 Weeks

### Fully Build

1. Falsifiability Compiler
   - claim graph, observables, forecast questions.

2. Scenario Simulator Lite
   - three scenario paths with evidence refs and claim impacts.

3. Belief Ledger Lite
   - manual forecast resolution and calibration scoring.

4. Agent IC Lite
   - 5 persona votes with evidence refs in Deep Review.

5. `What Would Break This?` UX
   - the signature interaction.

6. Thesis Mutation Detector
   - deterministic version diff plus LLM summary.

### Fake Or Seed

1. Historical evidence for Evidence Time Machine.
   - Seed one ticker with JSON snapshots.

2. External forecast signals.
   - Seed prediction-market or options-implied examples.

3. Paid transcripts and premium research.
   - Use user-uploaded/demo transcripts.

4. True causal forecasting accuracy.
   - Do not pretend to predict stock returns.

5. Hundreds of agents.
   - Use 5-7 high-quality agents.

### Avoid

- brokerage execution
- direct trading recommendations
- unbounded autonomous web browsing
- generic chat as the main UI
- "AI hedge fund" claims
- unsupported price targets

## 2-3 Week Solo Execution Plan

### Week 1: Conviction World Model Core

- Add tables for claims, observables, forecasts, scenario runs, and agent votes.
- Implement Thesis Compiler endpoint.
- Implement claim/observable validators.
- Add `World` and `Forecasts` tabs in thesis detail.
- Show editable claim graph and generated forecast cards.

### Week 2: Scenario And Committee

- Implement `SIMULATE` run type.
- Add Scenario Simulator Lite.
- Add Agent IC Lite with 5 personas.
- Persist persona votes and evidence refs.
- Add `What Would Break This?` button and scenario path UI.

### Week 3: Belief Ledger And Demo Layer

- Add manual forecast resolution.
- Add calibration scoring.
- Add thesis mutation detector.
- Add seeded Evidence Time Machine for one demo ticker.
- Polish demo data, UI copy, and run inspector traces.

## Killer Demo

Ticker: NVDA.

Thesis:

> NVDA remains mispriced because inference demand is underestimated, hyperscaler capex will stay elevated, and margins will remain above 70 percent despite Blackwell ramp costs.

Demo:

1. Open `Conviction Map`.
   - NVDA shows active forecasts and one fragile driver.

2. Open thesis.
   - Show causal graph: inference demand, hyperscaler capex, Blackwell ramp, gross margin, export controls, valuation multiple.

3. Click `What Would Break This?`
   - Three scenario paths appear.

4. Open `Margin Compression Path`.
   - It shows early-warning signals, evidence needed, claim impacts, and forecast cards.

5. Run Agent IC.
   - Fundamental agent votes hold.
   - Risk agent votes revise.
   - Evidence Referee rejects one uncited argument.
   - Committee Chair summarizes dissent.

6. Resolve a forecast from seeded historical evidence.
   - Calibration score updates.

7. Open Evidence Time Machine.
   - It shows that a margin warning should have triggered review two runs earlier.

8. Open Run Inspector.
   - Show run type, state transitions, evidence refs, agent votes, validation failures, latency, and prompt versions.

What impresses:

- Product: it makes a user's belief inspectable and improvable.
- AI: agents simulate futures, not just summarize documents.
- Engineering: stateful run types, persisted ledgers, validation, traces.
- Judgment: avoids fake trading claims and centers calibration.

## Final Positioning

Do not position StockSense as:

> AI stock research assistant.

Do not position it as:

> Autonomous trading agent.

Position it as:

> The conviction world model for serious investors.

One-line:

> StockSense turns investment theses into living world models that forecast, stress-test, and debug your beliefs as new evidence arrives.

Short demo pitch:

> Most finance AI summarizes what happened. StockSense models what would have to happen for you to be wrong, tracks the evidence that would reveal it, and measures whether your judgment is getting better.

## Product Standard

A new feature belongs only if it improves at least one of these:

1. Falsifiability
   - Can the belief be tested?

2. Foresight
   - Can the user rehearse plausible futures?

3. Evidence
   - Can every claim be inspected?

4. Calibration
   - Does the user get better over time?

5. Memory
   - Does the system remember what the user believed before?

If a feature does not improve these, it is probably just another finance chatbot feature.
