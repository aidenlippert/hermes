#!/bin/bash
set -e

# This entrypoint ensures any provided command runs via a shell
# so environment variables like $PORT are expanded correctly.

# ALWAYS run migrations first, regardless of what command Railway executes
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
  if [ "${FORCE_DB_RESET}" = "true" ]; then
    echo "🧨 FORCE_DB_RESET=true — performing destructive reset then migrating to head"
    # STEP 0: Drop alembic_version table to force a clean migration run
    echo "🔑 Step 0: Dropping alembic_version table to force fresh migrations..."
    PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\([^@]*\)@.*/\1/p') \
    PGHOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p') \
    PGPORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p') \
    PGDATABASE=$(echo "$DATABASE_URL" | sed -n 's/.*\/\(.*\)/\1/p') \
    PGUSER=$(echo "$DATABASE_URL" | sed -n 's/.*\/\/\([^:]*\):.*/\1/p') \
    psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -c "DROP TABLE IF EXISTS alembic_version CASCADE;" 2>&1 || echo "⚠️ Could not drop alembic_version (might not exist yet)"

    # STEP 1: Force-run the reset migration to wipe the database clean.
    echo "🔑 Step 1: Forcibly running the database reset migration (8f4f678fe91e)..."
    alembic upgrade 8f4f678fe91e 2>&1 || echo "⚠️ Could not run reset migration (this might be expected on the very first run)."

    # STEP 2: Run all subsequent migrations up to head.
    echo "🔑 Step 2: Running all migrations up to head..."
    alembic upgrade head 2>&1 || echo "⚠️ Migration failed or no migrations needed"
  else
    echo "🔄 Running safe migrations to head (data will be preserved). Set FORCE_DB_RESET=true to wipe DB."
    # Check if there are multiple heads and merge them
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
  fi
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
