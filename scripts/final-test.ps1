# Final Test - Check if backend can start

Write-Host "🧪 Final Backend Test"
Write-Host "=================="

# Test 1: Database Connection
Write-Host "1. Testing database connection..."
$dbTest = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>&1
if ($dbTest -match "accepting connections") {
    Write-Host "   ✅ PostgreSQL: Connected"
} else {
    Write-Host "   ❌ PostgreSQL: $dbTest"
    exit 1
}

# Test 2: Redis Connection  
Write-Host "2. Testing Redis connection..."
$redisTest = docker-compose -f docker-compose.dev.yml exec redis redis-cli ping 2>&1
if ($redisTest -match "PONG") {
    Write-Host "   ✅ Redis: Connected"
} else {
    Write-Host "   ❌ Redis: $redisTest"
    exit 1
}

# Test 3: Python Dependencies
Write-Host "3. Testing Python dependencies..."
try {
    py -c "import fastapi, uvicorn, sqlalchemy, psycopg2, python_dotenv" 2>$null
    Write-Host "   ✅ Python: Dependencies available"
} catch {
    Write-Host "   ❌ Python: Missing dependencies"
    Write-Host "   Run: py -m pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv"
    exit 1
}

Write-Host ""
Write-Host "🎉 All tests passed!"
Write-Host ""
Write-Host "You can now start the backend server with:"
Write-Host "  Method 1 (Batch): .\scripts\start-server.bat"
Write-Host "  Method 2 (PowerShell): .\scripts\start-backend-final.ps1"
Write-Host "  Method 3 (Manual):"
Write-Host "     cd D:\Python\startup\AI-Tools-Colllection\backend"
Write-Host "     set DATABASE_URL=postgresql://postgres:password@localhost:5432/wechat_translator"
Write-Write "     set REDIS_URL=redis://localhost:6379/0"
Write-Write "     py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host ""
Write-Host "🌐 Once started, access at:"
Write-Host "   - API: http://localhost:8000"
Write-Host "   - Docs: http://localhost:8000/docs"