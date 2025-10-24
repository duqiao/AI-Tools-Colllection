from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.database import get_collection
from app.models.schemas import User, UserProfile, UserProfileUpdate
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user profile"""
    try:
        collection = await get_collection("users")
        user = await collection.find_one({"_id": current_user["id"]})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return UserProfile(
            id=str(user["_id"]),
            email=user.get("email"),
            openid=user.get("openid"),
            username=user["username"],
            profile=user.get("profile", {}),
            subscription=user.get("subscription", {}),
            preferences=user.get("preferences", {}),
            createdAt=user.get("createdAt"),
            lastLoginAt=user.get("lastLoginAt")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user profile"""
    try:
        updates = {}
        
        # Build profile updates
        if profile_data.firstName is not None:
            updates["profile.firstName"] = profile_data.firstName
        if profile_data.lastName is not None:
            updates["profile.lastName"] = profile_data.lastName
        if profile_data.organization is not None:
            updates["profile.organization"] = profile_data.organization
        
        # Build preference updates
        if profile_data.defaultLanguage is not None:
            updates["preferences.defaultLanguage"] = profile_data.defaultLanguage
        if profile_data.autoDeleteDays is not None:
            updates["preferences.autoDeleteDays"] = profile_data.autoDeleteDays
        if profile_data.notificationSettings is not None:
            updates["preferences.notificationSettings"] = profile_data.notificationSettings
        
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )
        
        # Add updated timestamp
        updates["updatedAt"] = datetime.utcnow()
        
        # Update user in database
        collection = await get_collection("users")
        result = await collection.update_one(
            {"_id": current_user["id"]},
            {"$set": updates}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get updated user data
        updated_user = await collection.find_one({"_id": current_user["id"]})
        
        logger.info(f"User profile updated: {current_user.get('openid', current_user['id'])}", extra={
            "updates": list(updates.keys())
        })
        
        return UserProfile(
            id=str(updated_user["_id"]),
            email=updated_user.get("email"),
            openid=updated_user.get("openid"),
            username=updated_user["username"],
            profile=updated_user.get("profile", {}),
            subscription=updated_user.get("subscription", {}),
            preferences=updated_user.get("preferences", {}),
            createdAt=updated_user.get("createdAt"),
            lastLoginAt=updated_user.get("lastLoginAt")
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
    """Get user statistics"""
    try:
        from app.models.schemas import JobStatus
        
        # Get file statistics
        media_collection = await get_collection("media_files")
        total_files = await media_collection.count_documents({"uploaded_by": current_user["id"]})
        
        # Calculate total storage and duration
        pipeline = [
            {"$match": {"uploaded_by": current_user["id"]}},
            {"$group": {
                "_id": None,
                "total_size": {"$sum": "$file_size"},
                "total_duration": {"$sum": "$duration"},
                "audio_files": {"$sum": {"$cond": [{"$eq": ["$file_type", "audio"]}, 1, 0]}},
                "video_files": {"$sum": {"$cond": [{"$eq": ["$file_type", "video"]}, 1, 0]}}
            }}
        ]
        
        file_stats = await media_collection.aggregate(pipeline).to_list(None)
        file_stats = file_stats[0] if file_stats else {"total_size": 0, "total_duration": 0, "audio_files": 0, "video_files": 0}
        
        # Get transcription statistics
        jobs_collection = await get_collection("processing_jobs")
        
        total_transcriptions = await jobs_collection.count_documents({"user": current_user["id"]})
        completed_translations = await jobs_collection.count_documents({
            "user": current_user["id"],
            "status": JobStatus.COMPLETED
        })
        failed_translations = await jobs_collection.count_documents({
            "user": current_user["id"],
            "status": JobStatus.FAILED
        })
        processing_translations = await jobs_collection.count_documents({
            "user": current_user["id"],
            "status": JobStatus.PROCESSING
        })
        
        # Calculate average processing time
        pipeline = [
            {"$match": {"user": current_user["id"], "status": JobStatus.COMPLETED}},
            {"$group": {
                "_id": None,
                "avg_processing_time": {"$avg": "$processing_time"}
            }}
        ]
        
        avg_time_result = await jobs_collection.aggregate(pipeline).to_list(None)
        average_processing_time = avg_time_result[0]["avg_processing_time"] if avg_time_result else 0
        
        # Get current month usage
        from datetime import datetime, timedelta
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_month_pipeline = [
            {"$match": {
                "user": current_user["id"],
                "created_at": {"$gte": current_month_start}
            }},
            {"$group": {
                "_id": None,
                "minutes_used": {"$sum": "$duration"},
                "files_uploaded": {"$sum": 1}
            }}
        ]
        
        current_month_stats = await media_collection.aggregate(current_month_pipeline).to_list(None)
        current_month_stats = current_month_stats[0] if current_month_stats else {"minutes_used": 0, "files_uploaded": 0}
        
        # Calculate remaining limits
        subscription = current_user.get("subscription", {})
        limits = subscription.get("limits", {})
        usage = subscription.get("usage", {})
        
        storage_remaining = max(0, limits.get("maxStorage", 1024*1024*1024) - usage.get("currentStorage", 0))
        minutes_remaining = max(0, limits.get("monthlyMinutes", 120) - usage.get("monthlyMinutesUsed", 0))
        
        return {
            "files": {
                "total": total_files,
                "size": file_stats["total_size"],
                "duration": file_stats["total_duration"] or 0
            },
            "transcriptions": {
                "total": total_transcriptions,
                "completed": completed_translations,
                "failed": failed_translations,
                "processing": processing_translations,
                "average_processing_time": average_processing_time / 1000 if average_processing_time else 0  # Convert to seconds
            },
            "current_month": {
                "minutes_used": int(current_month_stats["minutes_used"] or 0),
                "files_uploaded": current_month_stats["files_uploaded"]
            },
            "limits": {
                "storage_remaining": storage_remaining,
                "minutes_remaining": minutes_remaining
            }
        }
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user statistics"
        )