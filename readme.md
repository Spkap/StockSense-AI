# StockSense Agent

**AI-Powered Autonomous Stock Market Research (ReAct Pattern)**

StockSense is an autonomous stock analysis system implementing the **ReAct (Reasoning + Action)** pattern: iterative reasoning, selective tool invocation, and adaptive summarization. The agent collects real market data (news + historical prices), performs LLM-based sentiment analysis, and produces a structured summary.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6+-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.x-blue.svg)](https://python.langchain.com/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

## Overview

StockSense demonstrates an applied AI agent architecture using LangGraph + LangChain tools. It combines recent news headlines (NewsAPI) and historical market data (Yahoo Finance via yfinance) with Gemini-based sentiment analysis (Gemini 2.0 Flash Lite) to produce a lightweight research snapshot. The agent maintains internal state (messages, tool usage, reasoning steps) across iterations until completion criteria are met or a max-iteration limit is reached.

### Key Characteristics

- **ReAct Agent**: Iterative reasoning cycle with tool calls (news, price data, sentiment, persistence)
- **Backend API**: FastAPI service exposing analysis endpoints and cached result retrieval
- **Frontend App**: React + TypeScript modern dashboard with thesis tracking
- **LLM Integration**: Google Gemini 2.0 Flash Lite (chat + text variants) via `langchain-google-genai`
- **Stateful Orchestration**: LangGraph `StateGraph` with conditional continuation
- **User Belief System**: Investment thesis tracking with Supabase authentication

## Architecture

### Technology Stack

| Layer            | Technology                               | Purpose                             |
| ---------------- | ---------------------------------------- | ----------------------------------- |
| **LLM / AI**     | Google Gemini 2.0 Flash Lite (LangChain) | Sentiment & reasoning               |
| **Agent Graph**  | LangGraph (StateGraph)                   | Iterative reasoning & tool routing  |
| **Tool Layer**   | LangChain `@tool` functions              | News, price, sentiment, persistence |
| **Backend**      | FastAPI + Uvicorn                        | REST API (analysis, cache, health)  |
| **Frontend**     | React + TypeScript + Vite                | Modern interactive dashboard        |
| **Persistence**  | SQLite + Supabase                        | Cached analyses + User data         |
| **Data Sources** | NewsAPI + yfinance (Yahoo Finance data)  | Headlines + OHLCV price history     |
| **Config / Env** | `python-dotenv`                          | API key management                  |

### ReAct Agent Workflow

```mermaid
graph TD
    A[Stock Ticker Input] --> B[Initialize ReAct Agent]
    B --> C[Reasoning Phase]
    C --> D{Analysis Complete?}
    D -->|No| E[Select Appropriate Tool]
    E --> F[Execute Action]
    F --> G[Observe Results]
    G --> C
    D -->|Yes| H[Generate Summary]
    H --> I[Save Results]
    I --> J[Return Analysis]
```

### Core Components

```
StockSense-Agent/
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/     # UI components (ResultsTabs, ThesisEditor, etc.)
│   │   ├── pages/          # Page components (ThesesPage)
│   │   ├── api/            # API hooks and clients
│   │   ├── context/        # React contexts (Auth, Sidebar, Theme)
│   │   └── types/          # TypeScript type definitions
│   └── package.json
├── stocksense/             # Python backend
│   ├── main.py             # FastAPI server (analysis + cache + auth endpoints)
│   ├── react_agent.py      # LangGraph ReAct agent implementation
│   ├── data_collectors.py  # NewsAPI + yfinance helper functions
│   ├── analyzer.py         # Sentiment analysis (Gemini prompt)
│   ├── skeptic.py          # Skeptic analysis (contrarian view)
│   ├── database.py         # SQLite caching helpers
│   ├── supabase_client.py  # Supabase client for user data
│   ├── auth_routes.py      # User authentication & thesis APIs
│   └── config.py           # Configuration & LLM/chat factories
├── supabase/
│   └── schema.sql          # Database schema for user data
├── tests/
│   ├── test_api.py         # API integration tests
│   └── test_tools.py       # Tool logic tests
├── requirements.txt        # Backend dependencies
└── requirements-backend.txt# Pin-locked backend dependencies
```

## Features

### Autonomous Agent

- Iterative reasoning loop via LangGraph (agent → tools → agent)
- Dynamic tool usage: news, price data, sentiment analysis, skeptic critique, save
- Prevents redundant tool calls (checks existing state)
- Max iteration guard (default 8)

### Market Data & Sentiment

- Recent headline aggregation (NewsAPI)
- Historical OHLCV price retrieval (yfinance)
- Per-headline sentiment analysis + overall summary (Gemini 2.0 Flash Lite)
- Skeptic analysis providing contrarian views and bear cases

### User Belief System

- User authentication via Supabase
- Investment thesis creation and tracking
- Kill criteria definition
- Thesis history and evolution tracking

### Infrastructure

- FastAPI backend (analysis trigger, cached retrieval, health, auth)
- React frontend (interactive dashboard, thesis management)
- SQLite caching (automatic path fallback resolution)
- Supabase for user data persistence

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- [NewsAPI Key](https://newsapi.org/register)
- [Supabase Project](https://supabase.com/) (optional, for user features)

### Installation

```bash
git clone https://github.com/Spkap/StockSense-Agent.git
cd StockSense-Agent

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-backend.txt

# Frontend setup
cd frontend
npm install  # or pnpm install
cd ..

# Environment variables
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key
NEWSAPI_KEY=your_newsapi_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
EOF
```

### Running the Application

```bash
# Terminal 1 – Backend API
python -m stocksense.main  # http://127.0.0.1:8000

# Terminal 2 – Frontend
cd frontend
npm run dev  # http://localhost:5173
```

### REST API

```bash
# Trigger ReAct agent analysis
curl -X POST "http://localhost:8000/analyze/AAPL"

# Retrieve cached results
curl "http://localhost:8000/results/AAPL"

# System health check
curl "http://localhost:8000/health"

# Get all cached tickers
curl "http://localhost:8000/cached-tickers"
```

### Example Analysis Output

```json
{
  "ticker": "AAPL",
  "summary": "Apple Inc. demonstrates strong market sentiment...",
  "sentiment_report": "Overall Sentiment: Positive ...",
  "headlines_count": 18,
  "overall_sentiment": "Bullish",
  "overall_confidence": 0.78,
  "key_themes": [...],
  "skeptic_report": "While sentiment is positive, consider...",
  "reasoning_steps": [...],
  "tools_used": ["fetch_news_headlines", "fetch_price_data", "analyze_sentiment", "generate_skeptic_critique"],
  "iterations": 4,
  "agent_type": "ReAct"
}
```

## API Reference

### Endpoints

| Method | Path                | Purpose                                    |
| ------ | ------------------- | ------------------------------------------ |
| POST   | `/analyze/{ticker}` | Run ReAct agent (fresh or cached shortcut) |
| GET    | `/results/{ticker}` | Latest cached summary & sentiment          |
| GET    | `/cached-tickers`   | List all cached tickers                    |
| GET    | `/health`           | Basic health status                        |
| GET    | `/api/me`           | Current user profile (auth required)       |
| GET    | `/api/theses`       | User's investment theses (auth required)   |
| POST   | `/api/theses`       | Create thesis (auth required)              |
| GET    | `/docs`             | Swagger UI                                 |

## Testing

```bash
# All tests (requires backend deps installed)
pytest -v

# Individual modules
pytest tests/test_api.py -v
pytest tests/test_tools.py -v

# Optional coverage
pytest --cov=stocksense --cov-report=term-missing
```

## Deployment

### Backend (Render)

Deploy the FastAPI backend to Render using the `render.yaml` configuration.

### Frontend (Vercel/Netlify)

The React frontend can be deployed to any static hosting service:

```bash
cd frontend
npm run build  # Produces dist/ folder
```

Set `VITE_API_URL` environment variable to your backend URL.

## Technical Highlights

- LangGraph workflow: agent node + tool node + conditional edge
- State tracks tools used, reasoning steps, iterations, messages
- Redundant tool invocations avoided (sentiment/news/price dedupe)
- SQLite path resolver with environment override + graceful fallbacks
- Gemini rate limit handling produces user-friendly summary
- Epistemic honesty: confidence scores, information gaps, skeptic critique

### Disclaimer

Example outputs are illustrative; actual results depend on live NewsAPI & yfinance data plus Gemini responses.
