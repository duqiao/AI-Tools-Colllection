from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db, get_collection
from app.core.redis import get_redis
from app.models.schemas import JobStatus

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
        
        # Check database connection
        try:
            database = await get_db()
            await database.command("ping")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
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
        
        # Get system statistics
        try:
            jobs_collection = await get_collection("processing_jobs")
            users_collection = await get_collection("users")
            media_collection = await get_collection("media_files")
            
            total_jobs = await jobs_collection.count_documents({})
            pending_jobs = await jobs_collection.count_documents({"processing.status": JobStatus.PENDING})
            processing_jobs = await jobs_collection.count_documents({"processing.status": JobStatus.PROCESSING})
            completed_jobs = await jobs_collection.count_documents({"processing.status": JobStatus.COMPLETED})
            failed_jobs = await jobs_collection.count_documents({"processing.status": JobStatus.FAILED})
            
            total_users = await users_collection.count_documents({})
            active_users = await users_collection.count_documents({"is_active": True})
            
            total_media = await media_collection.count_documents({})
            # Note: Media files don't have explicit file_type field, infer from MIME type
            audio_files = await media_collection.count_documents({"mimeType": {"$regex": "^audio/"}})
            video_files = await media_collection.count_documents({"mimeType": {"$regex": "^video/"}})
            
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
            "stt_provider": settings.STT_PROVIDER,
            "translation_provider": settings.TRANSLATION_PROVIDER,
            "max_file_size": settings.MAX_FILE_SIZE,
            "upload_dir": settings.UPLOAD_DIR,
            "max_concurrent_jobs": settings.MAX_CONCURRENT_JOBS
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
        await database.command("ping")
        
        redis_client = await get_redis()
        await redis_client.ping()
        
        from pathlib import Path
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "success": True,
            "message": "Service is ready"
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