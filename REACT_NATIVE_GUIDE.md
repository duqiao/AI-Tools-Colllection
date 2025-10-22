# React Native Frontend Development Guide

## Quick Start

### Prerequisites
- Node.js 18+ installed
- Expo CLI installed (`npm install -g expo-cli`)
- Expo Go app on your mobile device
- Backend API running on `http://127.0.0.1:8001`

### Starting the Frontend

```bash
cd react-native-app
npm install
npm start
```

This will start the Expo development server and display a QR code.

### Running on Different Platforms

```bash
# Start with web browser (for development testing)
npm run start

# Start for iOS simulator  
npm run ios

# Start for Android emulator
npm run android

# Start for web (browser testing)
npm run web
```

## Integration Testing Setup

### Step 1: Start Backend Services

```bash
# Option A: Manual setup
docker-compose -f docker-compose.dev.yml up -d mongodb redis
cd backend
python run.py

# Option B: Automated setup
python integration_test_env.py
```

### Step 2: Start Frontend

```bash
cd react-native-app
npm start
```

### Step 3: Test Integration

1. **Open Expo Go** on your mobile device
2. **Scan the QR code** shown in the terminal
3. **Allow camera permissions** (for file upload)
4. **Test features**:
   - File upload (audio/video)
   - Translation processing
   - User authentication
   - History viewing

## Key Features Testing

### 1. File Upload Testing
- **Supported Formats**: MP3, WAV, M4A, MP4, MOV, AVI
- **Max File Size**: 100MB (video), 50MB (audio)
- **Test Files**: 
  - Audio: Short MP3/WAV files (1-10MB)
  - Video: Short MP4 files (5-50MB)

### 2. API Integration Testing
- **Base URL**: `http://127.0.0.1:8001/api/v1`
- **Health Check**: Available at `/health`
- **API Documentation**: Available at `/docs`

### 3. Authentication Testing
- Guest mode (3 uploads per day)
- User registration/login
- JWT token handling
- Session management

## Development Configuration

### Environment Configuration

The app automatically uses different configurations based on `__DEV__` flag:

```javascript
// Development
const API_BASE_URL = 'http://127.0.0.1:8001/api/v1'

// Production  
const API_BASE_URL = 'https://your-api-domain.com/api/v1'
```

### Network Configuration

For testing on physical devices, ensure your device and computer are on the same network. Update the API URL in `src/services/api.ts`:

```javascript
// Replace with your computer's IP address
const API_BASE_URL = 'http://192.168.1.100:8001/api/v1';
```

## Testing Commands

### Unit Tests
```bash
cd react-native-app
npm test
```

### Linting
```bash
npm run lint
npm run lint:fix
```

### Type Checking
```bash
npm run type-check
```

### Code Formatting
```bash
npm run format
```

## Component Testing

### Key Components to Test

1. **FileUploader Component**
   - File selection
   - Progress tracking
   - Error handling

2. **TranslationScreen**
   - Upload workflow
   - Status updates
   - Results display

3. **HistoryScreen**
   - Translation history
   - Delete functionality
   - Pagination

4. **Auth Components**
   - Login/registration
   - Guest mode
   - Token refresh

## Integration Testing Scripts

### 1. Automated Integration Testing
```bash
# Run comprehensive integration tests
python test_integration.py
```

### 2. Environment Setup
```bash
# Setup complete development environment
python integration_test_env.py
```

## Debugging

### Backend Debugging
- Backend logs: Check terminal where backend is running
- API testing: Use `http://127.0.0.1:8001/docs`
- Database status: Check Docker containers

### Frontend Debugging
- Expo DevTools: Open in browser during development
- React Native Debugger: Use for detailed debugging
- Network tab: Monitor API calls in browser DevTools

### Common Issues

1. **Network Connection Errors**:
   - Ensure backend is running on correct port (8001)
   - Check firewall settings
   - Verify same network for device testing

2. **CORS Issues**:
   - Backend should allow frontend origin
   - Check CORS middleware configuration

3. **File Upload Issues**:
   - Check file size limits
   - Verify supported formats
   - Ensure proper permissions

## Performance Testing

### Load Testing
```bash
# Test API with multiple concurrent requests
python -c "
import requests
import threading
import time

def test_api():
    try:
        response = requests.get('http://127.0.0.1:8001/health')
        print(f'Status: {response.status_code}')
    except Exception as e:
        print(f'Error: {e}')

# Run 10 concurrent tests
threads = []
for _ in range(10):
    thread = threading.Thread(target=test_api)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
"
```

### Memory Testing
Monitor resource usage during testing:
```bash
# Backend memory
docker stats ai-mongodb-dev ai-redis-dev

# System resources
tasklist | grep python
```

## Production Deployment

### Building for Production
```bash
# Android
cd react-native-app
expo build:android

# iOS
expo build:ios
```

### Environment Variables
Set production variables in `.env`:
```bash
API_BASE_URL=https://your-api-domain.com/api/v1
ENVIRONMENT=production
```

## Troubleshooting Guide

### Frontend Issues
1. **Metro bundler issues**: Clear cache with `expo r -c`
2. **Dependency conflicts**: Delete `node_modules` and reinstall
3. **Platform-specific issues**: Test on multiple platforms

### Backend Issues  
1. **Database connection**: Check Docker containers are running
2. **Port conflicts**: Ensure no other services on port 8001
3. **CORS errors**: Verify CORS middleware configuration

### Integration Issues
1. **Network connectivity**: Ping backend from frontend device
2. **API version mismatch**: Ensure frontend uses correct API version
3. **Authentication**: Check JWT token handling

This comprehensive setup ensures smooth integration testing between your React Native frontend and FastAPI backend!