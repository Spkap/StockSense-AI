# StockSense Flow Architecture

This is the simplest walkthrough version of the system. It shows the main user journey, the core analysis pipeline, and how saved theses and alerts connect back to the analysis.

```mermaid
flowchart TD
    A[Client]
    A -->|select ticker + start analysis| B[React Frontend]
    B -->|GET analyze ticker stream| C[FastAPI SSE Endpoint]
    C -->|validate ticker + rate limit| D[API Gateway Logic]
    D -->|check existing result| E[Supabase Analysis Cache]
    D -->|if no cache or force refresh| F[ReAct Analysis Flow]
    F -->|fetch headlines| G[NewsAPI]
    F -->|fetch price history + fundamentals| H[yfinance]
    F -->|analyze sentiment + critique| I[Gemini via LangChain]
    F -->|save completed analysis| E
    E -->|stream progress + final result| C
    C -->|SSE events| B
    B -->|render summary, charts, sentiment, skeptic view| A

    A -->|open Debate Lab| J[Debate UI]
    J -->|GET debate ticker stream| K[Debate Endpoint]
    K -->|run Bull and Bear agents| L[Bull Analyst]
    K -->|run Bull and Bear agents| M[Bear Analyst]
    L -->|draft + rebuttal| N[Synthesizer]
    M -->|draft + rebuttal| N
    N -->|probability-weighted verdict| J

    A -->|sign in| O[Supabase Auth]
    O -->|Bearer token| B
    B -->|positions, theses, alerts API| P[Authenticated User API]
    P -->|read/write user data| Q[Supabase User Tables]
    E -->|latest analysis| R[Kill Criteria Monitor]
    Q -->|active theses + criteria| R
    R -->|create alerts when thesis breaks| Q
    Q -->|positions, theses, alerts| B
```

## Walkthrough

1. The client starts from the React frontend and requests a stock analysis.
2. FastAPI receives the streaming request, validates the ticker, and checks rate limits.
3. The backend first checks whether a cached analysis already exists in Supabase.
4. If cached data is available, it returns quickly. If not, the ReAct flow runs.
5. The ReAct flow gathers market evidence from NewsAPI and yfinance, then uses Gemini to interpret sentiment and generate the final analysis.
6. That analysis is saved back into Supabase and streamed to the frontend over SSE.
7. If the user opens Debate Lab, a separate Bull vs Bear flow runs and the Synthesizer produces the final verdict.
8. If the user is signed in, the frontend can also read and write positions, theses, and kill alerts through authenticated API routes.
9. New analyses are checked against saved thesis kill criteria, and alerts are created when a thesis is invalidated.