#!/bin/bash

# Alembic migration runner for WeChat Media Translator
# This script runs database migrations inside the Docker container

set -e

echo "🚀 Starting Alembic migrations..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run Alembic migrations
echo "📝 Running database migrations..."
docker-compose -f docker-compose.dev.yml run --rm backend alembic upgrade head

echo "✅ Database migrations completed successfully!"

# Show current migration status
echo "📊 Migration status:"
docker-compose -f docker-compose.dev.yml run --rm backend alembic current

echo "🎉 All done!"