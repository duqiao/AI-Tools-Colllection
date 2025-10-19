@echo off
echo Starting FastAPI Backend Server (Simple Version)
echo ================================================

cd /d "D:\Python\startup\AI-Tools-Colllection\backend"

echo Starting server without .env file...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause