from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.redis import set_progress, delete_progress
from app.models.schemas import (
    ProcessingJob, ProcessingJobResponse, ProgressResponse, 
    JobStatus, ProcessingStage
)
from app.api.dependencies import get_current_user
from app.services.media_processor import MediaProcessor
from app.repositories.job_repository import ProcessingJobRepository

logger = logging.getLogger(__name__)
router = APIRouter()

class TranslationStartRequest(BaseModel):
    source_language: Optional[str] = "auto"
    target_language: str = "zh"

@router.post("/{task_id}/start", response_model=ProcessingJobResponse)
async def start_translation(
    task_id: str,
    request: TranslationStartRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Start translation processing for uploaded file"""
    try:
        # Find processing job using PostgreSQL
        async with ProcessingJobRepository() as job_repo:
            job = await job_repo.get_by_job_id_and_user(task_id, current_user["id"])
        
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        current_status = job.get("processing", {}).get("status", "pending")
        if current_status != JobStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Task already {current_status}"
            )
        
        # Update job with translation settings using PostgreSQL
        async with ProcessingJobRepository() as job_repo:
            # Update job data
            update_data = {
                "processing": {
                    "status": JobStatus.PROCESSING,
                    "progress": 10,
                    "startedAt": datetime.utcnow(),
                    "currentStage": ProcessingStage.EXTRACTING_AUDIO,
                    "completedAt": None,
                    "error": None
                },
                "job": {
                    **job.get("job", {}),
                    "settings": {
                        **job.get("job", {}).get("settings", {}),
                        "source_language": request.source_language,
                        "target_language": request.target_language
                    }
                }
            }
            await job_repo.update(job["id"], update_data)
        
        # Set initial progress in Redis
        progress_data = {
            "task_id": task_id,
            "file_name": job.get("fileName", "Unknown"),
            "status": JobStatus.PROCESSING,
            "progress": 10,
            "stage": ProcessingStage.EXTRACTING_AUDIO,
            "message": "开始处理...",
            "start_time": int(asyncio.get_event_loop().time() * 1000)
        }
        await set_progress(task_id, progress_data)
        
        # Start processing in background
        background_tasks.add_task(
            process_translation_task,
            task_id,
            current_user["id"]
        )
        
        logger.info(f"Translation started for task: {task_id}", extra={
            "user_id": current_user["id"],
            "source_language": request.source_language,
            "target_language": request.target_language
        })
        
        # Get updated job for response
        async with ProcessingJobRepository() as job_repo:
            updated_job = await job_repo.get_by_id(job["id"])
        
        return ProcessingJobResponse(
            id=str(updated_job["id"]),
            job_id=task_id,
            status=JobStatus.PROCESSING,
            progress=10,
            current_stage=ProcessingStage.EXTRACTING_AUDIO,
            source_language=request.source_language,
            target_language=request.target_language,
            started_at=updated_job.get("processing", {}).get("startedAt"),
            completed_at=updated_job.get("processing", {}).get("completedAt")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start translation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start translation")

@router.get("/{task_id}/status", response_model=ProgressResponse)
async def get_translation_status(task_id: str, current_user = Depends(get_current_user)):
    """Get translation status"""
    try:
        # Try to get from Redis first (real-time progress)
        progress_data = await get_progress(task_id)
        if progress_data:
            return ProgressResponse(**progress_data)
        
        # If not in Redis, get from PostgreSQL database
        async with ProcessingJobRepository() as job_repo:
            job = await job_repo.get_by_job_id_and_user(task_id, current_user["id"])
        
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        processing = job.get("processing", {})
        
        progress_response = ProgressResponse(
            task_id=task_id,
            file_name=job.get("fileName", "Unknown"),
            status=processing.get("status", "pending"),
            progress=processing.get("progress", 0),
            stage=processing.get("currentStage", "queued"),
            message=processing.get("error", {}).get("message"),
            start_time=int(processing.get("startedAt").timestamp() * 1000) if processing.get("startedAt") else None,
            estimated_time_remaining=processing.get("estimatedTimeRemaining"),
            result=job.get("result"),
            error=processing.get("error", {}).get("message") if processing.get("error") else None
        )
        
        return progress_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get translation status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get translation status")

@router.delete("/{task_id}")
async def cancel_translation(task_id: str, current_user = Depends(get_current_user)):
    """Cancel translation processing"""
    try:
        # Find and update job using PostgreSQL
        async with ProcessingJobRepository() as job_repo:
            job = await job_repo.get_by_job_id_and_user(task_id, current_user["id"])
            
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )
            
            current_status = job.get("processing", {}).get("status", "pending")
            if current_status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
                raise HTTPException(
                    status_code=400,
                    detail="Task cannot be cancelled"
                )
            
            # Update job to cancelled
            update_data = {
                "processing": {
                    "status": JobStatus.CANCELLED,
                    "progress": job.get("processing", {}).get("progress", 0),
                    "startedAt": job.get("processing", {}).get("startedAt"),
                    "completedAt": datetime.utcnow(),
                    "error": None
                }
            }
            
            success = await job_repo.update(job["id"], update_data)
            if not success:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update job"
                )
        
        # Remove from Redis
        await delete_progress(task_id)
        
        logger.info(f"Translation cancelled: {task_id}", extra={
            "user_id": current_user["id"]
        })
        
        return {
            "success": True,
            "data": {
                "task_id": task_id,
                "status": JobStatus.CANCELLED,
                "message": "Translation cancelled successfully"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel translation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel translation")

@router.get("/history")
async def get_translation_history(
    page: int = 1,
    per_page: int = 20,
    current_user = Depends(get_current_user)
):
    """Get translation history"""
    try:
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        offset = (page - 1) * per_page
        
        # Get jobs using PostgreSQL repository
        async with ProcessingJobRepository() as job_repo:
            jobs = await job_repo.get_by_user(current_user["id"], per_page, offset)
            total = await job_repo.count_by_user(current_user["id"])
        
        # Format response
        items = []
        for job in jobs:
            processing = job.get("processing", {})
            job_settings = job.get("job", {}).get("settings", {})
            
            items.append({
                "id": job["id"],
                "fileName": job.get("fileName", "Unknown"),
                "fileType": job.get("fileType", "unknown"),
                "fileSize": job.get("fileSize", 0),
                "uploadDate": job.get("createdAt", datetime.utcnow()),
                "status": processing.get("status", "pending"),
                "progress": processing.get("progress", 0),
                "sourceLanguage": job_settings.get("source_language", "auto"),
                "targetLanguage": job_settings.get("target_language", "zh"),
                "result": job.get("result"),
                "error": processing.get("error", {}).get("message") if processing.get("error") else None
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "pages": (total + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        logger.error(f"Get translation history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get translation history")

async def get_progress(task_id: str):
    """Helper function to get progress from Redis"""
    try:
        from app.core.redis import get_progress as redis_get_progress
        return await redis_get_progress(task_id)
    except:
        return None

async def process_translation_task(task_id: str, user_id: str):
    """Background task to process translation"""
    try:
        logger.info(f"Starting background processing for task: {task_id}")
        
        # Initialize MediaProcessor
        media_processor = MediaProcessor()
        
        # Process the translation
        await media_processor.process_translation(task_id, user_id)
        
        logger.info(f"Background processing completed for task: {task_id}")
        
    except Exception as e:
        logger.error(f"Background processing error for task {task_id}: {e}", exc_info=True)
        
        # Update job with error using PostgreSQL
        try:
            async with ProcessingJobRepository() as job_repo:
                job = await job_repo.get_by_job_id_field(task_id)
                if job:
                    update_data = {
                        "processing": {
                            "status": JobStatus.FAILED,
                            "progress": job.get("processing", {}).get("progress", 0),
                            "startedAt": job.get("processing", {}).get("startedAt"),
                            "completedAt": datetime.utcnow(),
                            "error": {
                                "code": "PROCESSING_ERROR",
                                "message": str(e)
                            }
                        }
                    }
                    await job_repo.update(job["id"], update_data)
        except Exception as update_error:
            logger.error(f"Failed to update job with error: {update_error}")
        
        # Update Redis progress with error
        error_progress = {
            "task_id": task_id,
            "status": JobStatus.FAILED,
            "progress": 0,
            "stage": "processing_failed",
            "error": str(e)
        }
        await set_progress(task_id, error_progress)