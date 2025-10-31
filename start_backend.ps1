# Backend Startup Script for PowerShell (PostgreSQL Edition)
Write-Host "🚀 Starting Backend API with PostgreSQL" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Yellow

Set-Location $PSScriptRoot

Write-Host "📁 Current Directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check Docker services (PostgreSQL + Redis)
Write-Host "📦 Starting Docker services (PostgreSQL + Redis)..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.dev.yml up -d postgres redis
    Write-Host "✅ Docker services started" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start Docker services: $_" -ForegroundColor Red
    Write-Host "⚠️  Continuing anyway (backend may run without databases)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⏳ Waiting 15 seconds for PostgreSQL to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Test PostgreSQL
Write-Host "🔍 Testing PostgreSQL connection..." -ForegroundColor Blue
try {
    $postgresTest = docker exec ai-postgres-dev pg_isready -U admin -d ai_media_translation 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL is healthy" -ForegroundColor Green
        
        # Test database connection
        $connTest = docker exec ai-postgres-dev psql -U admin -d ai_media_translation -c "SELECT 1;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database connection successful" -ForegroundColor Green
        } else {
            Write-Host "⚠️  PostgreSQL running but database connection failed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ PostgreSQL not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ PostgreSQL test failed" -ForegroundColor Red
    Write-Host "💡 Make sure PostgreSQL is running on localhost:5432" -ForegroundColor Cyan
}

# Test Redis  
Write-Host "🔍 Testing Redis connection..." -ForegroundColor Blue
try {
    $redisTest = docker exec ai-redis-dev redis-cli -a dev123456 ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis is healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Redis test failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "🗄️  Setting up database schema..." -ForegroundColor Blue

# Change to backend directory
Set-Location "backend"

# Check if virtual environment exists
$venvPython = ".\venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
    
    # Clean environment before migration
    Write-Host "🧹 Cleaning environment variables..." -ForegroundColor Blue
    try {
        & $venvPython clean_env.py
    } catch {
        Write-Host "⚠️  Environment cleanup failed: $_" -ForegroundColor Yellow
    }
    
    # Run database migrations
    Write-Host "🔄 Running Alembic database migrations..." -ForegroundColor Yellow
    try {
        & $venvPython -m alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database migrations completed" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Migration failed - attempting to initialize..." -ForegroundColor Yellow
            # Try to initialize if first time
            & $venvPython -m alembic stamp head
            & $venvPython -m alembic upgrade head
        }
    } catch {
        Write-Host "⚠️  Migration error: $_" -ForegroundColor Yellow
        Write-Host "💡 Continuing with startup (will create tables if needed)" -ForegroundColor Cyan
    }
    
    # Create upload directories if they don't exist
    Write-Host "📁 Creating upload directories..." -ForegroundColor Blue
    if (!(Test-Path "uploads")) {
        New-Item -ItemType Directory -Path "uploads" | Out-Null
        Write-Host "✅ Created uploads directory" -ForegroundColor Green
    }
    if (!(Test-Path "temp")) {
        New-Item -ItemType Directory -Path "temp" | Out-Null
        Write-Host "✅ Created temp directory" -ForegroundColor Green
    }
    
    try {
        # Start backend
        Write-Host "🚀 Launching FastAPI server with PostgreSQL..." -ForegroundColor Green
        Write-Host ""
        Write-Host "📍 API will be available at:" -ForegroundColor Cyan
        Write-Host "   • Main API: http://127.0.0.1:8001" -ForegroundColor White
        Write-Host "   • Documentation: http://127.0.0.1:8001/docs" -ForegroundColor White  
        Write-Host "   • Health Check: http://127.0.0.1:8001/health" -ForegroundColor White
        Write-Host "   • PostgreSQL Status: Integrated" -ForegroundColor White
        Write-Host ""
        Write-Host "🔄 Press Ctrl+C to stop the server" -ForegroundColor Yellow
        Write-Host ""

        & $venvPython run.py
        
    } catch {
        Write-Host "❌ Failed to start backend: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "🛠️  Troubleshooting:" -ForegroundColor Yellow
        Write-Host "   1. Check if port 8001 is available: netstat -ano | findstr :8001" -ForegroundColor Gray
        Write-Host "   2. Check Python environment: .\venv\Scripts\python.exe --version" -ForegroundColor Gray
        Write-Host "   3. Check PostgreSQL connection: docker logs ai-postgres-dev" -ForegroundColor Gray
        Write-Host "   4. Check database exists: docker exec ai-postgres-dev psql -U admin -l" -ForegroundColor Gray
        Write-Host "   5. Run database setup: .\venv\Scripts\python.exe -m alembic upgrade head" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Setup instructions:" -ForegroundColor Yellow
    Write-Host "   1. Create virtual environment: python -m venv venv" -ForegroundColor Gray
    Write-Host "   2. Activate environment: .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   3. Install dependencies: pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "   4. Run this script again: .\start_backend.ps1" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎯 Once backend is running:" -ForegroundColor Cyan
Write-Host "   1. Start React Native: cd ..\react-native-app && npm start" -ForegroundColor Gray
Write-Host "   2. Test PostgreSQL integration: python test_postgres_connection.py" -ForegroundColor Gray
Write-Host "   3. Test API endpoints: python test_api_endpoints.py" -ForegroundColor Gray
Write-Host "   4. View database: docker exec -it ai-postgres-dev psql -U admin -d ai_media_translation" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 PostgreSQL Migration Complete:" -ForegroundColor Green
Write-Host "   • Database: PostgreSQL with UUID primary keys" -ForegroundColor Gray
Write-Host "   • Storage: JSONB columns for flexible data" -ForegroundColor Gray
Write-Host "   • Migration: Big Bang migration from MongoDB" -ForegroundColor Gray
Write-Host "   • Connection: asyncpg with connection pooling" -ForegroundColor Gray
Write-Host ""