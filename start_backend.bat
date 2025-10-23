@echo off
echo Backend Startup Script
echo ====================

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Starting Docker services...
docker-compose -f docker-compose.dev.yml up -d mongodb redis

echo.
echo Waiting for services to start...
timeout /t 15 /nobreak

echo.
echo Testing Docker services...
docker exec ai-mongodb-dev mongosh --eval "db.adminCommand('ping')" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ MongoDB is running
) else (
    echo ❌ MongoDB not ready
)

docker exec ai-redis-dev redis-cli -a dev123456 ping >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Redis is running
) else (
    echo ❌ Redis not ready
)

echo.
echo Starting backend API...
cd backend
venv\Scripts\python.exe run.py

echo.
echo Backend startup complete!
echo.
echo Access points:
echo   🌐 API: http://127.0.0.1:8001
echo   📚 Docs: http://127.0.0.1:8001/docs
echo   ❤️  Health: http://127.0.0.1:8001/health

pause