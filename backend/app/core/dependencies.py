"""
FastAPI dependencies

This module provides dependency injection functions for common
operations like database sessions, user authentication, etc.
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.user_service import UserService
from app.services.translation_service import TranslationService
from app.services.subscription_service import SubscriptionService
from app.services.quota_service import QuotaService

security = HTTPBearer()


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service instance."""
    return UserService(db)


def get_translation_service(db: Session = Depends(get_db)) -> TranslationService:
    """Get translation service instance."""
    return TranslationService(db)


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    """Get subscription service instance."""
    return SubscriptionService(db)


def get_quota_service(db: Session = Depends(get_db)) -> QuotaService:
    """Get quota service instance."""
    return QuotaService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current authenticated user from JWT token.
    
    This dependency extracts the JWT token, validates it,
    and returns the current user object.
    """
    # TODO: Implement JWT token validation
    # For now, return mock user
    
    try:
        token = credentials.credentials
        # Mock user for development
        mock_user = {
            "id": 1,
            "openid": "mock_openid_12345",
            "username": "测试用户",
            "subscription_level": "free"
        }
        return mock_user
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current active user.
    
    This dependency ensures the current user is active.
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_with_quota(
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Get current user with quota information.
    
    This dependency returns the user along with their quota status.
    """
    user_id = current_user["id"]
    quota_info = quota_service.check_quota_availability(user_id)
    
    return {
        **current_user,
        "quota_info": quota_info
    }