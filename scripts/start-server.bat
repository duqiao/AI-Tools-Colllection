@echo off
echo Starting FastAPI Backend Server
echo =====================================

echo Testing database connection...
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Database is not ready
    echo Please ensure Docker containers are running
    pause
    exit /b
)

echo Database is ready!
echo.

echo Setting environment variables...
set DATABASE_URL=postgresql://postgres:password@localhost:5432/wechat_translator
set REDIS_URL=redis://localhost:6379/0
set DEBUG=true
set SECRET_KEY=dev-secret-key-change-in-production

echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

cd D:\Python\startup\AI-Tools-Colllection\backend
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause