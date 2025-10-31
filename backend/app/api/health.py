from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.postgres_db import get_db
from app.core.redis import get_redis
from app.models.schemas import JobStatus
from app.repositories.user_repository import UserRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.job_repository import ProcessingJobRepository

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "success": True,
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.DEBUG and "development" or "production",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system statistics"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime": asyncio.get_event_loop().time(),
            "environment": settings.DEBUG and "development" or "production",
            "version": "1.0.0",
            "services": {
                "database": "checking...",
                "redis": "checking...",
                "file_system": "checking...",
                "stt_service": "configured",
                "translation_service": "configured"
            }
        }
        
        # Check PostgreSQL database connection
        try:
            database = await get_db()
            # Simple connection test with PostgreSQL
            async with database.get_connection() as conn:
                await conn.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
            health_status["database_type"] = "PostgreSQL"
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check Redis connection
        try:
            redis_client = await get_redis()
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Check file system
        try:
            from pathlib import Path
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            health_status["services"]["file_system"] = "healthy"
        except Exception as e:
            logger.error(f"File system health check failed: {e}")
            health_status["services"]["file_system"] = "unhealthy"
            health_status["status"] = "degraded"
        
        # Get system statistics using PostgreSQL repositories
        try:
            async with ProcessingJobRepository() as job_repo:
                total_jobs = await job_repo.count_total()
                pending_jobs = await job_repo.count_by_status("pending")
                processing_jobs = await job_repo.count_by_status("processing")
                completed_jobs = await job_repo.count_by_status("completed")
                failed_jobs = await job_repo.count_by_status("failed")
            
            async with UserRepository() as user_repo:
                total_users = await user_repo.count_total()
                active_users = await user_repo.count_active_users()
            
            async with MediaRepository() as media_repo:
                total_media = await media_repo.count_total()
                # Count by MIME type pattern
                audio_files = await media_repo.count_by_mime_type("audio%")
                video_files = await media_repo.count_by_mime_type("video%")
            
            health_status["statistics"] = {
                "jobs": {
                    "total": total_jobs,
                    "pending": pending_jobs,
                    "processing": processing_jobs,
                    "completed": completed_jobs,
                    "failed": failed_jobs
                },
                "users": {
                    "total": total_users,
                    "active": active_users
                },
                "media_files": {
                    "total": total_media,
                    "audio": audio_files,
                    "video": video_files
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            health_status["statistics"] = None
        
        # Configuration information
        health_status["configuration"] = {
            "database_type": "PostgreSQL",
            "stt_provider": getattr(settings, 'STT_PROVIDER', 'openai'),
            "translation_provider": getattr(settings, 'TRANSLATION_PROVIDER', 'openai'),
            "max_file_size": getattr(settings, 'MAX_FILE_SIZE', 100 * 1024 * 1024),
            "upload_dir": settings.UPLOAD_DIR,
            "postgres_host": settings.POSTGRES_HOST,
            "postgres_port": settings.POSTGRES_PORT,
            "postgres_db": settings.POSTGRES_DB
        }
        
        return {
            "success": health_status["status"] == "healthy",
            "data": health_status
        }
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "success": False,
            "error": "Health check failed",
            "data": {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        }

@router.get("/ready")
async def readiness_check():
    """Readiness check for container orchestration"""
    try:
        # Check if all critical services are ready
        database = await get_db()
        # Test PostgreSQL connection
        async with database.get_connection() as conn:
            await conn.execute("SELECT 1")
        
        redis_client = await get_redis()
        await redis_client.ping()
        
        from pathlib import Path
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "success": True,
            "message": "Service is ready",
            "database": "PostgreSQL"
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "success": False,
            "error": "Service is not ready",
            "message": str(e)
        }

@router.get("/live")
async def liveness_check():
    """Liveness check - if we can respond, we're alive"""
    return {
        "success": True,
        "message": "Service is alive"
    }