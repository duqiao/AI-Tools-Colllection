from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import uuid
import aiofiles
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_progress, delete_progress
from app.models.schemas import (
    MediaFile, ProcessingJob, ProcessingJobCreate, 
    UploadResponse, ProgressResponse, JobStatus
)
from app.api.dependencies import get_current_user, get_user_by_id
from app.services.media_processor import MediaProcessor
from app.utils.file_utils import (
    validate_file_type, get_file_type, 
    get_file_size_formatted, generate_unique_filename
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=UploadResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    file_type: Optional[str] = Form(None),
    original_filename: Optional[str] = Form(None),
    file_size: Optional[str] = Form(None),
    current_user = Depends(get_current_user)
):
    """Upload audio or video file for processing"""
    try:
        # Validate file
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type is required")
        
        if not validate_file_type(file.content_type):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Check file size
        actual_file_size = await get_file_size(file)
        file_type_enum = get_file_type(file.content_type)
        max_size = settings.MAX_AUDIO_SIZE if file_type_enum == "audio" else settings.MAX_VIDEO_SIZE
        
        if actual_file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size for {file_type_enum} is {get_file_size_formatted(max_size)}"
            )
        
        # Generate unique filename
        unique_filename = generate_unique_filename(file.filename or "upload")
        file_path = Path(settings.UPLOAD_DIR) / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create media file record
        media_file_data = {
            "original_name": original_filename or file.filename,
            "file_name": unique_filename,
            "file_path": str(file_path),
            "file_size": actual_file_size,
            "mime_type": file.content_type,
            "file_type": file_type_enum,
            "uploaded_by": current_user["id"]
        }
        
        collection = await get_collection("media_files")
        result = await collection.insert_one(media_file_data)
        
        # Generate task ID for React Native app compatibility
        task_id = str(result.inserted_id)
        
        logger.info(f"File uploaded successfully: {unique_filename}", extra={
            "user_id": current_user["id"],
            "file_size": actual_file_size,
            "file_type": file_type_enum
        })
        
        return UploadResponse(
            file_id=str(result.inserted_id),
            file_name=unique_filename,
            original_name=original_filename or file.filename,
            file_size=actual_file_size,
            file_type=file_type_enum,
            mime_type=file.content_type,
            upload_date=media_file_data["created_at"],
            task_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/{job_id}/status", response_model=ProgressResponse)
async def get_upload_status(job_id: str, current_user = Depends(get_current_user)):
    """Get upload/processing status"""
    try:
        # Try to get from Redis first (real-time progress)
        progress_data = await get_progress(job_id)
        if progress_data:
            return ProgressResponse(**progress_data)
        
        # If not in Redis, get from database
        collection = await get_collection("processing_jobs")
        job = await collection.find_one({
            "job_id": job_id,
            "user": current_user["id"]
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get media file name
        media_collection = await get_collection("media_files")
        media_file = await media_collection.find_one({"_id": job["media_file"]})
        
        progress_response = ProgressResponse(
            task_id=job_id,
            file_name=media_file["original_name"] if media_file else "Unknown",
            status=job["status"],
            progress=job["progress"],
            stage=job["current_stage"],
            message=job["error"]["message"] if job.get("error") else None,
            start_time=int(job["started_at"].timestamp() * 1000) if job.get("started_at") else None,
            estimated_time_remaining=job.get("estimated_time_remaining"),
            result=job.get("result"),
            error=job["error"]["message"] if job.get("error") else None
        )
        
        return progress_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get upload status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get upload status")

@router.delete("/{job_id}")
async def delete_upload(job_id: str, current_user = Depends(get_current_user)):
    """Delete uploaded file and associated job"""
    try:
        # Find and delete processing job
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one_and_delete({
            "job_id": job_id,
            "user": current_user["id"]
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete associated media file
        media_collection = await get_collection("media_files")
        media_file = await media_collection.find_one_and_delete({
            "_id": job["media_file"]
        })
        
        if media_file:
            # Delete physical file
            file_path = Path(media_file["file_path"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Physical file deleted: {media_file['file_name']}")
        
        # Remove from Redis
        await delete_progress(job_id)
        
        logger.info(f"Upload deleted: {job_id}", extra={
            "user_id": current_user["id"]
        })
        
        return {"success": True, "message": "Upload deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete upload")

@router.get("/history")
async def get_upload_history(
    page: int = 1,
    per_page: int = 20,
    current_user = Depends(get_current_user)
):
    """Get user's upload history"""
    try:
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        skip = (page - 1) * per_page
        
        # Get processing jobs with media files
        jobs_collection = await get_collection("processing_jobs")
        media_collection = await get_collection("media_files")
        
        # Aggregate jobs with media file info
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
        
        jobs = await jobs_collection.aggregate(pipeline).to_list(None)
        
        # Count total
        total = await jobs_collection.count_documents({"user": current_user["id"]})
        
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
        logger.error(f"Get upload history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get upload history")

async def get_file_size(file: UploadFile) -> int:
    """Get actual file size from UploadFile"""
    # For UploadFile, we need to read the content to get size
    content = await file.read()
    file_size = len(content)
    # Reset file position for subsequent reads
    await file.seek(0)
    return file_size