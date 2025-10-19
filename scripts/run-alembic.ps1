# Alembic migration runner for WeChat Media Translator
# This script runs database migrations inside the Docker container

Write-Host "🚀 Starting Alembic migrations..."

# Wait for PostgreSQL to be ready
Write-Host "⏳ Waiting for PostgreSQL to be ready..."
do {
    Start-Sleep -Seconds 2
    $ready = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>$null
} while ($LASTEXITCODE -ne 0)

Write-Host "✅ PostgreSQL is ready!"

# Run Alembic migrations
Write-Host "📝 Running database migrations..."
docker-compose -f docker-compose.dev.yml run --rm backend alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database migrations completed successfully!"
    
    # Show current migration status
    Write-Host "📊 Migration status:"
    docker-compose -f docker-compose.dev.yml run --rm backend alembic current
} else {
    Write-Host "❌ Migration failed!"
    exit 1
}

Write-Host "🎉 All done!"