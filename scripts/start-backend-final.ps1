# Final FastAPI Backend Startup Script

Write-Host "🚀 Starting FastAPI backend (Final Version)..."

# Navigate to backend directory
Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"

# Set environment variables directly
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:DEBUG = "true"
$env:SECRET_KEY = "dev-secret-key-change-in-production"
$env:APP_NAME = "WeChat Media Translator"
$env:VERSION = "1.0.0"
$env:ALGORITHM = "HS256"
$env:ACCESS_TOKEN_EXPIRE_MINUTES = "1440"
$env:UPLOAD_DIR = "uploads"
$env:MAX_FILE_SIZE = "104857600"
$env:LOG_LEVEL = "INFO"

# Test database connection
Write-Host "🔍 Testing database connection..."
try {
    $result = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres 2>&1
    if ($LASTEXITCODE -eq 0 -and $result -match "accepting connections") {
        Write-Host "✅ Database is ready"
    } else {
        Write-Host "❌ Database is not ready"
        Write-Host "   Please run: docker-compose -f docker-compose.dev.yml up postgres redis -d"
        exit 1
    }
} catch {
    Write-Host "❌ Cannot test database connection"
    exit 1
}

# Test Python dependencies
Write-Host "🐍 Testing Python dependencies..."
try {
    py -c "import fastapi, uvicorn, sqlalchemy, psycopg2, python_dotenv" 2>$null
    Write-Host "✅ Dependencies are available"
} catch {
    Write-Host "❌ Dependencies not found. Installing..."
    try {
        py -m pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
        Write-Host "✅ Dependencies installed"
    } catch {
        Write-Host "❌ Failed to install dependencies: $_"
        exit 1
    }
}

# Create a simple .env file with correct format
Write-Host "📝 Creating simple .env file..."
$envContent = @"
DATABASE_URL=postgresql://postgres:password@localhost:5432/wechat_translator
REDIS_URL=redis://localhost:6379/0
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
APP_NAME=WeChat Media Translator
VERSION=1.0.0
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=uploads
MAX_FILE_SIZE=104857600
LOG_LEVEL=INFO
"@

try {
    Set-Content -Path ".env" -Value $envContent -Encoding UTF8
    Write-Host "✅ .env file created"
} catch {
    Write-Host "❌ Failed to create .env file: $_"
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
    py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --env-file .env
} catch {
    Write-Host "❌ Failed to start server: $_"
    exit 1
}