# Quick Test Script - Verify All Services Are Working

Write-Host "🚀 Quick System Test"
Write-Host "==================="

# Test Docker services
Write-Host "📋 Testing Docker services..."

try {
    $postgresStatus = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0 -and $postgresStatus -match "accepting connections") {
        Write-Host "✅ PostgreSQL: Connected"
    } else {
        Write-Host "❌ PostgreSQL: Not ready - $postgresStatus"
    }
} catch {
    Write-Host "❌ PostgreSQL: Connection failed"
}

try {
    $redisStatus = docker-compose -f docker-compose.dev.yml exec redis redis-cli ping 2>&1
    if ($LASTEXITCODE -eq 0 -and $redisStatus -match "PONG") {
        Write-Host "✅ Redis: Connected"
    } else {
        Write-Host "❌ Redis: Not ready - $redisStatus"
    }
} catch {
    Write-Host "❌ Redis: Connection failed"
}

# Test Python
Write-Host ""
Write-Host "🐍 Testing Python..."
try {
    $pythonFound = $false
    $pythonPaths = @("python", "python3", "py")
    foreach ($path in $pythonPaths) {
        try {
            $version = & $path --version 2>$null
            if ($version -and $version -match "Python 3\.") {
                Write-Host "✅ Python: Found ($path)"
                $pythonFound = $true
                break
            }
        } catch {
            # Continue
        }
    }
    if (-not $pythonFound) {
        Write-Host "❌ Python: Not found"
    }
} catch {
    Write-Host "❌ Python: Check failed"
}

# Test ports
Write-Host ""
Write-Host "🌐 Testing ports..."

$ports = @{
    5432 = "PostgreSQL"
    6379 = "Redis"
    8000 = "FastAPI (Backend)"
    3007 = "Vue 3 (Frontend)"
}

foreach ($port in $ports.Keys) {
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $port)
        $connection.Close()
        Write-Host "✅ Port $port ($($ports[$port])): Open"
    } catch {
        Write-Host "❌ Port $port ($($ports[$port])): Closed"
    }
}

# Test database tables
Write-Host ""
Write-Host "🗃️ Testing database tables..."
try {
    $tables = docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d wechat_translator -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database tables: $tables"
    } else {
        Write-Host "❌ Database tables: Query failed"
    }
} catch {
    Write-Host "❌ Database tables: Connection failed"
}

Write-Host ""
Write-Host "🎉 Quick test completed!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Start backend: .\scripts\start-backend-dev.ps1"
Write-Host "2. Start frontend: cd wechat-miniprogram && npm run dev"
Write-Host "3. Open browser: http://localhost:3007"