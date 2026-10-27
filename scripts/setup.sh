#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null || { echo 'Install uv first: https://docs.astral.sh/uv/getting-started/installation/'; exit 1; }
command -v npm >/dev/null || { echo 'Install Node.js 22.12+ first.'; exit 1; }
uv venv --python 3.12 --allow-existing .venv
uv pip sync --python .venv/bin/python requirements.lock
(cd frontend && npm ci)
for file in .env frontend/.env; do
  if [ ! -f "$file" ]; then
    cp "$file.example" "$file"
    chmod 600 "$file"
  fi
done
echo 'Dependencies ready. Fill .env and frontend/.env; see docs/LOCAL_SETUP.md.'
