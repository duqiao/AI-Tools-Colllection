# Install Python Dependencies Script

Write-Host "🚀 Installing Python dependencies for FastAPI backend..."

# Set environment variables
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:REDIS_URL = "redis://localhost:6379/0"

# Try to find Python executable
$pythonPaths = @(
    "python",
    "python3", 
    "py"
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

# Change to backend directory
Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"

# Install dependencies
Write-Host "📦 Installing dependencies from requirements.txt..."
try {
    & $pythonCmd -m pip install --upgrade pip
    & $pythonCmd -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully!"
    
    # Test installation
    Write-Host "🧪 Testing installation..."
    & $pythonCmd -c "import fastapi, uvicorn, sqlalchemy, psycopg2"
    Write-Host "✅ All dependencies imported successfully!"
    
} catch {
    Write-Host "❌ Failed to install dependencies: $_"
    exit 1
}

Write-Host ""
Write-Host "🎉 Installation completed!"
Write-Host ""
Write-Host "Now you can start the backend server with:"
Write-Host "  .\scripts\start-backend-simple.ps1"
Write-Host ""
Write-Host "Or manually:"
Write-Host "  cd backend"
Write-Host "  py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"