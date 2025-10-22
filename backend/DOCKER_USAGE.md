# Docker Compose Usage Guide

## Quick Start Commands

### Development Environment (MongoDB + Redis)
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs mongodb
docker-compose logs redis
docker-compose logs backend

# Stop all services
docker-compose down

# Rebuild and start specific service
docker-compose up -d --build backend

# Scale services
docker-compose up -d --scale backend=2
```

### Production Environment (PostgreSQL)
```bash
# Set production environment
export DATABASE_TYPE=postgres
export NODE_ENV=production

# Start with PostgreSQL
docker-compose -f docker-compose.dev.yml --env-file .env.prod up -d postgres

# Or run only specific services
docker-compose -f docker-compose.dev.yml up -d postgres pgadmin
```

## Environment Configuration

### Switch Between Database Types
```bash
# Use MongoDB (default)
DATABASE_TYPE=mongodb
docker-compose -f docker-compose.dev.yml up -d

# Use PostgreSQL
DATABASE_TYPE=postgres
docker-compose -f docker-compose.dev.yml --env-file .env.prod up -d postgres

# Use Redis for caching (available with both)
REDIS_URL=redis://:dev123456@redis:6379/0
```

### Service Management

### View All Services
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs mongodb
docker-compose logs postgres
```

### Access Container Shells
```bash
# Access backend container
docker exec -it ai-backend-api sh

# Access MongoDB shell
docker exec -it ai-mongodb-dev mongosh

# Access PostgreSQL shell
docker exec -it ai-postgres-prod psql -U postgres -d ai_media_translation
```

### Monitor Resources
```bash
# View resource usage
docker stats

# Live monitoring with Docker Desktop
# Open Docker Desktop dashboard
```

## Health Checks

### Check Service Health
```bash
# Backend API
curl http://localhost:8000/health

# MongoDB
docker exec ai-mongodb-dev mongosh --eval "db.runCommand('ping')"

# PostgreSQL
docker exec ai-postgres-prod pg_isready -U postgres

# Redis
docker exec ai-redis-dev redis-cli -a dev123456 ping

# All services health check
docker-compose exec backend curl -f http://localhost:8000/health
```

### Database Management

### Access Database GUIs
```bash
# MongoDB Express (development)
open http://localhost:8081

# pgAdmin (production)
open http://localhost:5050

# Monitor with Grafana (if enabled)
open http://localhost:3000
```

## Development Workflow

### Local Development with Hot Reload
```bash
# Mount source code
docker-compose -f docker-compose.dev.yml \
  -v ./backend:/app \
  -v /backend/node_modules:/app/node_modules \
  backend \
  sh -c "npm install && npm run start:dev"
```

### Production Deployment
```bash
# Build and start
docker-compose -f docker-compose.dev.yml --env-file .env.prod up -d --build backend

# Scale application
docker-compose up -d --scale backend=3

# View production logs
docker-compose logs backend
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   # Kill processes using ports
   netstat -ano | findstr :8000
   netstat -ano | findstr :27017
   
   # Stop Docker services
   docker-compose down
   ```

2. **Permission Issues**:
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER ./uploads
   chmod -R 755 ./uploads
   
   # Fix PostgreSQL data permissions
   docker exec -it ai-postgres-prod chown postgres:postgres /var/lib/postgresql/data
   ```

3. **Connection Issues**:
   ```bash
   # Check network connectivity
   docker network ls
   
   # Test database connections
   docker exec backend python -c "
from app.core.database import init_db, get_db
import asyncio
async def test():
    try:
        await init_db()
        print('Database connection successful!')
    except Exception as e:
        print(f'Database connection failed: {e}')
asyncio.run(test())
"
   ```

### Cleaning Up

```bash
# Stop all services and remove volumes (DELETES DATA)
docker-compose down -v

# Remove Docker images
docker image prune -f

# Clean up Docker Desktop
docker system prune -f
```

This Docker setup provides complete containerization for your video/audio recognition backend with both development and production environments!