# Development

This guide covers local setup, dependency policy, database setup, tests, and contribution contracts.

## Tooling Policy

Python dependency management is uv-first:

- `pyproject.toml` is the dependency source of truth.
- `uv.lock` is the reproducible lockfile.
- Use `uv sync`, `uv run ...`, and `uv export ...`.
- Do not use `pip install`, `python -m venv`, or `pip-compile` for project setup.
- `requirements.txt` and `requirements-backend.txt` are compatibility exports only.

Frontend dependency management uses pnpm.

## Prerequisites

- Python 3.11+
- uv
- Node.js 20+
- pnpm
- Google Gemini API key
- NewsAPI key
- Supabase project
- SEC EDGAR user agent with contact information

## Setup

```bash
uv sync

cd frontend
pnpm install
cd ..

cp .env.example .env
cp frontend/.env.example frontend/.env
```

## Environment Variables

Backend variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Yes | Gemini access |
| `NEWSAPI_KEY` | Yes | News collection |
| `SEC_USER_AGENT` | Recommended | SEC EDGAR compliant user agent |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Public Supabase key |
| `SUPABASE_SERVICE_KEY` | Yes | Backend-only trusted key |
| `PORT` | Optional | Local API port, default `8000` |
| `UVICORN_RELOAD` | Optional | Local reload toggle |
| `LOG_LEVEL` | Optional | Backend log level |
| `CORS_ORIGINS` | Optional | Comma-separated frontend origins |

Frontend variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `VITE_SUPABASE_URL` | Yes | Browser Supabase URL |
| `VITE_SUPABASE_ANON_KEY` | Yes | Browser Supabase anon key |
| `VITE_API_URL` | Production | Backend API URL |

## Database Setup

Run the SQL files in order:

```text
supabase/schema.sql
supabase/migrations/000_core_schema_baseline.sql
supabase/migrations/001_stage4_features.sql
supabase/migrations/002_phase2_watchman.sql
supabase/migrations/003_analysis_cache.sql
supabase/migrations/004_add_ticker_unique.sql
supabase/migrations/005_analysis_traces.sql
supabase/migrations/006_alert_history_rls_policies.sql
supabase/migrations/007_thesis_forensics_runs.sql
supabase/migrations/008_agent_runs_and_evidence_memory.sql
supabase/migrations/009_conviction_world_model.sql
supabase/migrations/010_lock_analysis_cache_writes.sql
```

Migration `008_agent_runs_and_evidence_memory.sql` enables the Supabase `vector` extension. If the SQL editor cannot create it, enable it from the Supabase dashboard first.

## Run Locally

```bash
uv run python -m stocksense.main
```

In another terminal:

```bash
cd frontend
pnpm run dev
```

Open:

```text
http://localhost:5173
```

## Tests And Checks

Backend:

```bash
uv run pytest tests -v
```

Useful targeted suites:

```bash
uv run pytest tests/test_thesis_check.py tests/test_thesis_check_routes.py -v
uv run pytest tests/test_research_room.py tests/test_research_room_routes.py -v
uv run pytest tests/test_world_model_routes.py tests/test_scenario_simulator.py -v
```

Frontend:

```bash
cd frontend
pnpm run typecheck
pnpm run build
```

Smoke tests:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/cached-tickers
```

## Add An Evidence Source

1. Add the provider adapter in `stocksense/core/`.
2. Normalize provider responses into typed evidence items.
3. Return explicit source status: `ok`, `empty`, `failed`, `timeout`, or `skipped`.
4. Add the collector to the relevant orchestration module.
5. Persist replayable source metadata if future runs should retrieve it.
6. Add tests with mocked provider responses.
7. Surface source health in the frontend before generated memo prose appears.

## Add An Agent Or Run Step

1. Define Pydantic input and output contracts in `stocksense/core/`.
2. Keep prompts and role behavior close to the owning orchestration module.
3. Prefer structured outputs. If free-form output is unavoidable, validate and repair before accepting it.
4. Require evidence references for grounded claims.
5. Log run steps with latency, prompt version, retry count, model, and validation errors when available.
6. Update SSE event handling and frontend types together.

## Coding Contracts

- Do not expose `SUPABASE_SERVICE_KEY` to frontend code.
- Do not make evidence-dependent claims before collecting evidence.
- Do not hide source failures as neutral empty data.
- Do not accept grounded agent claims without evidence references.
- Do not edit generated requirements files by hand after dependency changes.
- Keep public documentation focused on how to understand, run, deploy, and contribute to the project.

## Requirements Exports

Only regenerate requirements files when an external platform needs them:

```bash
uv export --format requirements-txt --output-file requirements.txt
uv export --format requirements-txt --output-file requirements-backend.txt --no-dev
```
