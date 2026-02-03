#!/bin/bash
set -e

# Wait for DB if needed (optional, but good for production)
# echo "Waiting for database..."
# sleep 5 

# Run migrations
echo "🚀 Running database migrations..."
alembic upgrade head

# Start API
echo "🚀 Starting Uvicorn server..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
