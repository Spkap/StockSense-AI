# API

The StockSense backend is a FastAPI application. Public analysis endpoints can be called directly. Authenticated product endpoints require a Supabase access token:

```http
Authorization: Bearer <supabase-access-token>
```

The local API defaults to:

```text
http://127.0.0.1:8000
```

## Health And Metadata

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | API metadata and documentation links |
| `GET` | `/health` | Dependency status, version, required table checks |

Example:

```bash
curl http://127.0.0.1:8000/health
```

## Legacy Analysis Routes

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/analyze/{ticker}` | Run or retrieve cached ReAct-style ticker analysis |
| `GET` | `/analyze/{ticker}/stream` | Stream ticker analysis progress over SSE |
| `GET` | `/analyze/debate/{ticker}` | Run bull/bear adversarial debate |
| `GET` | `/analyze/debate/{ticker}/stream` | Stream debate progress over SSE |
| `GET` | `/results/{ticker}` | Get latest cached analysis |
| `DELETE` | `/results/{ticker}` | Delete cached analysis |
| `GET` | `/cached-tickers` | List cached tickers |

Example:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/AAPL?force=true"
```

## User And Thesis Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/me` | Current authenticated user |
| `GET` | `/api/positions` | List positions |
| `POST` | `/api/positions` | Create a position |
| `DELETE` | `/api/positions/{position_id}` | Delete a position |
| `GET` | `/api/theses` | List theses, optionally filtered by ticker |
| `POST` | `/api/theses` | Create a thesis |
| `PATCH` | `/api/theses/{thesis_id}` | Update a thesis and preserve history |
| `GET` | `/api/theses/{thesis_id}/history` | Fetch thesis history |
| `GET` | `/api/theses/{thesis_id}/compare` | Compare original analysis snapshot with current analysis |
| `GET` | `/api/kill-alerts` | List kill-criteria alerts |
| `GET` | `/api/kill-alerts/{alert_id}` | Fetch one alert |
| `PATCH` | `/api/kill-alerts/{alert_id}` | Update alert status |
| `DELETE` | `/api/kill-alerts/{alert_id}` | Delete an alert |

## Thesis Check Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/theses/{thesis_id}/check/stream` | Stream a fast thesis check |
| `GET` | `/api/theses/{thesis_id}/check/latest` | Latest thesis-check bundle |
| `GET` | `/api/thesis-runs/{run_id}` | Fetch one thesis run bundle |
| `POST` | `/api/thesis-runs/{run_id}/cancel` | Cancel a thesis check |
| `POST` | `/api/thesis-runs/{run_id}/corrections` | Save a correction for a run |

Thesis-check streams emit events like:

```json
{
  "type": "source_completed",
  "run_id": "uuid",
  "thesis_id": "uuid",
  "ticker": "AAPL",
  "phase": "evidence",
  "progress": 0.35,
  "message": "Collected 8 evidence items",
  "data": {
    "evidence_count": 8,
    "evidence_hash": "..."
  }
}
```

Terminal events include `completed`, `cancelled`, and `error`.

## Research Room Routes

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/research-room/{ticker}/stream?question=...` | Stream evidence-first research run |
| `GET` | `/api/research-room-runs/{run_id}` | Fetch Research Room run and steps |
| `POST` | `/api/research-room-runs/{run_id}/cancel` | Cancel Research Room run |
| `POST` | `/api/research-room-runs/{run_id}/thesis-draft` | Return generated thesis draft |

Research Room streams use the shared run event envelope:

```json
{
  "type": "retrieval_completed",
  "run_id": "uuid",
  "run_type": "research_room",
  "ticker": "NVDA",
  "phase": "retrieval",
  "progress": 0.44,
  "message": "Selected evidence for analyst context",
  "data": {
    "retrieved_ids": ["sec_10-q_01", "fact_revenue_01"]
  }
}
```

## World Model Routes

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/theses/{thesis_id}/compile` | Compile thesis into claims and forecast questions |
| `POST` | `/api/theses/{thesis_id}/scenarios` | Build bull/base/bear scenario paths |
| `POST` | `/api/forecast-questions/{forecast_id}/resolve` | Resolve a forecast and compute Brier score |

Resolve request:

```json
{
  "outcome": true,
  "probability": 0.62
}
```

## Error Expectations

| Status | Meaning |
| --- | --- |
| `400` | Invalid ticker, invalid payload, or missing required data |
| `401` | Missing, malformed, expired, or invalid bearer token |
| `404` | User-owned resource not found |
| `429` | Rate limit exceeded |
| `500` | Backend, provider, or persistence error |

Source failures inside agent runs should usually appear as source-health data rather than immediate request failure, unless the run cannot continue.
