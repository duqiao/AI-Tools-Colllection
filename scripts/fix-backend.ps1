# Quick Fix Script for Backend Issues

Write-Host "🔧 Fixing backend setup..."

# Navigate to backend directory
Set-Location "D:\Python\startup\AI-Tools-Colllection\backend"

# Install dependencies using py command
Write-Host "📦 Installing dependencies..."
try {
    py -m pip install --upgrade pip
    py -m pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully!"
} catch {
    Write-Host "❌ Failed to install dependencies: $_"
    Write-Host "Try running this manually:"
    Write-Host "  cd D:\Python\startup\AI-Tools-Colllection\backend"
    Write-Host "  py -m pip install -r requirements.txt"
    exit 1
}

# Set environment variables for the session
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/wechat_translator"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:DEBUG = "true"
$env:SECRET_KEY = "dev-secret-key-change-in-production"

Write-Host ""
Write-Host "✅ Setup completed!"
Write-Host ""
Write-Host "Now start the server with:"
Write-Host "  py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host ""
Write-Host "Or run the simple startup script:"
Write-Host "  cd D:\Python\startup\AI-Tools-Colllection"
Write-Host "  .\scripts\start-backend-simple.ps1"