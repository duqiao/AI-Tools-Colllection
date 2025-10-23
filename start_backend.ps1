# Backend Startup Script for PowerShell
Write-Host "🚀 Starting Backend API" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Yellow

Set-Location $PSScriptRoot

Write-Host "📁 Current Directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host ""

# Check Docker services
Write-Host "📦 Starting Docker services (MongoDB + Redis)..." -ForegroundColor Blue
try {
    docker-compose -f docker-compose.dev.yml up -d mongodb redis
    Write-Host "✅ Docker services started" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start Docker services: $_" -ForegroundColor Red
    Write-Host "⚠️  Continuing anyway (backend may run without databases)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⏳ Waiting 10 seconds for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test MongoDB
Write-Host "🔍 Testing MongoDB connection..." -ForegroundColor Blue
try {
    $mongoTest = docker exec ai-mongodb-dev mongosh --eval "db.adminCommand('ping')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB is healthy" -ForegroundColor Green
    } else {
        Write-Host "❌ MongoDB not responding" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ MongoDB test failed" -ForegroundColor Red
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
Write-Host "🌐 Starting Backend API Server..." -ForegroundColor Blue

# Change to backend directory
Set-Location "backend"

# Check if virtual environment exists
$venvPython = ".\venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
    
    try {
        # Start backend
        Write-Host "🚀 Launching FastAPI server..." -ForegroundColor Green
        Write-Host ""
        Write-Host "📍 API will be available at:" -ForegroundColor Cyan
        Write-Host "   • Main API: http://127.0.0.1:8001" -ForegroundColor White
        Write-Host "   • Documentation: http://127.0.0.1:8001/docs" -ForegroundColor White  
        Write-Host "   • Health Check: http://127.0.0.1:8001/health" -ForegroundColor White
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
        Write-Host "   3. Check configuration: python test_config.py" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Once backend is running:" -ForegroundColor Cyan
Write-Host "   1. Start React Native: cd ..\react-native-app && npm start" -ForegroundColor Gray
Write-Host "   2. Test integration: python test_integration.py" -ForegroundColor Gray
Write-Host ""