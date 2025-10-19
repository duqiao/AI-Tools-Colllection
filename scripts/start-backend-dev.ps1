# Development Backend Startup Script
# This script starts the FastAPI backend with local Python

Write-Host "🚀 Starting FastAPI backend for development..."

# Set environment variables
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:DEBUG = "true"
$env:SECRET_KEY = "dev-secret-key-change-in-production"
$env:CORS_ORIGINS = "http://localhost:3000,http://localhost:3007,http://127.0.0.1:3000,http://127.0.0.1:3007"

# Change to project root directory (not backend)
Set-Location "D:\Python\startup\AI-Tools-Colllection"

# Try to find Python executable
$pythonPaths = @(
    "python",
    "python3",
    "py",
    "D:\Python\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe"
)

$pythonCmd = $null
foreach ($path in $pythonPaths) {
    try {
        $version = & $path --version 2>$null
        if ($version -and $version -match "Python 3\.") {
            Write-Host "✅ Found Python: $path ($version)"
            $pythonCmd = $path
            break
        }
    } catch {
        # Continue to next path
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python 3 not found. Please install Python 3.11+ and add it to PATH"
    exit 1
}

# Check if dependencies are installed
Write-Host "📦 Checking dependencies..."
try {
    & $pythonCmd -c "import fastapi, uvicorn, sqlalchemy, psycopg2" 2>$null
    Write-Host "✅ Dependencies are available"
} catch {
    Write-Host "📦 Installing dependencies..."
    try {
        & $pythonCmd -m pip install fastapi uvicorn sqlalchemy psycopg2-binary python-multipart pydantic pydantic-settings python-dotenv
        Write-Host "✅ Dependencies installed successfully"
    } catch {
        Write-Host "❌ Failed to install dependencies: $_"
        Write-Host "🔧 Trying to install in backend directory..."
        try {
            Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"
            & $pythonCmd -m pip install -r requirements.txt
            Set-Location "D:\Python\startup\AI-Tools-Colllection"
            Write-Host "✅ Dependencies installed successfully from requirements.txt"
        } catch {
            Write-Host "❌ Failed to install from requirements.txt: $_"
            exit 1
        }
    }
}

# Test database connection
Write-Host "🔍 Testing database connection..."
try {
    $result = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "accepting connections") {
        Write-Host "✅ Database is ready"
    } else {
        Write-Host "❌ Database is not ready. Please run: docker-compose -f docker-compose.dev.yml up postgres redis -d"
        Write-Host "   Command output: $result"
        exit 1
    }
} catch {
    Write-Host "❌ Cannot connect to database. Please ensure Docker is running."
    Write-Host "   Error: $_"
    exit 1
}

# Start the FastAPI server
Write-Host "🌐 Starting FastAPI server on http://localhost:8000"
Write-Host "📖 API documentation will be available at http://localhost:8000/docs"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host ""

try {
    # Change to backend directory to run uvicorn
    Push-Location "D:\Python\startup\AI-Tools-Colllection\backend"
    & $pythonCmd -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} catch {
    Write-Host "❌ Failed to start server: $_"
    exit 1
} finally {
    Pop-Location
}