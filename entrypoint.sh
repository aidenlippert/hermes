#!/bin/bash
set -e

# This entrypoint ensures any provided command runs via a shell
# so environment variables like $PORT are expanded correctly.

# ALWAYS run migrations first, regardless of what command Railway executes
echo "📦 Running database migrations..."
if [ -n "$DATABASE_URL" ]; then
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
    echo "⚠️ No DATABASE_URL set, skipping migrations"
fi

if [ "$#" -gt 0 ]; then
  cmd="$*"
else
  cmd="./start.sh"
fi

echo "🔑 ENTRYPOINT executing: $cmd"
exec /bin/bash -lc "$cmd"
