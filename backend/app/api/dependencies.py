from fastapi import Depends, HTTPException
from typing import Dict, Any, Optional

from app.api.auth import get_current_user, get_current_user_optional, get_user_by_id

# Re-export dependencies for convenience
get_current_user_dependency = Depends(get_current_user)
get_current_user_optional_dependency = Depends(get_current_user_optional)

def check_quota(minimum_quota: int = 1):
    """Dependency to check if user has sufficient quota"""
    async def quota_dependency(current_user: Dict[str, Any] = get_current_user_dependency):
        if current_user["quota_used"] + minimum_quota > current_user["quota_limit"]:
            raise HTTPException(
                status_code=429,
                detail="Quota exceeded",
                headers={
                    "X-Quota-Used": str(current_user["quota_used"]),
                    "X-Quota-Limit": str(current_user["quota_limit"]),
                    "X-Quota-Remaining": str(current_user["quota_limit"] - current_user["quota_used"])
                }
            )
        return current_user
    return quota_dependency

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