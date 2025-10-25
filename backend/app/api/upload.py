from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime, timedelta
import os
import uuid
import time
import aiofiles
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_progress, delete_progress, get_progress
from app.models.schemas import (
    MediaFile, ProcessingJob, ProcessingJobCreate, 
    UploadResponse, ProgressResponse, JobStatus
)
from app.api.dependencies import get_user_by_id
from app.api.auth import get_current_user_optional
from app.services.media_processor import MediaProcessor
from app.utils.file_utils import (
    validate_file_type, get_file_type, 
    get_file_size_formatted, generate_unique_filename
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.options("/")
@router.options("")
async def upload_options():
    """Handle CORS preflight requests for upload endpoint"""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"}
    )

@router.post("/")
@router.post("")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    model: str = Form("whisper-1"),
    speaker_diarization: bool = Form(False),
    auto_delete: Optional[int] = Form(None),
    current_user = Depends(get_current_user_optional)
):
    """Upload video or audio file for transcription"""
    logger.info(f"📤 Upload request received - File: {file.filename}")
    
    # Auto-create guest user if not authenticated
    if not current_user:
        logger.info("🔓 No user authentication found, creating guest user...")
        try:
            from app.api.auth import guest_login
            from app.models.schemas import UserCreate
            
            guest_data = UserCreate(
                username=f"Guest_{int(time.time())}",
                openid=f"guest_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            )
            
            guest_user = await guest_login(guest_data)
            current_user = {
                "id": guest_user["user"]["id"],
                "username": guest_user["user"]["username"],
                "openid": guest_user["user"]["openid"],
                "subscription_level": guest_user["user"]["subscription_level"],
                "quota_used": guest_user["user"]["quota_used"],
                "quota_limit": guest_user["user"]["quota_limit"],
                "quota_reset_date": guest_user["user"]["quota_reset_date"],
                "is_active": guest_user["user"]["is_active"]
            }
            logger.info(f"✅ Guest user created: {current_user['username']}")
        except Exception as guest_error:
            logger.error(f"❌ Failed to create guest user: {guest_error}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create guest user session"
            )
    else:
        logger.info(f"🔓 Authenticated user: {current_user.get('username', 'Unknown')}")
    
    try:
        # Validate file
        if not file.content_type:
            raise HTTPException(status_code=400, detail="File content type is required")
        
        if not validate_file_type(file.content_type):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Validate model
        valid_models = ["whisper-1", "whisper-base", "whisper-small", "whisper-medium", "whisper-large", "deepseek-1"]
        if model not in valid_models:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model. Valid options: {', '.join(valid_models)}"
            )
        
        # Validate auto_delete
        if auto_delete is not None and (auto_delete < 1 or auto_delete > 365):
            raise HTTPException(
                status_code=400,
                detail="auto_delete must be between 1 and 365 days"
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
        
        # Generate unique filename and job ID
        unique_filename = generate_unique_filename(file.filename or "upload")
        file_path = Path(settings.UPLOAD_DIR) / unique_filename
        job_id = str(uuid.uuid4())
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Extract file duration if possible
        duration = None
        try:
            # Basic duration extraction for audio/video files
            import mutagen
            audio_file = mutagen.File(file_path)
            if audio_file and hasattr(audio_file, 'info'):
                duration = audio_file.info.length
        except:
            pass  # Duration extraction is optional
        
        # Create media file record
        media_file_data = {
            "originalName": file.filename,
            "fileName": unique_filename,
            "filePath": str(file_path),
            "fileSize": actual_file_size,
            "mimeType": file.content_type,
            "duration": duration,
            "uploaded_by": current_user["id"],
            "expiresAt": datetime.utcnow() + timedelta(days=auto_delete or 30) if auto_delete != 0 else None
        }
        
        # Create processing job record
        job_data = {
            "jobId": job_id,  # Keep consistent with schema and queries
            "mediaFileId": None,  # Will be set after media file is created
            "userId": current_user["id"],  # Keep consistent with schema
            "job": {
                "provider": "openai",
                "model": model,
                "settings": {
                    "language": language or "auto",
                    "speakerDiarization": speaker_diarization,
                    "profanityFilter": False,
                    "punctuation": True,
                    "customVocabulary": []
                }
            },
            "processing": {
                "status": "uploaded",
                "progress": 0,
                "startedAt": None,
                "completedAt": None,
                "error": None,
                "retryCount": 0,
                "lastRetryAt": None
            },
            "queue": {
                "priority": 5,
                "attempts": 0,
                "maxAttempts": 3,
                "nextRetryAt": None
            },
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        # Save to database
        media_collection = await get_collection("media_files")
        media_result = await media_collection.insert_one(media_file_data)
        
        # Link job to media file
        job_data["mediaFileId"] = media_result.inserted_id
        
        jobs_collection = await get_collection("processing_jobs")
        job_result = await jobs_collection.insert_one(job_data)
        
        # Estimate processing time (rough calculation: 1 second per 10 seconds of audio)
        estimated_processing_time = int((duration or 60) / 10) if duration else 60
        
        logger.info(f"File uploaded successfully: {unique_filename}", extra={
            "user_id": current_user["id"],
            "job_id": job_id,
            "file_size": actual_file_size,
            "file_type": file_type_enum
        })
        
        # Start processing immediately (synchronous approach for reliability)
        try:
            from app.services.media_processor import MediaProcessor
            processor = MediaProcessor()
            
            logger.info(f"Starting processing task for job {job_id}")
            
            # Process immediately (not as background task)
            # This ensures the task will definitely run
            import asyncio
            asyncio.create_task(
                processor.process_transcription_job(
                    job_id,
                    str(media_result.inserted_id),
                    current_user["id"]
                )
            )
            
            logger.info(f"Processing task started for job {job_id}")
            
        except Exception as task_error:
            logger.error(f"Failed to start processing task for job {job_id}: {task_error}")
            import traceback
            logger.error(f"Task error details: {traceback.format_exc()}")
            # Don't fail the upload, just log the error
        
        return {
            "job_id": job_id,
            "status": "uploaded",
            "file_info": {
                "original_name": file.filename,
                "file_size": actual_file_size,
                "mime_type": file.content_type,
                "duration": duration
            },
            "estimated_processing_time": estimated_processing_time,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/{job_id}")
async def get_transcription_status(job_id: str, current_user = Depends(get_current_user_optional)):
    """Get transcription status and results"""
    try:
        # For status checks, get job info first to determine access
        collection = await get_collection("processing_jobs")
        job = await collection.find_one({"jobId": job_id})
        
        if not job:
            logger.warning(f"Job {job_id} not found")
            return {
                "success": False,
                "error": "Job not found",
                "data": None
            }
        
        # If no user and job was created by a guest, create new guest session
        if not current_user and job.get("isGuestUpload"):
            logger.info("🔓 Creating guest session for status check...")
            try:
                from app.api.auth import guest_login
                from app.models.schemas import UserCreate
                
                guest_data = UserCreate(
                    username=f"Guest_{int(time.time())}",
                    openid=f"guest_{int(time.time())}_{uuid.uuid4().hex[:8]}"
                )
                
                guest_user = await guest_login(guest_data)
                current_user = {
                    "id": guest_user["user"]["id"],
                    "username": guest_user["user"]["username"],
                    "openid": guest_user["user"]["openid"],
                    "subscription_level": guest_user["user"]["subscription_level"],
                    "quota_used": guest_user["user"]["quota_used"],
                    "quota_limit": guest_user["user"]["quota_limit"],
                    "quota_reset_date": guest_user["user"]["quota_reset_date"],
                    "is_active": guest_user["user"]["is_active"]
                }
                logger.info(f"✅ Guest session created: {current_user['username']}")
            except Exception as guest_error:
                logger.error(f"❌ Failed to create guest session: {guest_error}")
                return {
                    "success": False,
                    "error": "Failed to create guest session",
                    "data": None
                }
        # If user is authenticated, verify ownership
        elif current_user and job.get("userId") != current_user["id"]:
            logger.warning(f"User {current_user.get('id')} attempted to access job {job_id} owned by {job.get('userId')}")
            return {
                "success": False,
                "error": "You don't have permission to access this job",
                "data": None
            }
        
        logger.info(f"Fetching status for job {job_id}, user {current_user.get('id')}")
        
        # Try to get from Redis first (real-time progress)
        progress_data = await get_progress(job_id)
        if progress_data:
            logger.info(f"Found job {job_id} in Redis cache")
            job_response = await format_job_response(progress_data, current_user["id"])
            
            # Wrap response in expected format
            return {
                "success": True,
                "error": None,
                "data": job_response
            }
        
        # If not in Redis, get from database
        collection = await get_collection("processing_jobs")
        job = await collection.find_one({
            "jobId": job_id,
            "userId": current_user["id"]
        })
        
        if not job:
            logger.warning(f"Job {job_id} not found for user {current_user.get('id')}")
            raise HTTPException(
                status_code=404, 
                detail=f"Job {job_id} not found. Please verify the job ID and ensure you have permission to access it."
            )
        
        logger.info(f"Found job {job_id} in database, status: {job.get('processing', {}).get('status', 'unknown')}")
        job_response = await format_job_response(job, current_user["id"])
        
        # Wrap response in expected format
        return {
            "success": True,
            "error": None,
            "data": job_response
        }
        
    except HTTPException as http_ex:
        # Return properly formatted error response
        return {
            "success": False,
            "error": http_ex.detail,
            "data": None
        }
    except Exception as e:
        logger.error(f"Get transcription status error for job {job_id}: {str(e)}", exc_info=True, extra={
            "job_id": job_id,
            "user_id": current_user.get("id"),
            "error_type": type(e).__name__
        })
        # Return properly formatted error response
        return {
            "success": False,
            "error": f"Failed to get transcription status: {str(e)}",
            "data": None
        }

async def format_job_response(job_data: dict, user_id: str) -> dict:
    """Format job data to match OpenAPI specification"""
    try:
        if not job_data:
            logger.error("Empty job_data provided to format_job_response")
            return {
                "job_id": "unknown",
                "status": "error",
                "error": "Invalid job data"
            }

        logger.debug(f"Formatting job response for job {job_data.get('jobId', 'unknown')}")
        
        # Get media file info
        media_file = None
        media_file_id = job_data.get("mediaFileId")
        if media_file_id:
            media_collection = await get_collection("media_files")
            media_file = await media_collection.find_one({"_id": media_file_id})
            if not media_file:
                logger.warning(f"Media file not found for ID {media_file_id}")
        
        # Get transcription results if completed
        results = None
        if job_data.get("processing", {}).get("status") == "completed":
            results_collection = await get_collection("transcription_results")
            transcription_result = await results_collection.find_one({"jobId": job_data["jobId"]})
            if transcription_result:
                results = {
                    "text": transcription_result["full_text"],
                    "language": transcription_result["language"],
                    "confidence": transcription_result["confidence"],
                    "duration": transcription_result.get("duration", 0),
                    "words": [
                        {
                            "word": segment.get("text", ""),
                            "start": segment.get("start_time", 0),
                            "end": segment.get("end_time", 0),
                            "confidence": segment.get("confidence", 0)
                        }
                        for segment in transcription_result.get("segments", [])
                    ],
                    "segments": [
                        {
                            "id": i,
                            "start": segment.get("start_time", 0),
                            "end": segment.get("end_time", 0),
                            "text": segment.get("text", ""),
                            "speaker": segment.get("speaker"),
                            "confidence": segment.get("confidence", 0)
                        }
                        for i, segment in enumerate(transcription_result.get("segments", []))
                    ],
                    "speakers": []  # TODO: Implement speaker diarization
                }
        
        # Format response
        response = {
            "job_id": job_data["jobId"],
            "status": job_data.get("processing", {}).get("status", "uploaded"),
            "progress": job_data.get("processing", {}).get("progress", 0),
            "file_info": {
                "original_name": media_file.get("originalName", "Unknown") if media_file else "Unknown",
                "file_size": media_file.get("fileSize", 0) if media_file else 0,
                "mime_type": media_file.get("mimeType", "unknown") if media_file else "unknown",
                "duration": media_file.get("duration") if media_file else None
            },
            "settings": job_data.get("job", {}).get("settings", {}),
            "results": results,
            "processing_info": {
                "started_at": job_data.get("processing", {}).get("startedAt"),
                "completed_at": job_data.get("processing", {}).get("completedAt"),
                "processing_time": None,  # TODO: Calculate processing time
                "cost": 0.0  # TODO: Implement cost calculation
            },
            "error": job_data.get("processing", {}).get("error"),
            "created_at": job_data.get("createdAt"),
            "updated_at": job_data.get("updatedAt")
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error formatting job response: {e}")
        return {
            "job_id": job_data.get("jobId", "unknown"),
            "status": "failed",
            "error": str(e)
        }

@router.delete("/{job_id}")
async def delete_upload(job_id: str, current_user = Depends(get_current_user_optional)):
    """Delete uploaded file and associated job"""
    try:
        # Find and delete processing job
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one_and_delete({
            "jobId": job_id,
            "userId": current_user["id"]
        })
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete associated media file
        media_collection = await get_collection("media_files")
        media_file = await media_collection.find_one_and_delete({
            "_id": job["mediaFileId"]
        })
        
        if media_file:
            # Delete physical file
            file_path = Path(media_file["filePath"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Physical file deleted: {media_file['fileName']}")
        
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

@router.get("/jobs")
async def get_transcription_jobs(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user = Depends(get_current_user_optional)
):
    """Get user's transcription jobs"""
    try:
        # Validate parameters
        if limit < 1 or limit > 100:
            limit = 20
        if offset < 0:
            offset = 0
            
        if status and status not in ["queued", "processing", "completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Valid values: queued, processing, completed, failed"
            )
        
        # Build query
        query = {"userId": current_user["id"]}
        if status:
            # Convert status names to match JobStatus enum
            status_mapping = {
                "queued": JobStatus.PENDING,
                "processing": JobStatus.PROCESSING,
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED
            }
            query["processing.status"] = status_mapping.get(status, status)
        
        # Get jobs with pagination
        collection = await get_collection("processing_jobs")
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Get jobs with pagination
        jobs = await collection.find(query).sort("createdAt", -1).skip(offset).limit(limit).to_list(None)
        
        # Format response
        formatted_jobs = []
        for job in jobs:
            # Get media file info
            media_collection = await get_collection("media_files")
            media_file = await media_collection.find_one({"_id": job["mediaFileId"]})
            
            # Get transcription results if completed
            result = None
            if job.get("processing", {}).get("status") == "completed":
                results_collection = await get_collection("transcription_results")
                transcription_result = await results_collection.find_one({"jobId": job["jobId"]})
                if transcription_result:
                    result = {
                        "text": transcription_result["full_text"],
                        "language": transcription_result["language"],
                        "confidence": transcription_result["confidence"],
                        "duration": transcription_result.get("duration", 0),
                        "words": transcription_result.get("segments", [])
                    }
            
            formatted_job = {
                "job_id": job["jobId"],
                "status": job.get("processing", {}).get("status", "uploaded"),
                "progress": job.get("processing", {}).get("progress", 0),
                "file_info": {
                    "original_name": media_file.get("originalName", "Unknown") if media_file else "Unknown",
                    "file_size": media_file.get("fileSize", 0) if media_file else 0,
                    "mime_type": media_file.get("mimeType", "unknown") if media_file else "unknown",
                    "duration": media_file.get("duration") if media_file else None
                },
                "settings": job.get("job", {}).get("settings", {
                    "language": "auto",
                    "model": "whisper-1",
                    "speaker_diarization": False
                }),
                "results": result,
                "processing_info": {
                    "started_at": job.get("processing", {}).get("startedAt"),
                    "completed_at": job.get("processing", {}).get("completedAt"),
                    "processing_time": None,
                    "cost": 0.0
                },
                "error": job.get("processing", {}).get("error"),
                "created_at": job.get("createdAt"),
                "updated_at": job.get("updatedAt")
            }
            
            formatted_jobs.append(formatted_job)
        
        # Calculate statistics
        stats_pipeline = [
            {"$match": {"userId": current_user["id"]}},
            {"$group": {
                "_id": "$processing.status",
                "count": {"$sum": 1}
            }}
        ]
        
        status_counts = await collection.aggregate(stats_pipeline).to_list(None)
        stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        
        for status_count in status_counts:
            if status_count["_id"] in stats:
                stats[status_count["_id"]] = status_count["count"]
        
        return {
            "jobs": formatted_jobs,
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total
            },
            "stats": {
                "total_processing": total,
                "completed": stats["completed"],
                "failed": stats["failed"],
                "queued": stats["pending"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get transcription jobs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get transcription jobs"
        )

@router.get("/history")
async def get_upload_history(
    page: int = 1,
    per_page: int = 20,
    current_user = Depends(get_current_user_optional)
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

@router.get("/{job_id}/download")
async def download_transcription(
    job_id: str,
    format: str = "json",
    current_user = Depends(get_current_user_optional)
):
    """Download transcription results in various formats"""
    try:
        if format not in ["json", "txt", "srt", "vtt"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Supported formats: json, txt, srt, vtt"
            )
        
        # Get transcription result
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({
            "job_id": job_id,
            "user_id": current_user["id"],  # Changed from user to user_id
            "status": JobStatus.COMPLETED
        })
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail="Transcription not found or not completed"
            )
        
        # Get transcription results from separate collection if exists
        results_collection = await get_collection("transcription_results")
        transcription_result = await results_collection.find_one({"job_id": job_id})
        
        if not transcription_result:
            raise HTTPException(
                status_code=404,
                detail="Transcription results not found"
            )
        
        # Generate content based on format
        if format == "json":
            content = {
                "job_id": job_id,
                "text": transcription_result["full_text"],
                "language": transcription_result["language"],
                "confidence": transcription_result["confidence"],
                "duration": transcription_result.get("duration", 0),
                "segments": transcription_result.get("segments", []),
                "metadata": transcription_result.get("metadata", {}),
                "created_at": transcription_result["created_at"]
            }
            from fastapi.responses import JSONResponse
            return JSONResponse(content=content)
        
        elif format == "txt":
            content = transcription_result["full_text"]
            media_type = "text/plain"
            filename = f"transcription_{job_id}.txt"
        
        elif format == "srt":
            content = _generate_srt_content(transcription_result.get("segments", []))
            media_type = "text/plain"
            filename = f"transcription_{job_id}.srt"
        
        elif format == "vtt":
            content = _generate_vtt_content(transcription_result.get("segments", []))
            media_type = "text/vtt"
            filename = f"transcription_{job_id}.vtt"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download transcription error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to download transcription"
        )

def _generate_srt_content(segments: list) -> str:
    """Generate SRT format content"""
    srt_content = []
    
    for i, segment in enumerate(segments, 1):
        start_time = _format_srt_time(segment.get("start_time", 0))
        end_time = _format_srt_time(segment.get("end_time", 0))
        text = segment.get("text", "")
        
        srt_content.append(f"{i}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(text)
        srt_content.append("")  # Empty line between segments
    
    return "\\n".join(srt_content)

def _generate_vtt_content(segments: list) -> str:
    """Generate WebVTT format content"""
    vtt_content = ["WEBVTT", ""]
    
    for segment in segments:
        start_time = _format_vtt_time(segment.get("start_time", 0))
        end_time = _format_vtt_time(segment.get("end_time", 0))
        text = segment.get("text", "")
        
        vtt_content.append(f"{start_time} --> {end_time}")
        vtt_content.append(text)
        vtt_content.append("")  # Empty line between segments
    
    return "\\n".join(vtt_content)

def _format_srt_time(seconds: float) -> str:
    """Format time for SRT (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def _format_vtt_time(seconds: float) -> str:
    """Format time for WebVTT (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

async def get_file_size(file: UploadFile) -> int:
    """Get actual file size from UploadFile"""
    # For UploadFile, we need to read the content to get size
    content = await file.read()
    file_size = len(content)
    # Reset file position for subsequent reads
    await file.seek(0)
    return file_size