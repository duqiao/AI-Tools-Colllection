# WeChat Media Translator

A WeChat mini-program for media-to-text translation with AI-powered speech recognition.

## Project Overview

This application provides multi-format media translation capabilities including:
- Voice recording and transcription
- Audio file upload and processing  
- Video file audio extraction and transcription
- WeChat video message processing
- URL-based media download and transcription
- Freemium business model with VIP subscriptions

## Architecture

### Technology Stack

**Frontend (WeChat Mini-Program)**
- WeChat Mini-Program Framework
- TypeScript
- Vue.js 3
- uni-app (for cross-platform compatibility)

**Backend (FastAPI)**
- Python 3.11+
- FastAPI framework
- SQLAlchemy ORM
- PostgreSQL database
- Redis for caching
- Alembic for migrations

**External Services**
- Alibaba Cloud Speech Recognition
- Tencent Cloud Speech Recognition
- WeChat Pay API

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry point
│   ├── tests/              # Test suite
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile          # Container configuration
├── wechat-miniprogram/      # WeChat mini-program
│   ├── pages/              # Application pages
│   ├── components/         # Reusable components
│   ├── services/          # API services
│   ├── utils/             # Utility functions
│   ├── app.js             # Mini-program entry point
│   ├── pages.json         # Page configuration
│   ├── manifest.json      # App configuration
│   └── package.json       # Node.js dependencies
├── specs/                  # Feature specifications
│   ├── 001-wechat-media-translator/
│   └── 002-mini-program-tool/
└── docs/                  # Documentation
```

## Quick Start

### Backend Setup

1. **Create Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to mini-program directory**
   ```bash
   cd wechat-miniprogram
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure WeChat**
   - Update `manifest.json` with your WeChat AppID
   - Configure API endpoints in `app.js`

4. **Development**
   ```bash
   npm run dev:mp-weixin  # For WeChat mini-program
   # or
   npm run dev:h5         # For H5 web
   ```

## Development

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing
```bash
# Backend tests
cd backend
pytest

# Type checking
mypy app/

# Code formatting
black app/
isort app/
```

### Code Quality
```bash
# Linting
eslint wechat-miniprogram/src --ext .vue,.js,.ts

# Type checking  
npm run type-check
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `WECHAT_APPID`: WeChat application ID
- `WECHAT_SECRET`: WeChat application secret
- `ALIBABA_CLOUD_ACCESS_KEY_ID`: Alibaba Cloud access key
- `ALIBABA_CLOUD_ACCESS_KEY_SECRET`: Alibaba Cloud secret key
- `TENCENT_CLOUD_SECRET_ID`: Tencent Cloud secret ID
- `TENCENT_CLOUD_SECRET_KEY`: Tencent Cloud secret key

## Deployment

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Manual Deployment
1. **Backend**: Deploy to cloud server with Docker
2. **Database**: Set up PostgreSQL and Redis
3. **Miniprogram**: Upload to WeChat Developer Console

## API Endpoints

### Authentication
- `POST /api/v1/auth/wechat-login` - WeChat login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/refresh-token` - Refresh token

### Translation
- `POST /api/v1/translation/upload` - Upload media file
- `POST /api/v1/translation/start` - Start translation
- `GET /api/v1/translation/{task_id}/status` - Get translation status
- `GET /api/v1/translation/{task_id}/result` - Get translation result
- `GET /api/v1/translation/history` - Get translation history

### Users
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/stats` - Get user statistics

### Subscription
- `GET /api/v1/subscription/plans` - Get subscription plans
- `POST /api/v1/subscription/orders` - Create subscription order
- `POST /api/v1/subscription/pay/wechat` - WeChat payment
- `GET /api/v1/subscription/current` - Get current subscription

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request

## License

MIT License - see LICENSE file for details

## Support

For questions and support, please refer to the documentation or create an issue in the repository.