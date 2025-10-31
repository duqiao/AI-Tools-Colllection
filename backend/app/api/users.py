from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.repositories.user_repository import UserRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.job_repository import ProcessingJobRepository
from app.models.schemas import User, UserProfile, UserProfileUpdate, UserResponse, SubscriptionLevel
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user profile using PostgreSQL"""
    try:
        async with UserRepository() as user_repo:
            user = await user_repo.get_by_id(current_user["id"])
            
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
        
        return UserResponse(
            id=str(user["id"]),
            username=user["username"],
            email=user["email"],
            subscription_level=user["subscription_level"],
            profile=user.get("profile", {}),
            usage_stats=user.get("usage_stats", {}),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
            last_login=user.get("last_login")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user profile using PostgreSQL"""
    try:
        async with UserRepository() as user_repo:
            # Build profile updates using PostgreSQL schema
            profile_updates = {}
            
            if profile_data.first_name is not None:
                profile_updates["first_name"] = profile_data.first_name
            if profile_data.last_name is not None:
                profile_updates["last_name"] = profile_data.last_name
            if profile_data.avatar_url is not None:
                profile_updates["avatar_url"] = profile_data.avatar_url
            if profile_data.preferences is not None:
                profile_updates["preferences"] = profile_data.preferences
            
            if not profile_updates:
                raise HTTPException(
                    status_code=400,
                    detail="No valid fields to update"
                )
            
            # Update user profile
            success = await user_repo.update_profile(current_user["id"], profile_updates)
            
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Get updated user data
            updated_user = await user_repo.get_by_id(current_user["id"])
            
            logger.info(f"User profile updated: {current_user['id']}", extra={
                "updates": list(profile_updates.keys())
            })
        
        return UserResponse(
            id=str(updated_user["id"]),
            username=updated_user["username"],
            email=updated_user["email"],
            subscription_level=updated_user["subscription_level"],
            profile=updated_user.get("profile", {}),
            usage_stats=updated_user.get("usage_stats", {}),
            created_at=updated_user.get("created_at"),
            updated_at=updated_user.get("updated_at"),
            last_login=updated_user.get("last_login")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )

@router.get("/stats")
async def get_user_statistics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user statistics using PostgreSQL"""
    try:
        # Get file statistics using PostgreSQL
        async with MediaRepository() as media_repo:
            total_files = await media_repo.count_by_user(current_user["id"])
            storage_stats = await media_repo.get_storage_stats(current_user["id"])
            
            # Get files by type
            audio_files = await media_repo.count_by_type("audio")
            video_files = await media_repo.count_by_type("video")
            
            # Filter by user for file type counts
            audio_user_files = len(await media_repo.get_by_user_and_status(
                current_user["id"], "uploaded"
            ))
            # For now, we'll approximate - this would need refinement in real implementation
            user_audio_files = await media_repo.get_by_file_type("audio", limit=1000)
            user_video_files = await media_repo.get_by_file_type("video", limit=1000)
            
            user_audio_count = sum(1 for f in user_audio_files if str(f["user_id"]) == str(current_user["id"]))
            user_video_count = sum(1 for f in user_video_files if str(f["user_id"]) == str(current_user["id"]))
        
        # Get job statistics using PostgreSQL
        async with ProcessingJobRepository() as job_repo:
            total_jobs = await job_repo.count_by_user(current_user["id"])
            completed_jobs = await job_repo.get_by_status("completed")
            failed_jobs = await job_repo.get_by_status("failed")
            processing_jobs = await job_repo.get_by_status("processing")
            
            # Filter jobs by user
            user_completed = sum(1 for job in completed_jobs if str(job["user_id"]) == str(current_user["id"]))
            user_failed = sum(1 for job in failed_jobs if str(job["user_id"]) == str(current_user["id"]))
            user_processing = sum(1 for job in processing_jobs if str(job["user_id"]) == str(current_user["id"]))
            
            # Get job statistics
            job_stats = await job_repo.get_user_job_statistics(current_user["id"])
        
        # Get user statistics from user repository
        async with UserRepository() as user_repo:
            user_stats = await user_repo.get_user_stats(current_user["id"])
        
        # Get usage stats from current user data
        usage_stats = current_user.get("usage_stats", {})
        subscription_level = current_user.get("subscription_level", SubscriptionLevel.FREE)
        
        # Define limits by subscription level
        daily_limits = {
            SubscriptionLevel.FREE: {
                "total_files_processed": 10,
                "total_audio_duration": 300,  # 5 minutes
                "storage_used_bytes": 50 * 1024 * 1024  # 50MB
            },
            SubscriptionLevel.PREMIUM: {
                "total_files_processed": 100,
                "total_audio_duration": 3600,  # 1 hour
                "storage_used_bytes": 200 * 1024 * 1024  # 200MB
            },
            SubscriptionLevel.ENTERPRISE: {
                "total_files_processed": 1000,
                "total_audio_duration": 10800,  # 3 hours
                "storage_used_bytes": 500 * 1024 * 1024  # 500MB
            }
        }
        
        limits = daily_limits.get(subscription_level, daily_limits[SubscriptionLevel.FREE])
        
        # Calculate remaining limits
        files_remaining = max(0, limits["total_files_processed"] - usage_stats.get("total_files_processed", 0))
        audio_seconds_remaining = max(0, limits["total_audio_duration"] - usage_stats.get("total_audio_duration", 0))
        storage_bytes_remaining = max(0, limits["storage_used_bytes"] - usage_stats.get("storage_used_bytes", 0))
        
        return {
            "files": {
                "total": total_files,
                "size": storage_stats.get("total_size", 0),
                "duration": storage_stats.get("total_duration", 0),
                "audio_files": user_audio_count,
                "video_files": user_video_count
            },
            "transcriptions": {
                "total": total_jobs,
                "completed": user_completed,
                "failed": user_failed,
                "processing": user_processing,
                "average_processing_time": job_stats.get("avg_processing_time_seconds", 0)
            },
            "usage": {
                "total_files_processed": usage_stats.get("total_files_processed", 0),
                "total_audio_duration": usage_stats.get("total_audio_duration", 0),
                "api_calls_count": usage_stats.get("api_calls_count", 0),
                "storage_used_bytes": usage_stats.get("storage_used_bytes", 0)
            },
            "limits": {
                "files_remaining": files_remaining,
                "audio_seconds_remaining": audio_seconds_remaining,
                "storage_bytes_remaining": storage_bytes_remaining
            },
            "subscription_level": subscription_level
        }
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user statistics"
        )