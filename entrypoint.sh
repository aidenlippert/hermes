#!/bin/bash
set -e

# This entrypoint ensures any provided command runs via a shell
# so environment variables like $PORT are expanded correctly.

# ALWAYS run migrations first, regardless of what command Railway executes
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    echo "Running: alembic upgrade head"
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
