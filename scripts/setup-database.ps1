# Database Setup Script for WeChat Media Translator
# This script sets up the database using local Python environment

Write-Host "🚀 Starting database setup..."

# Set environment variables
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:PYTHONPATH = "D:\Python\startup\AI-Tools-Colllection\backend"

# Check if PostgreSQL is running
Write-Host "🔍 Checking PostgreSQL connection..."
try {
    $result = docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres
    if ($result -match "accepting connections") {
        Write-Host "✅ PostgreSQL is running and accepting connections"
    } else {
        Write-Host "❌ PostgreSQL is not ready"
        exit 1
    }
} catch {
    Write-Host "❌ Failed to connect to PostgreSQL: $_"
    exit 1
}

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
        if ($version) {
            Write-Host "✅ Found Python: $path ($version)"
            $pythonCmd = $path
            break
        }
    } catch {
        # Continue to next path
    }
}

if (-not $pythonCmd) {
    Write-Host "❌ Python not found. Please install Python 3.11+ and add it to PATH"
    exit 1
}

# Install dependencies
Write-Host "📦 Installing Python dependencies..."
Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"
try {
    & $pythonCmd -m pip install --upgrade pip
    & $pythonCmd -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully"
} catch {
    Write-Host "❌ Failed to install dependencies: $_"
    exit 1
}

# Run Alembic migrations
Write-Host "🗃️ Running database migrations..."
try {
    & $pythonCmd -m alembic upgrade head
    Write-Host "✅ Database migrations completed successfully"
    
    # Show migration status
    Write-Host "📊 Migration status:"
    & $pythonCmd -m alembic current
} catch {
    Write-Host "❌ Migration failed: $_"
    exit 1
}

Write-Host "🎉 Database setup completed successfully!"