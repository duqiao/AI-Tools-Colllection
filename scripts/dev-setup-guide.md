# Development Setup Guide

## 🚀 Quick Start

This guide helps you set up the complete development environment for the WeChat Media Translator project.

## Prerequisites

- Docker Desktop (for PostgreSQL and Redis)
- Python 3.11+ (for FastAPI backend)
- Node.js 18+ (for Vue 3 frontend)
- Git

## 📋 Setup Steps

### 1. Start Database Services

```bash
# Navigate to project root
cd D:\Python\startup\AI-Tools-Colllection

# Start PostgreSQL and Redis
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Verify services are running
docker-compose -f docker-compose.dev.yml ps
```

### 2. Database Setup

The database tables are automatically created when you start PostgreSQL for the first time. If you need to recreate them:

```bash
# Reset database (WARNING: This deletes all data)
docker-compose -f docker-compose.dev.yml down
docker volume rm ai-tools-collection_postgres_data_dev
docker-compose -f docker-compose.dev.yml up -d postgres redis
```

### 3. Start Backend (FastAPI)

#### Option A: Using PowerShell Script (Recommended)
```powershell
# Navigate to project root
cd D:\Python\startup\AI-Tools-Colllection

# Run the backend startup script
.\scripts\start-backend-dev.ps1
```

#### Option B: Manual Setup
```bash
# Navigate to backend directory
cd D:\Python\startup\AI-Tools-Colllection\backend

# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/wechat_translator"
export REDIS_URL="redis://localhost:6379/0"
export DEBUG="true"
export SECRET_KEY="dev-secret-key-change-in-production"

# Install dependencies (if not already installed)
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-multipart pydantic python-dotenv

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Start Frontend (Vue 3)

```bash
# Navigate to frontend directory
cd D:\Python\startup\AI-Tools-Colllection\wechat-miniprogram

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🔍 Verification

### 1. Database Connection
```bash
# Test PostgreSQL
docker-compose -f docker-compose.dev.yml exec postgres pg_isready -U postgres

# Test Redis
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping
```

### 2. Backend API
- Open http://localhost:8000 in browser
- Should see: `{"message": "WeChat Media Translator API", "version": "1.0.0", "status": "running"}`
- API Documentation: http://localhost:8000/docs

### 3. Frontend
- Open http://localhost:3007 (or the port shown in terminal)
- Should see the AI语音视频工具 interface

## 🛠️ Development Workflow

### Database Operations

```bash
# Connect to database
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d wechat_translator

# View tables
\dt

# View users
SELECT * FROM users LIMIT 5;
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Test endpoints (requires authentication)
curl http://localhost:8000/api/v1/translation/status
```

### Frontend Development

The frontend is built with Vue 3 + TypeScript and includes:
- Responsive design matching Figma mockups
- Browser-compatible uni-app API layer
- Component-based architecture

## 🐛 Troubleshooting

### Port Conflicts
If ports are already in use, the services will automatically try alternative ports:
- Frontend: 3000, 3001, 3002, etc.
- Backend: 8000
- Database: 5432
- Redis: 6379

### Docker Issues
```bash
# Restart Docker services
docker-compose -f docker-compose.dev.yml restart

# View logs
docker-compose -f docker-compose.dev.yml logs postgres
docker-compose -f docker-compose.dev.yml logs redis
```

### Backend Issues
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install
```

## 📊 Project Structure

```
AI-Tools-Colllection/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── api/           # API endpoints
│   │   ├── services/      # Business logic
│   │   └── core/          # Configuration
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile.dev     # Docker development config
├── wechat-miniprogram/     # Vue 3 frontend
│   ├── src/
│   │   ├── pages/         # Vue pages
│   │   ├── components/    # Vue components
│   │   ├── stores/        # State management
│   │   └── utils/         # Utilities
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile          # Docker config
├── scripts/                # Utility scripts
├── docker-compose.dev.yml  # Development Docker config
└── specs/                  # Project specifications
```

## 🎯 Next Steps

1. **Test API Integration**: Connect frontend to backend APIs
2. **Implement Features**: Add new functionality following the task list
3. **Run Tests**: Implement and run automated tests
4. **Deploy**: Set up production deployment

## 📚 Documentation

- API Documentation: http://localhost:8000/docs
- Frontend Guide: Available in the Vue application
- Database Schema: Defined in `backend/app/models/`
- Task List: `specs/001-wechat-media-translator/tasks.md`