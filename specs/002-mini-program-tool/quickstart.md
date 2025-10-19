# Quickstart Guide: Mini-Program Media Translation Tool Development

**Created**: 2025-10-18  
**Purpose**: Development setup and initial implementation guide for uni-app + FastAPI cross-platform development

## Overview

This guide helps developers set up their development environment for creating a cross-platform mini-program media translation tool using uni-app (frontend) and FastAPI (backend). The application supports WeChat mini-program, H5 web, and mobile app deployment with consistent user experience across all platforms.

## Prerequisites

### Development Tools
- **Node.js** 16+ and npm/yarn
- **Python** 3.11+ with pip
- **PostgreSQL** 15+ 
- **Redis** 6+ (for caching and task queues)
- **Git** for version control

### Platform-Specific Tools
- **HBuilderX** (recommended for uni-app development) OR
- **Vue CLI** with uni-app plugin
- **Postman** or similar API testing tool
- **Docker** and Docker Compose (optional but recommended)

### WeChat Development
- **WeChat Developer Tools** for mini-program testing
- **WeChat AppID** for development and testing
- **WeChat Pay Sandbox** for payment testing

## Project Setup

### 1. Repository Structure

```
wechat-media-translator/
├── frontend/                 # uni-app project
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── api/
│   │   ├── store/
│   │   └── utils/
│   ├── manifest.json
│   ├── pages.json
│   └── package.json
├── backend/                  # FastAPI project
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── alembic/
├── database/                 # Database setup
│   ├── migrations/
│   └── seeds/
├── docker-compose.yml        # Development environment
├── docs/                     # Documentation
└── README.md
```

### 2. Backend Setup (FastAPI)

#### Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary redis celery pydantic python-jose passlib python-multipart
pip install pytest pytest-asyncio httpx

# Install optional AI/ML libraries
pip install openai-whisper librosa pydub
```

#### Database Configuration

```bash
# Create PostgreSQL database
createdb wechat_translator

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/wechat_translator"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key-here"
export WECHAT_APPID="your-wechat-appid"
export WECHAT_SECRET="your-wechat-secret"
```

#### FastAPI Project Structure

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, translation, users, subscription

app = FastAPI(title="WeChat Media Translator API")

# CORS middleware for uni-app development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(translation.router, prefix="/api/v1/translation", tags=["translation"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(subscription.router, prefix="/api/v1/subscription", tags=["subscription"])
```

#### Database Models Setup

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(128), unique=True, nullable=False, index=True)
    username = Column(String(100))
    avatar_url = Column(String(1024))
    subscription_level = Column(String(50), default="free")
    quota_used = Column(Integer, default=0)
    quota_limit = Column(Integer, default=1)
    quota_reset_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="func.now()")
    updated_at = Column(DateTime, server_default="func.now()", onupdate="func.now()")
```

#### Run FastAPI Development Server

```bash
# Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API documentation will be available at:
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### 3. Frontend Setup (uni-app)

#### Option A: HBuilderX (Recommended)

1. Download and install **HBuilderX** from https://www.dcloud.io/hbuilderx.html
2. Create new uni-app project:
   - File → New → Project
   - Choose uni-app (Vue 3)
   - Select TypeScript template
   - Configure project details

#### Option B: Vue CLI

```bash
# Install Vue CLI
npm install -g @vue/cli

# Create uni-app project
vue create -p dcloudio/uni-preset-vue frontend

# Navigate to project
cd frontend

# Install dependencies
npm install
```

#### uni-app Configuration

```json
// manifest.json
{
  "name": "WeChat媒体翻译器",
  "appid": "__UNI__XXXXXX",
  "description": "语音视频转文字翻译小程序",
  "versionName": "1.0.0",
  "versionCode": "100",
  "transformPx": false,
  "mp-weixin": {
    "appid": "your-wechat-appid",
    "setting": {
      "urlCheck": false,
      "es6": true,
      "postcss": true,
      "minified": true
    },
    "usingComponents": true
  },
  "permission": {
    "scope.userLocation": {
      "desc": "用于获取用户位置信息"
    }
  }
}
```

```json
// pages.json
{
  "pages": [
    {
      "path": "pages/index/index",
      "style": {
        "navigationBarTitleText": "媒体翻译"
      }
    },
    {
      "path": "pages/history/history",
      "style": {
        "navigationBarTitleText": "翻译历史"
      }
    },
    {
      "path": "pages/profile/profile",
      "style": {
        "navigationBarTitleText": "个人中心"
      }
    }
  ],
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "媒体翻译器",
    "navigationBarBackgroundColor": "#F8F8F8",
    "backgroundColor": "#F8F8F8"
  },
  "tabBar": {
    "color": "#7A7E83",
    "selectedColor": "#3cc51f",
    "borderStyle": "black",
    "backgroundColor": "#ffffff",
    "list": [
      {
        "pagePath": "pages/index/index",
        "iconPath": "static/tab-home.png",
        "selectedIconPath": "static/tab-home-active.png",
        "text": "翻译"
      },
      {
        "pagePath": "pages/history/history",
        "iconPath": "static/tab-history.png",
        "selectedIconPath": "static/tab-history-active.png",
        "text": "历史"
      },
      {
        "pagePath": "pages/profile/profile",
        "iconPath": "static/tab-profile.png",
        "selectedIconPath": "static/tab-profile-active.png",
        "text": "我的"
      }
    ]
  }
}
```

#### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "strict": true,
    "jsx": "preserve",
    "importHelpers": true,
    "moduleResolution": "Node",
    "experimentalDecorators": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "lib": ["ESNext", "DOM", "DOM.Iterable", "ScriptHost"]
  },
  "include": [
    "src/**/*.ts",
    "src/**/*.tsx",
    "src/**/*.vue",
    "types/**/*.d.ts"
  ],
  "exclude": ["node_modules", "dist"]
}
```

#### API Service Layer

```typescript
// src/api/index.ts
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000/api/v1'
  : 'https://api.yourdomain.com/api/v1';

class ApiService {
  private baseURL = API_BASE_URL;

  async request<T>(url: string, options: RequestOptions = {}): Promise<ApiResponse<T>> {
    const token = uni.getStorageSync('token');
    
    const defaultOptions: RequestOptions = {
      header: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.header
      }
    };

    return new Promise((resolve, reject) => {
      uni.request({
        url: `${this.baseURL}${url}`,
        ...defaultOptions,
        ...options,
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data as ApiResponse<T>);
          } else {
            reject(new Error(`API Error: ${res.statusCode}`));
          }
        },
        fail: reject
      });
    });
  }

  async get<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(url, { 
      method: 'POST', 
      data,
      header: { 'Content-Type': 'application/json' }
    });
  }
}

export const api = new ApiService();
```

## Development Workflow

### 1. Backend Development

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Run database migrations
alembic upgrade head

# Start FastAPI development server
uvicorn app.main:app --reload

# Run tests
pytest

# Check code quality
black app/
isort app/
mypy app/
```

### 2. Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Start development server
npm run dev:mp-weixin  # For WeChat mini-program
# OR
npm run dev:h5         # For H5 development

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build:mp-weixin  # WeChat mini-program
npm run build:h5         # H5 production
```

### 3. Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add translation tasks table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### 4. Testing Strategy

#### Backend Testing

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

async def test_wechat_login_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/wechat-login", json={
        "code": "test_wechat_code",
        "userInfo": {
            "nickname": "测试用户",
            "avatarUrl": "https://example.com/avatar.jpg"
        }
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data["data"]
    assert data["data"]["user"]["username"] == "测试用户"

async def test_protected_endpoint_without_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "TOKEN_MISSING"
```

#### Frontend Testing

```typescript
// tests/auth.test.ts
import { api } from '@/api';

describe('Authentication', () => {
  beforeEach(() => {
    // Clear storage before each test
    uni.clearStorageSync();
  });

  it('should login with WeChat and store token', async () => {
    const mockResponse = {
      success: true,
      data: {
        user: { id: 1, username: '测试用户' },
        token: 'test-token',
        expiresIn: 86400
      }
    };

    jest.spyOn(uni, 'request').mockImplementation(({ success }) => {
      success({ statusCode: 200, data: mockResponse });
      return {} as any;
    });

    const result = await api.post('/auth/wechat-login', {
      code: 'test-code',
      userInfo: { nickname: '测试用户' }
    });

    expect(result.data.user.username).toBe('测试用户');
    expect(uni.setStorageSync).toHaveBeenCalledWith('token', 'test-token');
  });
});
```

## Key Configuration Files

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: wechat_translator
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres/wechat_translator
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
```

### Environment Configuration

```bash
# .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/wechat_translator
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# WeChat Configuration
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# File Storage
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_FILE_TYPES=mp3,wav,mp4,mov,avi

# Third-party Services
ALIBABA_CLOUD_ACCESS_KEY=your-access-key
ALIBABA_CLOUD_SECRET_KEY=your-secret-key
TENCENT_CLOUD_SECRET_ID=your-secret-id
TENCENT_CLOUD_SECRET_KEY=your-secret-key

# Development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Common Development Issues

### 1. WeChat Mini-Program Development

**Issue**: CORS errors during development  
**Solution**: Configure CORS in FastAPI and use WeChat Developer Tools

```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    cors_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    wechat_appid: str
    wechat_secret: str
    
    class Config:
        env_file = ".env"
```

### 2. File Upload Issues

**Issue**: File upload size limits  
**Solution**: Configure limits in both uni-app and FastAPI

```python
# app/core/config.py
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.mp4', '.mov', '.avi']

# FastAPI middleware
@app.middleware("http")
async def limit_file_size(request: Request, call_next):
    if request.method == "POST" and "multipart/form-data" in request.headers.get("content-type", ""):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
    return await call_next(request)
```

### 3. Database Connection Issues

**Issue**: Connection pool exhaustion  
**Solution**: Configure connection pool properly

```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

## Next Steps

1. **Complete Development Setup**: Follow this guide to set up your local environment
2. **Review API Contracts**: Study the detailed API specifications in `contracts/`
3. **Implement Core Features**: Start with authentication, then translation functionality
4. **Testing Strategy**: Implement comprehensive tests for all components
5. **Deployment Planning**: Plan for production deployment and CI/CD setup

## Support Resources

- **uni-app Documentation**: https://uniapp.dcloud.io/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **WeChat Mini-Program Development**: https://developers.weixin.qq.com/miniprogram/dev/
- **Project Repository**: Check the project's Git repository for latest updates

This quickstart guide provides everything needed to begin development of the uni-app + FastAPI migration.