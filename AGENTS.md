## Project Tooling

- Python dependency management is uv-first.
- `pyproject.toml` is the dependency source of truth.
- `uv.lock` is the reproducible lockfile.
- Use `uv sync`, `uv run ...`, and `uv export ...` instead of `pip install`, `python -m venv`, or `pip-compile`.
- `requirements.txt` and `requirements-backend.txt` are compatibility exports only; regenerate them from `uv.lock` if an external platform still needs requirements files.
