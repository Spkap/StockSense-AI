## Project Tooling

- Python dependency management is uv-first.
- `pyproject.toml` is the dependency source of truth.
- `uv.lock` is the reproducible lockfile.
- Use `uv sync`, `uv run ...`, and `uv export ...` instead of `pip install`, `python -m venv`, or `pip-compile`.
- `requirements.txt` and `requirements-backend.txt` are compatibility exports only; regenerate them from `uv.lock` if an external platform still needs requirements files.

<claude-mem-context>
# Memory Context

# [StockSense-Agent] recent context, 2026-04-28 8:18pm GMT+5:30

No previous sessions found.
</claude-mem-context>
