from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.database import get_collection
from app.models.schemas import User
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user profile"""
    try:
        return {
            "success": True,
            "data": current_user
        }
        
    except Exception as e:
        logger.error(f"Get user profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )

@router.put("/profile")
async def update_user_profile(
    profile_data: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user profile"""
    try:
        # Get allowed update fields
        allowed_fields = {"username", "avatar_url"}
        updates = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No valid fields to update"
            )
        
        # Add constraints
        if "username" in updates:
            updates["username"] = updates["username"][:50].strip()
            if not updates["username"]:
                raise HTTPException(
                    status_code=400,
                    detail="Username cannot be empty"
                )
        
        if "avatar_url" in updates:
            updates["avatar_url"] = updates["avatar_url"][:255].strip()
        
        # Update user in database
        collection = await get_collection("users")
        result = await collection.update_one(
            {"_id": current_user["id"]},
            {
                "$set": {
                    **updates,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get updated user data
        updated_user = await get_collection("users").find_one({"_id": current_user["id"]})
        
        logger.info(f"User profile updated: {current_user['openid']}", extra={
            "updates": list(updates.keys())
        })
        
        return {
            "success": True,
            "data": {
                "id": str(updated_user["_id"]),
                "openid": updated_user["openid"],
                "username": updated_user["username"],
                "avatar_url": updated_user["avatar_url"],
                "subscription_level": updated_user["subscription_level"],
                "quota_used": updated_user["quota_used"],
                "quota_limit": updated_user["quota_limit"],
                "quota_reset_date": updated_user["quota_reset_date"],
                "is_active": updated_user["is_active"],
                "updated_at": updated_user["updated_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update user profile"
        )

@router.get("/statistics")
async def get_user_statistics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user statistics"""
    try:
        from app.models.schemas import JobStatus
        
        # Get translation statistics
        jobs_collection = await get_collection("processing_jobs")
        
        total_translations = await jobs_collection.count_documents({"user": current_user["id"]})
        completed_translations = await jobs_collection.count_documents({
            "user": current_user["id"],
            "status": JobStatus.COMPLETED
        })
        failed_translations = await jobs_collection.count_documents({
            "user": current_user["id"],
            "status": JobStatus.FAILED
        })
        
        success_rate = 0
        if total_translations > 0:
            success_rate = round((completed_translations / total_translations) * 100)
        
        # Get quota information
        quota_remaining = max(0, current_user["quota_limit"] - current_user["quota_used"])
        
        return {
            "success": True,
            "data": {
                "user": {
                    "id": current_user["id"],
                    "username": current_user["username"],
                    "subscription_level": current_user["subscription_level"],
                    "quota_used": current_user["quota_used"],
                    "quota_limit": current_user["quota_limit"],
                    "quota_remaining": quota_remaining,
                    "quota_reset_date": current_user["quota_reset_date"]
                },
                "statistics": {
                    "total_translations": total_translations,
                    "completed_translations": completed_translations,
                    "failed_translations": failed_translations,
                    "success_rate": success_rate,
                    "join_date": current_user.get("created_at", "unknown")
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user statistics"
        )