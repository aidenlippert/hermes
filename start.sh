#!/bin/bash
set -e

echo "🚀 Starting Hermes backend..."

# Run migrations
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
    alembic upgrade head || echo "⚠️ Migration failed or no migrations needed"
else
    echo "⚠️ No DATABASE_URL set, skipping migrations"
fi

# Start server with proper port handling
PORT=${PORT:-8000}
echo "🌐 Starting uvicorn on port $PORT..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
