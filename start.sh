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
      echo "⚠️ Multiple heads detected. Upgrading each head individually..."
      # Upgrade to first head (federation path)
      alembic upgrade federation_contacts_v1 2>&1 || echo "⚠️ Federation path migration done/failed"
      # Upgrade to second head (orgs/acl path)  
      alembic upgrade a2a_p0_1 2>&1 || echo "⚠️ A2A/Orgs path migration done/failed"
      # Now upgrade to the merge point
      echo "✅ Upgrading to merge point..."
      alembic upgrade heads 2>&1 || echo "⚠️ Final merge migration failed"
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
