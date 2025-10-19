@echo off
echo Starting Docker services...

cd /d "D:\Python\startup\AI-Tools-Colllection"

docker-compose -f docker-compose.dev.yml up -d postgres redis

echo.
echo Checking services...

echo Testing PostgreSQL:
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres

echo.
echo Testing Redis:
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

echo.
echo Services started! You can now run:
echo PowerShell: .\scripts\start-backend-dev.ps1
echo Or: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause