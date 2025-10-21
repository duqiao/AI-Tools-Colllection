# AI Media Translation Backend - Python FastAPI

A comprehensive Python FastAPI backend for AI-powered media translation with video/audio recognition capabilities.

## 🎯 Features

- **Multi-format Support**: Audio (MP3, WAV, M4A, OGG, FLAC, AAC) + Video (MP4, MOV, AVI, MKV, WebM)
- **AI Speech-to-Text**: OpenAI Whisper integration with multiple models (tiny, base, small, medium, large)
- **Translation Services**: Google Translate + DeepL support
- **Real-time Progress**: Redis caching with live progress tracking
- **Media Processing**: FFmpeg audio extraction from video files
- **User Management**: Guest mode with quotas + JWT authentication
- **Modern Architecture**: Async FastAPI + MongoDB + Redis
- **Production Ready**: Comprehensive logging, error handling, health checks

## 🏗️ Technology Stack

- **Backend**: Python 3.9+ with FastAPI (async support)
- **AI/ML**: OpenAI Whisper, Google Translate, transformers
- **Database**: MongoDB with Motor (async driver)
- **Caching**: Redis for real-time progress tracking
- **Media**: FFmpeg for audio/video processing
- **Authentication**: JWT with refresh tokens

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.9+ (3.9 or 3.10 recommended)
python --version

# MongoDB 5.0+
mongod --version

# Redis 6.0+
redis-server --version

# FFmpeg
ffmpeg -version
```

### Installation

1. **Clone and Setup**:
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

2. **Install Dependencies (try one of these)**:

**Option A: Stable Versions (Recommended)**
```bash
pip install -r requirements.stable.txt
```

**Option B: Minimal Versions (Most Compatible)**
```bash
pip install -r requirements.minimal.txt
```

**Option C: Manual Installation**
```bash
# Install core requirements first
pip install fastapi uvicorn python-multipart python-jose[cryptography] pymongo redis pydantic aiofiles python-dotenv

# Then install PyTorch
pip install torch==2.1.0 torchaudio==2.1.0

# Then install Whisper
pip install openai-whisper==20231117
```

**Option D: If you have GPU issues**
```bash
# CPU-only versions
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu/torch_stable.html
pip install torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu/torchaudio_stable.html
```

3. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Start Services**:
```bash
# Start MongoDB and Redis in separate terminals
mongod
redis-server

# Start the API server
python run.py
```

2. **Configure Environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Start Services**:
```bash
# Start MongoDB
mongod

# Start Redis
redis-server

# Start the API server
python run.py
```

### Key Environment Variables

```env
# AI Services (choose your providers)
STT_PROVIDER=openai          # or google
OPENAI_API_KEY=your-key

TRANSLATION_PROVIDER=google    # or deepl
GOOGLE_TRANSLATE_API_KEY=your-key

# Database
MONGODB_URI=mongodb://localhost:27017/ai_media_translation
REDIS_URL=redis://localhost:6379
```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/auth/guest` - Guest user registration
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Media Upload  
- `POST /api/v1/upload` - Upload audio/video file
- `GET /api/v1/upload/{jobId}/status` - Get upload status
- `DELETE /api/v1/upload/{jobId}` - Delete uploaded file
- `GET /api/v1/upload/history` - Get upload history

### Translation
- `POST /api/v1/translation/{taskId}/start` - Start translation processing
- `GET /api/v1/translation/{taskId}/status` - Get translation status  
- `DELETE /api/v1/translation/{taskId}` - Cancel translation
- `GET /api/v1/translation/history` - Get translation history

### User Management
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `GET /api/v1/users/statistics` - Get user statistics

### Health Checks
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health
- `GET /health/ready` - Readiness probe (Kubernetes)
- `GET /health/live` - Liveness probe (Kubernetes)

## 🔄 Processing Pipeline

1. **File Upload** → User uploads audio/video via `/api/v1/upload`
2. **Processing Start** → Client calls `/api/v1/translation/{taskId}/start`
3. **Audio Extraction** → Extract audio from video (if needed) using FFmpeg
4. **Speech-to-Text** → Convert speech to text using OpenAI Whisper
5. **Translation** → Translate text to target language
6. **Result Storage** → Save results to MongoDB
7. **Real-time Updates** → Progress tracked via Redis cache

## 🔧 Configuration

### Whisper Models
```env
WHISPER_MODEL=base    # Options: tiny, base, small, medium, large
# tiny: ~32MB, fast, less accurate
# base: ~142MB, balanced speed/accuracy  
# large: ~1550MB, most accurate, slower
```

### File Size Limits
```env
MAX_AUDIO_SIZE=52428800    # 50MB for audio
MAX_VIDEO_SIZE=104857600   # 100MB for video
MAX_FILE_SIZE=104857600    # 100MB overall
```

### User Quotas
```env
GUEST_DAILY_LIMIT=3       # 3 translations per day
FREE_DAILY_LIMIT=10       # 10 translations per day
PREMIUM_DAILY_LIMIT=1000 # 1000 translations per day
```

## 📱 Integration with React Native

Your existing React Native app will work seamlessly:

```javascript
// Your existing api.ts will connect to:
const API_BASE_URL = 'http://localhost:8000/api/v1'

// Upload endpoint
POST /api/v1/translation/upload

// Status endpoint  
GET /api/v1/translation/{taskId}/status
```

The Python backend provides the same API contract that your React Native app expects.

## 🛠️ Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
pytest tests/test_main.py
```

### Code Quality
```bash
# Code formatting
black app/

# Type checking  
mypy app/

# Linting
flake8 app/
```

### Database Operations
```bash
# Create indexes for performance
python -m app.db.create_indexes

# Seed development data
python -m app.db.seed
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Build image
docker build -t ai-media-translation-backend .

# Run with environment file
docker run -p 8000:8000 --env-file .env ai-media-translation-backend
```

### Environment Setup
```bash
# Production environment variables
export NODE_ENV=production
export DEBUG=False
export MONGODB_URI=mongodb://your-production-db/ai_media_translation
export REDIS_URL=redis://your-production-redis:6379
```

## 🔍 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📊 Monitoring

### Health Endpoints
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health with statistics
curl http://localhost:8000/health/detailed

# Kubernetes probes
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

### Logging
```bash
# View logs
tail -f logs/app.log

# Error logs
tail -f logs/errors.log
```

## 🎯 Supported Formats

### Audio Files
- **MP3**: `audio/mpeg`
- **WAV**: `audio/wav`, `audio/x-wav`  
- **M4A**: `audio/mp4`
- **OGG**: `audio/ogg`
- **FLAC**: `audio/flac`
- **AAC**: `audio/aac`

### Video Files
- **MP4**: `video/mp4`
- **MOV**: `video/quicktime`
- **AVI**: `video/x-msvideo`
- **MKV**: `video/x-matroska`
- **WebM**: `video/webm`

## 🔐 Security Features

- **JWT Authentication**: Access + refresh tokens
- **Rate Limiting**: 100 requests per minute per IP
- **File Validation**: MIME type and size verification
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic model validation
- **Error Handling**: No sensitive data leakage

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**:
   - Install FFmpeg and ensure it's in PATH
   - Verify: `ffmpeg -version`

2. **MongoDB connection failed**:
   - Check MongoDB is running: `mongod --version`
   - Verify connection string in `.env`

3. **Redis connection failed**:
   - Check Redis is running: `redis-cli ping`
   - Verify Redis URL in `.env`

4. **OpenAI API errors**:
   - Verify API key is valid and active
   - Check rate limits: `curl -H "Authorization: Bearer $key" https://api.openai.com/v1/models`

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run.py
```

## 📈 Performance Optimization

### Database Indexes
- User queries: `openid`, `is_active`
- Job queries: `job_id`, `user + status`, `status + created_at`
- File queries: `file_name`, `uploaded_by + upload_date`

### Caching Strategy
- **Redis** for real-time progress tracking
- **User sessions** cached with 1-hour expiration
- **Translation results** cached for 24 hours

### Concurrency
- **Async FastAPI** for high throughput
- **Background tasks** for media processing
- **Connection pooling** for database efficiency

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Open Pull Request

## 📝 License

MIT License - see LICENSE file for details.