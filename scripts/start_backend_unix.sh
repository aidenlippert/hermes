#!/usr/bin/env bash
# Starts Hermes backend with SQLite (Unix/macOS)
# Usage: bash scripts/start_backend_unix.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Resolve a Python interpreter
PY=""
if [[ -n "${PYTHON_BIN:-}" ]] && command -v "$PYTHON_BIN" >/dev/null 2>&1; then
	PY="$PYTHON_BIN"
elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
	PY="$REPO_ROOT/.venv/bin/python"
elif command -v python >/dev/null 2>&1; then
	PY="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
	PY="$(command -v python3)"
else
	echo "Error: No Python interpreter found."
	echo "Install Python 3.10+ or create a venv, for example:" 1>&2
	echo "  sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip" 1>&2
	echo "  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" 1>&2
	exit 1
fi

export DATABASE_URL="sqlite+aiosqlite:///$REPO_ROOT/hermes_dev.db"
export PYTHONUNBUFFERED=1
printf "DATABASE_URL=%s\n" "$DATABASE_URL"

# Basic dependency checks to provide a friendly hint
MISSING=()
for MOD in uvicorn fastapi sqlalchemy aiosqlite; do
	if ! "$PY" -c "import $MOD" >/dev/null 2>&1; then
		MISSING+=("$MOD")
	fi
done
if (( ${#MISSING[@]} > 0 )); then
	echo "Missing Python modules for $PY: ${MISSING[*]}" 1>&2
	echo "Install them with:" 1>&2
	echo "  $PY -m pip install -r requirements.txt" 1>&2
	exit 1
fi

echo "Starting Hermes backend on http://127.0.0.1:8000 ..."
exec "$PY" -m uvicorn backend.main_v2:app --host 127.0.0.1 --port 8000 --log-level info
