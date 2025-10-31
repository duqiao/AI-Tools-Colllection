from fastapi import Depends, HTTPException
from typing import Dict, Any, Optional
import logging

from app.api.auth import get_current_user, get_current_user_optional, get_user_by_id
from app.repositories.user_repository import UserRepository
from app.models.schemas import SubscriptionLevel

logger = logging.getLogger(__name__)

# Re-export dependencies for convenience
get_current_user_dependency = Depends(get_current_user)
get_current_user_optional_dependency = Depends(get_current_user_optional)

def check_subscription_level(minimum_level: SubscriptionLevel = SubscriptionLevel.FREE):
    """Dependency to check if user has sufficient subscription level"""
    async def subscription_dependency(current_user: Dict[str, Any] = get_current_user_dependency):
        user_level = current_user.get("subscription_level", SubscriptionLevel.FREE)
        
        # Define subscription hierarchy
        level_hierarchy = {
            SubscriptionLevel.FREE: 0,
            SubscriptionLevel.PREMIUM: 1,
            SubscriptionLevel.ENTERPRISE: 2
        }
        
        if level_hierarchy.get(user_level, 0) < level_hierarchy.get(minimum_level, 0):
            raise HTTPException(
                status_code=403,
                detail=f"Subscription level {minimum_level} required",
                headers={
                    "X-Current-Subscription": str(user_level),
                    "X-Required-Subscription": str(minimum_level)
                }
            )
        return current_user
    return subscription_dependency

def check_usage_limits(daily_limit_key: str = "total_files_processed"):
    """Dependency to check if user has exceeded daily usage limits"""
    async def usage_limit_dependency(current_user: Dict[str, Any] = get_current_user_dependency):
        try:
            usage_stats = current_user.get("usage_stats", {})
            subscription_level = current_user.get("subscription_level", SubscriptionLevel.FREE)
            
            # Define daily limits by subscription level
            daily_limits = {
                SubscriptionLevel.FREE: {
                    "total_files_processed": 10,
                    "total_audio_duration": 300,  # 5 minutes in seconds
                    "api_calls_count": 50
                },
                SubscriptionLevel.PREMIUM: {
                    "total_files_processed": 100,
                    "total_audio_duration": 3600,  # 1 hour in seconds
                    "api_calls_count": 500
                },
                SubscriptionLevel.ENTERPRISE: {
                    "total_files_processed": 1000,
                    "total_audio_duration": 10800,  # 3 hours in seconds
                    "api_calls_count": 5000
                }
            }
            
            limits = daily_limits.get(subscription_level, daily_limits[SubscriptionLevel.FREE])
            current_usage = usage_stats.get(daily_limit_key, 0)
            limit = limits.get(daily_limit_key, 0)
            
            if current_usage >= limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Daily limit exceeded for {daily_limit_key}",
                    headers={
                        "X-Usage-Current": str(current_usage),
                        "X-Usage-Limit": str(limit),
                        "X-Usage-Remaining": "0",
                        "X-Subscription-Level": str(subscription_level)
                    }
                )
            
            return current_user
            
        except Exception as e:
            logger.error(f"Error checking usage limits: {e}")
            # If we can't check limits, allow the request but log the error
            return current_user
    return usage_limit_dependency

def check_file_size_limit(max_size_mb: Optional[int] = None):
    """Dependency to check if file size is within user's limits"""
    async def file_size_dependency(
        current_user: Dict[str, Any] = get_current_user_dependency,
        file_size: int = 0  # This would be injected from request
    ):
        try:
            subscription_level = current_user.get("subscription_level", SubscriptionLevel.FREE)
            file_size_mb = file_size / (1024 * 1024)  # Convert bytes to MB
            
            # Define file size limits by subscription level
            file_size_limits = {
                SubscriptionLevel.FREE: 50,      # 50MB
                SubscriptionLevel.PREMIUM: 200,  # 200MB
                SubscriptionLevel.ENTERPRISE: 500  # 500MB
            }
            
            user_limit = file_size_limits.get(subscription_level, 50)
            
            # Use provided max_size if it's smaller than user's limit
            effective_limit = min(max_size or user_limit, user_limit)
            
            if file_size_mb > effective_limit:
                raise HTTPException(
                    status_code=413,
                    detail=f"File size {file_size_mb:.1f}MB exceeds limit of {effective_limit}MB",
                    headers={
                        "X-File-Size": str(file_size_mb),
                        "X-File-Size-Limit": str(effective_limit),
                        "X-Subscription-Level": str(subscription_level)
                    }
                )
            
            return current_user
            
        except Exception as e:
            logger.error(f"Error checking file size limit: {e}")
            return current_user
    return file_size_dependency

def require_auth():
    """Dependency to require authentication"""
    async def auth_dependency(current_user: Dict[str, Any] = get_current_user_optional_dependency):
        if not current_user:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return current_user
    return auth_dependency

def require_active_user():
    """Dependency to require active user account"""
    async def active_user_dependency(current_user: Dict[str, Any] = get_current_user_dependency):
        # For PostgreSQL, all users are considered active unless explicitly marked otherwise
        # This can be extended later if needed
        return current_user
    return active_user_dependency

async def get_user_repository():
    """Get user repository instance"""
    return UserRepository()

# Utility function to enrich user data with additional information
async def enrich_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich user data with computed fields and limits"""
    try:
        subscription_level = user_data.get("subscription_level", SubscriptionLevel.FREE)
        usage_stats = user_data.get("usage_stats", {})
        
        # Add computed fields
        enriched_data = user_data.copy()
        enriched_data["computed"] = {
            "remaining_files_today": max(0, 10 - usage_stats.get("total_files_processed", 0)),
            "remaining_audio_seconds": max(0, 300 - usage_stats.get("total_audio_duration", 0)),
            "storage_used_mb": usage_stats.get("storage_used_bytes", 0) / (1024 * 1024),
            "subscription_tier": subscription_level
        }
        
        return enriched_data
        
    except Exception as e:
        logger.error(f"Error enriching user data: {e}")
        return user_data