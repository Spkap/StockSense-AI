# Local setup

Run `./scripts/setup.sh` from the repository root. Requires uv and Node.js 22.12+ (Node 24 works). Python 3.12 is isolated in `.venv`; backend packages are pinned in `requirements.lock`.

Fill `.env` with `FIREWORKS_API_KEY`, `NEWSAPI_KEY`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY`. Add `SUPABASE_SERVICE_KEY` for background thesis monitoring. Keep that service key exclusively on the backend.

Fill `frontend/.env` with the matching `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL=http://127.0.0.1:8000`. These files are ignored by Git. Restart services after changing them. Never put a service key in a VITE variable.

In your StockSense Supabase project's SQL editor, apply these files in order:

1. `supabase/schema.sql`
2. `supabase/migrations/001_stage4_features.sql`
3. `supabase/migrations/002_phase2_watchman.sql`
4. `supabase/migrations/003_analysis_cache.sql`

Enable the desired email/Google login providers in Supabase Auth. Allow `http://127.0.0.1:3000` and `http://localhost:3000` as local redirect URLs. Google login additionally requires Google OAuth provider credentials in Supabase.

Run `./scripts/dev.sh` to launch both services. Ctrl-C stops both. The script checks required local values first; it does not verify keys remotely. Frontend: http://127.0.0.1:3000. API and Swagger: http://127.0.0.1:8000/docs. These fixed ports must be available.

Before credentials are ready, run `cd frontend && npm run dev` to view the dashboard at http://localhost:3000. Analysis and account features remain unavailable.

Verification:

```sh
.venv/bin/python scripts/check_config.py
uv pip check --python .venv/bin/python
.venv/bin/python -m pytest tests/test_scheduler.py -q
npm --prefix frontend run build
curl --fail http://127.0.0.1:8000/health
```

The existing API/tool tests use live services and external data. They are not proof of working Fireworks, NewsAPI, or Supabase access until real credentials are supplied and those paths are exercised. The health endpoint checks API-key presence, not provider acceptance.

AI inference uses `langchain-fireworks` with `accounts/fireworks/models/deepseek-v4p1-flash-1017`. Set `FIREWORKS_MODEL` in `.env` to override the default. Gemini credentials are no longer used. Fireworks does not replace NewsAPI or Supabase.
