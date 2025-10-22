# Docker Production Deployment Guide

## Overview

This guide covers deploying the AI Media Translation backend using Docker Compose in production.

## Prerequisites

- Docker Desktop installed and running
- Sufficient system resources:
  - CPU: 4+ cores recommended
  - Memory: 8GB+ recommended
  - Storage: 50GB+ available
- Ollama installed locally for LLM services (if using local models)

## Environment Setup

### 1. Environment Variables

Create a `.env.production` file with your production configuration:

```bash
# Database Credentials
POSTGRES_PASSWORD=your-secure-postgres-password
REDIS_PASSWORD=your-secure-redis-password

# Security Secrets (generate strong random strings)
JWT_SECRET=your-super-secure-jwt-secret-key-here
JWT_REFRESH_SECRET=your-super-secure-refresh-secret-key-here

# API Configuration
CORS_ORIGINS=["https://your-domain.com", "https://app.your-domain.com"]

# Ollama Configuration (if using local LLM)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=deepseek-coder:6.7b-instruct

# Performance Settings
MAX_CONCURRENT_JOBS=100
PROCESSING_TIMEOUT=3600
DB_POOL_SIZE=20

# Monitoring
GRAFANA_USER=admin
GRAFANA_PASSWORD=your-secure-grafana-password
GRAFANA_URL=https://monitoring.your-domain.com

# Logging
LOG_LEVEL=warn
```

### 2. SSL/TLS Configuration (Optional)

For production with SSL, you'll need to:
1. Obtain SSL certificates
2. Configure reverse proxy (nginx/traefik)
3. Update CORS origins to use HTTPS

## Deployment Steps

### 1. Start Database Services

```bash
# Start databases first
docker-compose -f docker-compose.prod.yml up -d postgres redis

# Wait for databases to be healthy
docker-compose -f docker-compose.prod.yml ps
```

### 2. Start Backend Service

```bash
# Build and start backend
docker-compose -f docker-compose.prod.yml up -d --build backend

# Check backend logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 3. Start Monitoring (Optional)

```bash
# Start monitoring services
docker-compose -f docker-compose.prod.yml up -d grafana prometheus

# Access monitoring dashboards
# Grafana: http://localhost:3001
# Prometheus: http://localhost:9091
```

### 4. Verify Deployment

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test API health
curl http://localhost:8000/health

# Test database connectivity
docker-compose -f docker-compose.prod.yml exec backend python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
print('Database connectivity: OK')
"
```

## Production Configuration

### Backend Optimization

The production configuration includes:

- **Database**: PostgreSQL with optimized settings
- **Caching**: Redis with memory limits and eviction policy
- **Security**: Strong passwords, secrets management
- **Performance**: Resource limits, connection pooling
- **Monitoring**: Grafana + Prometheus for observability
- **Logging**: Structured logging with configurable levels

### Resource Allocation

```yaml
# Backend service limits
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Database Configuration

PostgreSQL is configured for production with:
- Connection limit: 200
- Shared buffers: 256MB
- Effective cache size: 1GB
- Logging disabled for performance (can be enabled)

### Redis Configuration

Redis is optimized for production with:
- Max memory: 512MB
- Eviction policy: LRU
- Append-only file persistence
- Password authentication

## Monitoring Setup

### Grafana Dashboards

1. Access Grafana: `http://localhost:3001`
2. Login with configured credentials
3. Add Prometheus data source
4. Import dashboard templates

### Key Metrics to Monitor

- **API Response Times**: Track performance
- **Database Connections**: Monitor pool usage
- **Memory Usage**: Prevent OOM issues
- **CPU Usage**: Ensure adequate resources
- **Error Rates**: Track application health

### Alerting Setup

Configure Prometheus alerts for:
- High error rates (>5%)
- Slow response times (>2s)
- Database connection failures
- High memory usage (>80%)

## Maintenance

### Updates

```bash
# Update services
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --force-recreate

# Backup data before major updates
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres ai_media_translation > backup.sql
```

### Backup Strategy

1. **Database Backup**:
   ```bash
   # Automated backup script
   docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres ai_media_translation > "backup_$(date +%Y%m%d).sql"
   ```

2. **Volume Backup**:
   ```bash
   # Backup Docker volumes
   docker run --rm -v ai-tools-colllection_postgres_prod_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
   ```

### Scaling

```bash
# Scale backend service
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Add load balancer for multiple instances
```

## Security Considerations

1. **Network Security**:
   - Use internal Docker networks
   - Don't expose database ports publicly
   - Configure firewall rules

2. **Secrets Management**:
   - Use strong passwords
   - Rotate secrets regularly
   - Consider using Docker secrets or HashiCorp Vault

3. **API Security**:
   - Enable rate limiting
   - Use HTTPS in production
   - Validate all inputs
   - Implement proper authentication

4. **Container Security**:
   - Use non-root users
   - Keep images updated
   - Scan for vulnerabilities
   - Use resource limits

## Troubleshooting

### Common Issues

1. **Database Connection Failures**:
   ```bash
   # Check database health
   docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs postgres
   ```

2. **Backend Health Issues**:
   ```bash
   # Check backend logs
   docker-compose -f docker-compose.prod.yml logs -f backend
   
   # Restart service
   docker-compose -f docker-compose.prod.yml restart backend
   ```

3. **Performance Issues**:
   ```bash
   # Check resource usage
   docker stats
   
   # Monitor connections
   docker-compose -f docker-compose.prod.yml exec backend python -c "
   import asyncio
   from app.core.redis import redis_client
   print('Redis info:', asyncio.run(redis_client.info()))
   "
   ```

### Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Remove volumes (deletes data!)
docker-compose -f docker-compose.prod.yml down -v

# Clean up unused images
docker system prune -f
```

## Support

For issues or questions:
1. Check service logs: `docker-compose logs [service]`
2. Verify resource usage: `docker stats`
3. Test connectivity: `curl http://localhost:8000/health`
4. Review monitoring dashboards

This deployment provides a production-ready environment for your video/audio recognition backend!