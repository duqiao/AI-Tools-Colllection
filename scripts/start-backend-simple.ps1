# Simple FastAPI Backend Startup Script

Write-Host "🚀 Starting FastAPI backend..."

# Set environment variables
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:DEBUG = "true"
$env:SECRET_KEY = "dev-secret-key-change-in-production"
$env:CORS_ORIGINS = "http://localhost:3000,http://localhost:3007,http://127.0.0.1:3000,http://127.0.0.1:3007"

# Test database connection first
Write-Host "🔍 Testing database connection..."
try {
    $result = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $result -match "accepting connections") {
        Write-Host "❌ Database is not ready. Please ensure Docker containers are running:"
        Write-Host "   docker-compose -f docker-compose.dev.yml up postgres redis -d"
        exit 1
    }
    Write-Host "✅ Database is ready"
} catch {
    Write-Host "❌ Cannot connect to database. Please ensure Docker is running."
    exit 1
}

# Find Python
$pythonCmd = "py"  # Use the py command since it worked for you
try {
    $version = & $pythonCmd --version 2>$null
    if ($version -and $version -match "Python 3\.") {
        Write-Host "✅ Using Python: $version"
    } else {
        Write-Host "❌ Invalid Python version"
        exit 1
    }
} catch {
    Write-Host "❌ Python not found"
    exit 1
}

# Change to backend directory
Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"

# Check if dependencies are installed
Write-Host "📦 Checking dependencies..."
try {
    & $pythonCmd -c "import fastapi, uvicorn" 2>$null
    Write-Host "✅ Dependencies are available"
} catch {
    Write-Host "❌ Dependencies not found. Please run:"
    Write-Host "   .\scripts\install-dependencies.ps1"
    exit 1
}

# Start the server
Write-Host ""
Write-Host "🌐 Starting FastAPI server..."
Write-Host "   Server URL: http://localhost:8000"
Write-Host "   API Docs:  http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

try {
    & $pythonCmd -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "❌ Failed to start server: $_"
    exit 1
}