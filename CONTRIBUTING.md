# Contributing

Thanks for improving StockSense. This project is an evidence-first investment research system, so the quality bar is higher than "the UI renders" or "the model answered."

## Development Flow

```bash
git checkout -b feature/your-change
uv sync
cd frontend && pnpm install && cd ..
```

Run the checks that match your change:

```bash
uv run pytest tests -v

cd frontend
pnpm run typecheck
pnpm run build
```

## Dependency Policy

- Python dependencies go through `pyproject.toml`.
- Commit `uv.lock` when dependencies change.
- Do not hand-edit `requirements.txt` or `requirements-backend.txt`; regenerate them with uv only when needed for deployment compatibility.
- Frontend dependencies go through `frontend/package.json` and `frontend/pnpm-lock.yaml`.

## Testing Expectations

| Change type | Expected checks |
| --- | --- |
| Backend route | Route tests plus relevant orchestration tests |
| Agent output schema | Schema tests and agent validation tests |
| Evidence source | Mocked provider tests and source-status behavior |
| Persistence | Payload builder tests and migration review |
| Frontend UI | Typecheck, build, and manual local flow check |
| Documentation | Link check and command accuracy review |

## Product Contracts

- User-facing finance claims must be evidence-backed or clearly marked as missing proof.
- Source failures must be visible; do not silently convert infrastructure failures into neutral empty evidence.
- Browser code must never receive service-role secrets.
- Agent outputs should use typed schemas and validation.
- Evidence-dependent agent flows should collect deterministic evidence before generating prose.
- User corrections and run history should be preserved when behavior changes.

## Documentation

Public docs should help a visitor understand, run, deploy, or contribute to the project. Internal planning notes, audits, scratch specs, and agent execution plans should stay out of the public documentation surface.

Update docs when changing:

- setup commands
- environment variables
- Supabase migrations
- public API routes
- deployment behavior
- major architecture boundaries

## Disclaimer Standard

StockSense is research software, not financial advice. New user-facing surfaces should avoid language that sounds like a trading recommendation or guaranteed outcome.
