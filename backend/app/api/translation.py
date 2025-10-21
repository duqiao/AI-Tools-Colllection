from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import asyncio

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_progress, delete_progress
from app.models.schemas import (
    ProcessingJob, ProcessingJobResponse, ProgressResponse, 
    JobStatus, ProcessingStage
)
from app.api.dependencies import get_current_user
from app.services.media_processor import MediaProcessor

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
        # Find processing job
        collection = await get_collection("processing_jobs")
        job = await collection.find_one({
            "job_id": task_id,
            "user": current_user["id"]
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if job["status"] != JobStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Task already {job['status']}"
            )
        
        # Update job with translation settings
        await collection.update_one(
            {"_id": job["_id"]},
            {
                "$set": {
                    "source_language": request.source_language,
                    "target_language": request.target_language,
                    "status": JobStatus.PROCESSING,
                    "started_at": asyncio.get_event_loop().time(),
                    "progress": 10,
                    "current_stage": ProcessingStage.EXTRACTING_AUDIO,
                    "updated_at": asyncio.get_event_loop().time()
                }
            }
        )
        
        # Set initial progress in Redis
        progress_data = {
            "task_id": task_id,
            "file_name": job.get("file_name", "Unknown"),
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
        
        return ProcessingJobResponse(
            id=str(job["_id"]),
            job_id=task_id,
            status=JobStatus.PROCESSING,
            progress=10,
            current_stage=ProcessingStage.EXTRACTING_AUDIO,
            source_language=request.source_language,
            target_language=request.target_language,
            started_at=job.get("started_at"),
            completed_at=job.get("completed_at")
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
        
        # If not in Redis, get from database
        collection = await get_collection("processing_jobs")
        job = await collection.find_one({
            "job_id": task_id,
            "user": current_user["id"]
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        progress_response = ProgressResponse(
            task_id=task_id,
            file_name=job.get("file_name", "Unknown"),
            status=job["status"],
            progress=job["progress"],
            stage=job["current_stage"],
            message=job.get("error", {}).get("message"),
            start_time=int(job["started_at"].timestamp() * 1000) if job.get("started_at") else None,
            estimated_time_remaining=job.get("estimated_time_remaining"),
            result=job.get("result"),
            error=job.get("error", {}).get("message")
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
        collection = await get_collection("processing_jobs")
        
        # Find and update job
        job = await collection.find_one_and_update({
            "job_id": task_id,
            "user": current_user["id"],
            "status": {"$in": [JobStatus.PENDING, JobStatus.PROCESSING]}
        }, {
            "$set": {
                "status": JobStatus.CANCELLED,
                "completed_at": asyncio.get_event_loop().time(),
                "updated_at": asyncio.get_event_loop().time()
            }
        })
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Task not found or cannot be cancelled"
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
        
        skip = (page - 1) * per_page
        
        # Get jobs with media files info
        collection = await get_collection("processing_jobs")
        pipeline = [
            {
                "$match": {"user": current_user["id"]}
            },
            {
                "$lookup": {
                    "from": "media_files",
                    "localField": "media_file",
                    "foreignField": "_id",
                    "as": "media_file_info"
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$skip": skip
            },
            {
                "$limit": per_page
            }
        ]
        
        jobs = await collection.aggregate(pipeline).to_list(None)
        total = await collection.count_documents({"user": current_user["id"]})
        
        # Format response
        items = []
        for job in jobs:
            media_info = job.get("media_file_info", [{}])[0]
            items.append({
                "id": job["_id"],
                "fileName": media_info.get("original_name", "Unknown"),
                "fileType": media_info.get("file_type", "unknown"),
                "fileSize": media_info.get("file_size", 0),
                "uploadDate": media_info.get("upload_date", job["created_at"]),
                "status": job["status"],
                "progress": job["progress"],
                "sourceLanguage": job["source_language"],
                "targetLanguage": job["target_language"],
                "result": job.get("result"),
                "error": job.get("error", {}).get("message")
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
        
        # Update job with error
        collection = await get_collection("processing_jobs")
        await collection.update_one(
            {"job_id": task_id},
            {
                "$set": {
                    "status": JobStatus.FAILED,
                    "error": {
                        "code": "PROCESSING_ERROR",
                        "message": str(e)
                    },
                    "completed_at": asyncio.get_event_loop().time(),
                    "updated_at": asyncio.get_event_loop().time()
                }
            }
        )
        
        # Update Redis progress with error
        error_progress = {
            "task_id": task_id,
            "status": JobStatus.FAILED,
            "progress": 0,
            "stage": "processing_failed",
            "error": str(e)
        }
        await set_progress(task_id, error_progress)