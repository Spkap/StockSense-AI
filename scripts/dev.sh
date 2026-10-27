#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -x .venv/bin/python ] || { echo 'Run ./scripts/setup.sh first.'; exit 1; }
.venv/bin/python scripts/check_config.py
backend_pid=''
frontend_pid=''
cleanup() {
  [ -z "$backend_pid" ] || kill "$backend_pid" 2>/dev/null || true
  [ -z "$frontend_pid" ] || kill "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
.venv/bin/python -m uvicorn stocksense.main:app --host 127.0.0.1 --port 8000 --reload &
backend_pid=$!
npm --prefix frontend run dev -- --host 127.0.0.1 --strictPort &
frontend_pid=$!
echo 'Frontend: http://127.0.0.1:3000 | API docs: http://127.0.0.1:8000/docs'
while kill -0 "$backend_pid" 2>/dev/null && kill -0 "$frontend_pid" 2>/dev/null; do sleep 1; done
exit 1
