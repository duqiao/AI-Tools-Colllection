# Using Docker Desktop for MongoDB and Redis

## Docker Desktop Setup for Backend API

This guide shows how to set up MongoDB and Redis using Docker Desktop for your video/audio recognition backend.

## Prerequisites

1. **Install Docker Desktop**:
   - Download from [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Install and start Docker Desktop
   - Verify it's running: Docker Desktop icon in system tray

2. **System Requirements**:
   - Windows 10/11 Pro, Enterprise, or Education (Build 19044 or higher)
   - macOS 10.15 or newer
   - At least 4GB RAM
   - BIOS-level hardware virtualization enabled

## MongoDB Setup with Docker Desktop

### Option 1: Run MongoDB Container

```bash
# Pull MongoDB image
docker pull mongo:6.0

# Run MongoDB container
docker run --name ai-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=password123 \
  -e MONGO_INITDB_DATABASE=ai_media_translation \
  -v mongodb_data:/data/db \
  -d mongo:6.0
```

### Option 2: Use docker-compose (Recommended)

Create `docker-compose.yml` in your project root:

```yaml
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
      MONGO_INITDB_ROOT_PASSWORD: password123
      MONGO_INITDB_DATABASE: ai_media_translation
      MONGO_INITDB_ROOT_USER: root
    command: mongod --auth --bind_ip_all

  redis:
    image: redis:7-alpine
    container_name: ai-redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass redispwd123

volumes:
  mongodb_data:
    driver: local
  redis_data:
    driver: local
```

### Start Services:

```bash
# In your project root
docker-compose up -d

# Check if services are running
docker ps

# View logs
docker-compose logs mongodb
docker-compose logs redis
```

### MongoDB Connection String for Backend:

Update your `backend/.env` file:

```env
# MongoDB connection for Docker
MONGODB_URI=mongodb://admin:password123@localhost:27017/ai_media_translation?authSource=admin
```

## Redis Setup with Docker Desktop

### Option 1: Simple Redis Container

```bash
# Run Redis container
docker run --name ai-redis \
  -p 6379:6379 \
  -v redis_data:/data \
  -d redis:7-alpine \
  redis-server --appendonly yes --requirepass redispwd123
```

### Option 2: docker-compose (Already included above)

Redis is already included in the docker-compose.yml file above.

### Redis Connection String for Backend:

Update your `backend/.env` file to include Redis:

```env
# Redis connection for Docker
REDIS_URL=redis://:redispwd123@localhost:6379/0
```

## Docker Desktop GUI Management

### Access Docker Desktop Dashboard:

1. **Open Docker Desktop** application
2. **View Containers**: See running containers, resource usage
3. **View Volumes**: Manage persistent data volumes
4. **View Images**: Manage pulled Docker images
5. **View Resources**: Monitor CPU, memory, disk usage

## Container Management Commands

### Basic Operations:

```bash
# List all containers
docker ps -a

# Stop all containers
docker-compose down

# Stop specific container
docker stop ai-mongodb

# Start container
docker start ai-mongodb

# Remove container
docker rm ai-mongodb

# View container logs
docker logs ai-mongodb
docker-compose logs mongodb

# Access container shell
docker exec -it ai-mongodb /bin/bash
```

### Container Networking:

```bash
# Check container network
docker network ls

# Connect to container
docker exec -it ai-mongodb /bin/sh
docker exec -it ai-redis /bin/sh

# Test MongoDB connection from inside container
docker exec ai-mongodb mongosh --eval "db.runCommand('ping')"
```

## Update Backend Configuration

### Complete .env file example:

```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database Configuration (Docker)
MONGODB_URI=mongodb://admin:password123@localhost:27017/ai_media_translation?authSource=admin
REDIS_URL=redis://:redispwd123@localhost:6379/0

# Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-this-in-production

# File Upload
UPLOAD_DIR=./uploads
TEMP_DIR=./temp
MAX_FILE_SIZE=104857600

# Speech-to-Text
STT_PROVIDER=openai
WHISPER_MODEL=base
```

## Health Check Scripts

### Test MongoDB Connection:

```bash
# Test MongoDB connection
docker exec ai-mongodb mongosh --eval "
db = db.getSiblingDB('ai_media_translation');
try {
  db.runCommand({ping: 1});
  print('✅ MongoDB connection successful');
} catch (error) {
  print('❌ MongoDB connection failed:', error);
}
"
```

### Test Redis Connection:

```bash
# Test Redis connection
docker exec ai-redis redis-cli -a redispwd123 ping
```

## Development Workflow

### 1. Start Services:
```bash
# Start both services in background
docker-compose up -d

# Verify both are running
docker-compose ps
```

### 2. Start Backend:
```bash
# Activate virtual environment
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate

# Start the API server
python run.py
```

### 3. Test End-to-End:
```bash
# Run the test we created earlier
python test_simple.py

# Or run full E2E test
python test_e2e.py
```

## Production Considerations

### Security:
- **Change default passwords**: Don't use production deployments
- **Use environment variables**: Keep credentials out of code
- **Network isolation**: Use Docker networks for service isolation

### Persistence:
- **Named volumes**: All data persists in Docker volumes
- **Backup strategies**: Regular database dumps
- **Data migration**: Plan for data portability

### Performance:
- **Resource limits**: Configure container memory and CPU limits
- **Monitoring**: Use Docker Desktop monitoring tools
- **Optimization**: Tune MongoDB and Redis configurations

### Scaling:
- **Docker Swarm**: For multi-node deployments
- **Kubernetes**: For production scaling
- **Replication**: Consider MongoDB replica sets

## Troubleshooting

### Common Issues:

1. **Port conflicts**:
   ```bash
   # Kill processes using ports
   netstat -ano | findstr :27017
   netstat -ano | findstr :6379
   
   # Stop conflicting services
   docker stop $(docker ps -q)
   ```

2. **Container not starting**:
   ```bash
   # Check container logs
   docker-compose logs mongodb
   docker-compose logs redis
   
   # Check resource usage
   docker stats
   ```

3. **Connection refused**:
   - Verify Docker Desktop is running
   - Check firewall settings
   - Ensure containers are started: `docker ps`

4. **Data persistence issues**:
   - Check volume mounts: `docker volume ls`
   - Verify volume permissions
   - Check Docker Desktop shared drives settings

### Cleaning Up:

```bash
# Stop all services
docker-compose down

# Remove volumes (BE CAREFUL - DELETES DATA)
docker volume rm mongodb_data redis_data

# Remove containers
docker-compose rm -f

# Clean up unused images
docker image prune -f
```

## API Integration Examples

### Python Code Updates for Docker:

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # MongoDB Docker settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://admin:password123@localhost:27017/ai_media_translation")
    
    # Redis Docker settings  
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://:redispwd123@localhost:6379/0")
```

### Connection Testing:

```python
# Test database connectivity
import asyncio
from app.core.database import init_db, get_db
from app.core.redis import init_redis

async def test_docker_services():
    try:
        await init_db()
        print("✅ MongoDB connection successful")
        
        db = await get_db()
        collections = await db.list_collection_names()
        print(f"✅ Available collections: {collections}")
        
        await init_redis()
        print("✅ Redis connection successful")
        
    except Exception as e:
        print(f"❌ Service connection failed: {e}")
        return False
    
    return True
```

This Docker Desktop setup provides a complete, production-ready environment for your video/audio recognition backend!