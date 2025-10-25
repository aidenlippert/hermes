#!/bin/bash
# Railway Post-Deploy Migration Script
# This runs automatically after each Railway deployment

echo "🚀 Starting Railway post-deployment tasks..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
sleep 5

# Run Alembic migrations
echo "📦 Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Seed initial data if needed
echo "🌱 Checking for initial data..."
python scripts/init_database.py

echo "🎉 Post-deployment tasks complete!"
