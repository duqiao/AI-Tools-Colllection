# MongoDB Setup Guide for Backend API

## Problem: MongoDB Connection Failed

**Error**: `WinError 10061` - Target computer actively refused connection
**Cause**: MongoDB service is not running on localhost:27017

## Solution Options

### Option 1: Install and Run MongoDB Locally (Recommended for Development)

#### Windows Installation:

```powershell
# Method 1: Using Chocolate (Recommended)
choco install mongodb

# Method 2: Download directly
winget install MongoDB
```

#### Start MongoDB Service:

```powershell
# Start MongoDB as a service
net start MongoDB

# Or run in standalone mode
mongod --dbpath "C:\data\db" --logpath "C:\data\log\mongod.log"
```

### Option 2: Use MongoDB Atlas (Cloud - Easier Setup)

#### Steps:
1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster
3. Get your connection string
4. Update your `.env` file:

```env
# Replace with your MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/ai_media_translation
```

### Option 3: Run MongoDB with Docker (Recommended for Consistency)

```dockerfile
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    container_name: ai-mongodb
    restart: always
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: ai_media_translation
```

```powershell
# Start with Docker
docker-compose up -d
```

## Verify Installation

### Check if MongoDB is Running:

```powershell
# Check MongoDB service status
netstat -an | findstr "27017"

# Or test with MongoDB CLI
mongosh --eval "db.runCommand({ping: 1})"

# Or test with Python
python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    print('✅ MongoDB connection successful!')
except Exception as e:
    print(f'❌ MongoDB connection failed: {e}')
"
```

## Configuration Updates

### Update Backend Configuration:

1. **Install MongoDB Python Driver** (if not already installed):
```powershell
pip install pymongo motor
```

2. **Verify Environment Variables** (in `backend/.env`):
```env
MONGODB_URI=mongodb://localhost:27017/ai_media_translation
```

### Test Backend After MongoDB Setup:

```powershell
# Test database connection
python -c "
from app.core.database import init_db
import asyncio
async def test():
    try:
        await init_db()
        print('✅ Database initialization successful!')
    except Exception as e:
        print(f'❌ Database initialization failed: {e}')
asyncio.run(test())
"

# Start your backend server
python run.py
```

## Quick Fix Steps

1. **Choose Setup Method**: MongoDB Atlas (easiest) OR Local MongoDB OR Docker
2. **Start MongoDB Service**: Following instructions above
3. **Verify Connection**: Use test commands to confirm MongoDB is accessible
4. **Restart Backend**: `python run.py` to connect to the database

## MongoDB Commands Reference

```bash
# Basic MongoDB commands
mongosh                          # Start MongoDB shell
mongosh --host localhost --port 27017
mongosh mongodb://user:password@localhost/ai_media_translation

# Database operations
db                            # Show current database
show collections              # List all collections
db.media_files.find()         # Query documents
db.media_files.createIndex({field: 1})  # Create index
```

## Troubleshooting

### Common Issues:

1. **Port 27017 is in use**:
   - Stop other MongoDB instances: `net stop MongoDB`
   - Kill process: `taskkill /F /IM mongod.exe`

2. **Windows Firewall blocking**:
   - Add exception for MongoDB in Windows Firewall
   - Check antivirus software is not blocking MongoDB

3. **Data directory permissions**:
   - Ensure MongoDB has write permissions to data directory
   - Run with administrator privileges if needed

4. **Corrupted MongoDB installation**:
   - Uninstall MongoDB completely
   - Reinstall using installer from MongoDB website

## Production Considerations

- **Security**: Enable authentication for production environments
- **Backup**: Set up regular database backups
- **Monitoring**: Use MongoDB Atlas monitoring or MongoDB Compass
- **Replication**: Consider replica sets for high availability

## Next Steps After Fix

Once MongoDB is running:

1. **Test Backend Health**: Visit `http://localhost:8000/health`
2. **Test File Upload**: Use the test scripts we created earlier
3. **Verify Database**: Check that uploaded files are stored correctly
4. **Test Transcription**: Verify OpenAI Whisper integration works

Choose the setup method that works best for your development environment and follow the steps above!