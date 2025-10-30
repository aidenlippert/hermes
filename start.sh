#!/bin/bash
set -e

echo "🚀 Starting Hermes backend..."
echo "📊 Environment check:"
echo "  DATABASE_URL: ${DATABASE_URL:0:20}..."
echo "  REDIS_URL: ${REDIS_URL:0:20}..."
echo "  PORT: ${PORT:-NOT_SET}"

# Run migrations
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    echo "🔍 Checking for multiple migration heads..."
    HEADS_COUNT=$(alembic heads 2>/dev/null | wc -l)
    if [ "$HEADS_COUNT" -gt 1 ]; then
      echo "⚠️ Multiple heads detected. Upgrading to merge point (a1afb20e28ab)..."
      alembic upgrade a1afb20e28ab 2>&1 || echo "⚠️ Migration to merge point failed"
    else
      echo "✅ Single head found. Upgrading to head..."
      alembic upgrade head 2>&1 || echo "⚠️ Migration failed or no migrations needed"
    fi
else
    echo "⚠️ No DATABASE_URL set, skipping migrations"
fi

# Start server with proper port handling
PORT=${PORT:-8000}
echo "🌐 Starting uvicorn on port $PORT..."
echo "Command: uvicorn backend.main_v2:app --host 0.0.0.0 --port $PORT"
exec uvicorn backend.main_v2:app --host 0.0.0.0 --port "$PORT"
