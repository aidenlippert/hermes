#!/bin/bash
set -e

# This entrypoint ensures any provided command runs via a shell
# so environment variables like $PORT are expanded correctly.

# ALWAYS run migrations first, regardless of what command Railway executes
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    # STEP 1: Force-run the reset migration to wipe the database clean.
    echo "🔑 Step 1: Forcibly running the database reset migration (8f4f678fe91e)..."
    alembic upgrade 8f4f678fe91e 2>&1 || echo "⚠️ Could not run reset migration (this might be expected on the very first run)."

    # STEP 2: Run all subsequent migrations up to head.
    echo "🔑 Step 2: Running all migrations up to head..."
    alembic upgrade head 2>&1 || echo "⚠️ Migration failed or no migrations needed"
else
    echo "⚠️ No DATABASE_URL set, skipping migrations"
fi

if [ "$#" -gt 0 ]; then
  cmd="$*"
else
  cmd="./start.sh"
fi

echo "🔑 ENTRYPOINT executing: $cmd"
exec /bin/bash -lc "$cmd"
