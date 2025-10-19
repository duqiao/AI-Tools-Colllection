"""
Quota API endpoints for managing user translation quotas.

This module provides API endpoints for checking quota status,
usage tracking, and quota management operations.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from app.core.logging import get_logger
from app.core.dependencies import get_current_active_user, get_quota_service
from app.services.quota_service import QuotaService

logger = get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


# Pydantic models
class QuotaCheckRequest(BaseModel):
    """Quota check request model."""
    required_quota: int = 1


class QuotaUseRequest(BaseModel):
    """Quota usage request model."""
    amount: int = 1
    usage_type: str = "translation"
    description: Optional[str] = None
    translation_id: Optional[int] = None


class QuotaResponse(BaseModel):
    """Quota status response model."""
    available: bool
    remaining: int
    plan_type: str
    monthly_quota: int
    used_quota: int
    subscription_active: bool
    warning_level: Optional[str] = None
    message: Optional[str] = None
    next_reset: Optional[str] = None
    show_upgrade_prompt: bool = False


class QuotaAnalyticsResponse(BaseModel):
    """Quota analytics response model."""
    period_days: int
    total_used: int
    total_quota: int
    utilization_percent: float
    daily_usage: Dict[str, int]
    average_daily: float
    quota_info: Dict[str, Any]


class BonusQuotaRequest(BaseModel):
    """Bonus quota request model (admin only)."""
    user_id: int
    bonus_amount: int
    reason: str
    expiry_days: Optional[int] = None


@router.get("/status", response_model=QuotaResponse)
async def get_quota_status(
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Get current user's quota status.
    
    This endpoint returns detailed information about the user's
    current quota including remaining usage and warnings.
    """
    try:
        user_id = current_user["id"]
        
        # Get basic quota availability
        quota_info = quota_service.check_quota_availability(user_id)
        
        # Get warning threshold information
        warning_info = quota_service.get_quota_warning_threshold(user_id)
        
        # Get reset schedule
        reset_schedule = quota_service.get_quota_reset_schedule(user_id)
        
        # Combine all quota information
        response_data = {
            **quota_info,
            "warning_level": warning_info.get("warning_level"),
            "message": warning_info.get("message"),
            "next_reset": reset_schedule.get("next_reset"),
            "show_upgrade_prompt": warning_info.get("show_upgrade_prompt", False)
        }
        
        return QuotaResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Get quota status error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配额状态失败"
        )


@router.post("/check", response_model=QuotaResponse)
async def check_quota_availability(
    request: QuotaCheckRequest,
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Check if user has enough quota for a translation.
    
    This endpoint validates quota availability before starting
    a new translation operation.
    """
    try:
        user_id = current_user["id"]
        required_quota = request.required_quota
        
        # Check quota availability
        quota_info = quota_service.check_quota_availability(user_id, required_quota)
        
        if not quota_info["available"]:
            return QuotaResponse(
                available=False,
                remaining=quota_info["remaining"],
                plan_type=quota_info["plan_type"],
                monthly_quota=quota_info.get("monthly_quota", 1),
                used_quota=quota_info.get("used_quota", 0),
                subscription_active=quota_info.get("subscription_active", False),
                warning_level="exhausted",
                message="翻译次数不足",
                show_upgrade_prompt=True
            )
        
        # Get warning threshold
        warning_info = quota_service.get_quota_warning_threshold(user_id)
        
        return QuotaResponse(
            available=True,
            remaining=quota_info["remaining"],
            plan_type=quota_info["plan_type"],
            monthly_quota=quota_info.get("monthly_quota", 1),
            used_quota=quota_info.get("used_quota", 0),
            subscription_active=quota_info.get("subscription_active", False),
            warning_level=warning_info.get("warning_level"),
            message=warning_info.get("message"),
            show_upgrade_prompt=warning_info.get("show_upgrade_prompt", False)
        )
        
    except Exception as e:
        logger.error(f"Check quota availability error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查配额可用性失败"
        )


@router.post("/use", response_model=Dict[str, Any])
async def use_quota(
    request: QuotaUseRequest,
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Use quota for a translation or other operation.
    
    This endpoint deducts quota from the user's account
    and creates usage records for tracking.
    """
    try:
        user_id = current_user["id"]
        
        # Use quota
        result = quota_service.use_quota(
            user_id=user_id,
            amount=request.amount,
            usage_type=request.usage_type,
            description=request.description,
            translation_id=request.translation_id
        )
        
        if result["success"]:
            logger.info(f"User {user_id} used {request.amount} quota")
            return {
                "success": True,
                "message": "配额使用成功",
                "remaining": result.get("remaining", 0)
            }
        else:
            logger.warning(f"User {user_id} quota usage failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error", "配额使用失败"),
                "remaining": result.get("remaining", 0)
            }
        
    except Exception as e:
        logger.error(f"Use quota error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="使用配额失败"
        )


@router.post("/reset", response_model=Dict[str, Any])
async def reset_quota(
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Reset user's quota (admin operation or automatic reset).
    
    This endpoint resets the user's quota for a new period.
    """
    try:
        user_id = current_user["id"]
        
        # In a real implementation, this would be admin-only
        # For now, allow users to reset their own quota for testing
        success = quota_service.reset_quota(user_id)
        
        if success:
            return {
                "success": True,
                "message": "配额重置成功"
            }
        else:
            return {
                "success": False,
                "error": "配额重置失败"
            }
        
    except Exception as e:
        logger.error(f"Reset quota error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置配额失败"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_quota_history(
    limit: int = 50,
    usage_type: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Get user's quota usage history.
    
    This endpoint returns a history of quota usage records
    for the authenticated user.
    """
    try:
        user_id = current_user["id"]
        
        # Get usage history
        history = quota_service.get_quota_usage_history(
            user_id=user_id,
            limit=limit,
            usage_type=usage_type
        )
        
        # Convert to response format
        response_data = []
        for record in history:
            response_data.append({
                "id": record.id,
                "usage_type": record.usage_type,
                "amount": record.amount,
                "description": record.description,
                "created_at": record.created_at.isoformat(),
                "translation_id": record.translation_id
            })
        
        return response_data
        
    except Exception as e:
        logger.error(f"Get quota history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配额历史失败"
        )


@router.get("/analytics", response_model=QuotaAnalyticsResponse)
async def get_quota_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Get quota usage analytics for a time period.
    
    This endpoint returns analytics data about quota usage
    patterns and statistics for the specified period.
    """
    try:
        user_id = current_user["id"]
        
        # Get analytics data
        analytics = quota_service.get_quota_usage_analytics(
            user_id=user_id,
            days=days
        )
        
        return QuotaAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"Get quota analytics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配额分析数据失败"
        )


@router.get("/reset-schedule", response_model=Dict[str, Any])
async def get_quota_reset_schedule(
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Get quota reset schedule information.
    
    This endpoint returns information about when the user's
    quota will be automatically reset.
    """
    try:
        user_id = current_user["id"]
        
        # Get reset schedule
        schedule = quota_service.get_quota_reset_schedule(user_id)
        
        if "error" in schedule:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=schedule["error"]
            )
        
        return schedule
        
    except Exception as e:
        logger.error(f"Get quota reset schedule error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取配额重置计划失败"
        )


@router.post("/check-reset-needed", response_model=Dict[str, Any])
async def check_quota_reset_needed(
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Check if user's quota needs to be reset.
    
    This endpoint checks if the user's quota period has ended
    and needs to be reset.
    """
    try:
        user_id = current_user["id"]
        
        # Check if reset is needed
        reset_check = quota_service.check_quota_period_reset_needed(user_id)
        
        if reset_check["needs_reset"]:
            # Perform automatic reset
            success = quota_service.reset_quota(user_id)
            
            return {
                "needs_reset": True,
                "reset_performed": success,
                "plan_type": reset_check["plan_type"],
                "current_quota": reset_check["current_quota"],
                "new_quota": reset_check["new_quota"],
                "reset_date": reset_check["reset_date"]
            }
        else:
            return {
                "needs_reset": False,
                "reset_performed": False,
                "plan_type": reset_check["plan_type"],
                "current_quota": reset_check["current_quota"],
                "new_quota": reset_check["new_quota"]
            }
        
    except Exception as e:
        logger.error(f"Check quota reset needed error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="检查配额重置需求失败"
        )


@router.post("/bonus", response_model=Dict[str, Any])
async def add_bonus_quota(
    request: BonusQuotaRequest,
    current_user: dict = Depends(get_current_active_user),
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Add bonus quota to user account (admin operation).
    
    This endpoint adds bonus quota to a user's account
    for promotional or compensation purposes.
    """
    try:
        # In a real implementation, this would check if the current user is an admin
        # For now, we'll allow it for testing purposes
        
        success = quota_service.add_bonus_quota(
            user_id=request.user_id,
            bonus_amount=request.bonus_amount,
            reason=request.reason,
            expiry_days=request.expiry_days
        )
        
        if success:
            logger.info(f"Added {request.bonus_amount} bonus quota to user {request.user_id}")
            return {
                "success": True,
                "message": f"成功添加 {request.bonus_amount} 次奖励配额",
                "user_id": request.user_id,
                "bonus_amount": request.bonus_amount,
                "reason": request.reason
            }
        else:
            return {
                "success": False,
                "error": "添加奖励配额失败"
            }
        
    except Exception as e:
        logger.error(f"Add bonus quota error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加奖励配额失败"
        )


# Admin-only endpoints (would need admin authentication middleware in production)
@router.post("/admin/reset-expired", response_model=Dict[str, Any])
async def reset_expired_quotas(
    quota_service: QuotaService = Depends(get_quota_service)
):
    """
    Reset quotas for all expired subscriptions (admin operation).
    
    This endpoint finds all users with expired subscriptions
    and resets them to free tier quotas.
    """
    try:
        # In a real implementation, this would require admin authentication
        reset_count = quota_service.check_and_reset_expired_quotas()
        
        return {
            "success": True,
            "message": f"成功重置 {reset_count} 个过期的订阅配额",
            "reset_count": reset_count
        }
        
    except Exception as e:
        logger.error(f"Reset expired quotas error: {str(e)}")
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置过期配额失败"
        )