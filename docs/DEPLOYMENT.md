# Deployment

StockSense has a static frontend and a FastAPI backend. Supabase provides auth and Postgres persistence.

## Required Production Environment

Backend:

| Variable | Purpose |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini access |
| `NEWSAPI_KEY` | News collection |
| `SEC_USER_AGENT` | SEC EDGAR compliant user agent |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Public Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Backend service role key |
| `CORS_ORIGINS` | Allowed frontend origins |
| `LOG_LEVEL` | Backend log level |

Frontend:

| Variable | Purpose |
| --- | --- |
| `VITE_API_URL` | Deployed backend URL |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon key |

## Backend: Cloud Run

The repo includes a Dockerfile and Cloud Build config.

```bash
gcloud builds submit --config cloudbuild.yaml
```

The Cloud Build pipeline:

1. Builds the backend Docker image.
2. Pushes it to Artifact Registry.
3. Deploys `stocksense-backend` to Cloud Run.

Current config defaults:

| Setting | Value |
| --- | --- |
| Service | `stocksense-backend` |
| Region | `asia-south1` |
| Container port | `8080` |
| Memory | `4Gi` |
| CPU | `4` |

The Dockerfile installs Python dependencies with uv from `pyproject.toml` and `uv.lock`.

## Backend: Render

`render.yaml` defines a web service that:

- installs dependencies with uv
- starts Uvicorn from the locked environment
- expects production secrets in the Render dashboard

Render is useful for a simple web-service deployment. Cloud Run is the more production-oriented path in this repo.

## Frontend

Build the frontend:

```bash
cd frontend
pnpm run build
```

Deploy `frontend/dist` to Vercel, Netlify, or another static host.

Set:

```text
VITE_API_URL=https://your-backend-url
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=...
```

Then set backend `CORS_ORIGINS` to the deployed frontend origin.

## Database

Before production traffic, apply the Supabase schema and migrations listed in [Development](DEVELOPMENT.md).

Verify:

- Auth is enabled for the frontend login flow.
- Row Level Security policies are present.
- `vector` extension is enabled for evidence memory migration `008`.
- Service role key is available only to backend runtime.

## Post-Deploy Checks

Backend:

```bash
curl https://your-backend-url/health
curl https://your-backend-url/cached-tickers
```

Frontend:

1. Load the deployed app.
2. Sign in with Supabase auth.
3. Create or open a thesis.
4. Run a thesis check and verify SSE progress.
5. Run a Research Room query.
6. Compile a thesis into World Model claims.

## Operational Notes

- `/health` reports degraded status when required dependencies or tables are missing.
- SSE routes require proxies that do not buffer responses.
- Cloud Run scales by instances; the Dockerfile runs one Uvicorn worker.
- Long-running research beyond request lifetime should move to a dedicated worker queue before heavy production use.
