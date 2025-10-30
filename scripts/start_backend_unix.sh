#!/usr/bin/env bash
# Starts Hermes backend with SQLite (Unix/macOS)
# Usage: bash scripts/start_backend_unix.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"
export DATABASE_URL="sqlite+aiosqlite:///$REPO_ROOT/hermes_dev.db"
export PYTHONUNBUFFERED=1
printf "DATABASE_URL=%s\n" "$DATABASE_URL"
echo "Starting Hermes backend on http://127.0.0.1:8000 ..."
python -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
