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
    echo "Running: alembic upgrade head"
    alembic upgrade head 2>&1 || echo "⚠️ Migration failed or no migrations needed"
else
    echo "⚠️ No DATABASE_URL set, skipping migrations"
fi

# Start server with proper port handling
PORT=${PORT:-8000}
echo "🌐 Starting uvicorn on port $PORT..."
echo "Command: uvicorn backend.main_v2:app --host 0.0.0.0 --port $PORT"
exec uvicorn backend.main_v2:app --host 0.0.0.0 --port "$PORT"
