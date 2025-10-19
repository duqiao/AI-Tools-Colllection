"""
Quota service for managing user translation quotas and usage tracking.

This module provides business logic for quota management, including
quota checking, deduction, and reset operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.subscription import Subscription, UsageRecord
from app.core.logging import get_logger

logger = get_logger(__name__)


class QuotaService:
    """Service for quota management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_quota_availability(self, user_id: int, required_quota: int = 1) -> Dict[str, Any]:
        """Check if user has enough quota available."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "available": False,
                "remaining": 0,
                "error": "User not found"
            }
        
        # Check subscription quota first
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            remaining_quota = subscription.remaining_quota
            is_available = remaining_quota >= required_quota
            
            return {
                "available": is_available,
                "remaining": remaining_quota,
                "plan_type": subscription.plan_type,
                "monthly_quota": subscription.monthly_quota,
                "used_quota": subscription.used_quota,
                "subscription_active": subscription.is_active,
                "reset_date": subscription.end_date
            }
        
        # Check free user quota
        remaining_quota = user.remaining_quota
        is_available = remaining_quota >= required_quota
        
        return {
            "available": is_available,
            "remaining": remaining_quota,
            "plan_type": "free",
            "monthly_quota": user.quota_limit,
            "used_quota": user.quota_used,
            "subscription_active": user.is_subscription_active,
            "reset_date": user.quota_reset_date
        }
    
    def use_quota(
        self,
        user_id: int,
        amount: int = 1,
        usage_type: str = "translation",
        description: Optional[str] = None,
        translation_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Deduct quota from user's account."""
        # Check quota availability first
        quota_check = self.check_quota_availability(user_id, amount)
        if not quota_check["available"]:
            return {
                "success": False,
                "error": "Insufficient quota",
                "remaining": quota_check["remaining"]
            }
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "success": False,
                "error": "User not found"
            }
        
        # Use subscription quota if available
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            success = subscription.use_quota(amount)
            if success:
                # Create usage record
                usage_record = UsageRecord(
                    user_id=user_id,
                    translation_id=translation_id,
                    usage_type=usage_type,
                    amount=amount,
                    description=description or f"Quota usage: {usage_type}"
                )
                self.db.add(usage_record)
                self.db.commit()
                
                logger.info(f"Used {amount} quota from subscription for user {user_id}")
                return {
                    "success": True,
                    "remaining": subscription.remaining_quota,
                    "plan_type": subscription.plan_type
                }
        
        # Use free user quota
        if user.remaining_quota >= amount:
            user.increment_quota_used()
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                translation_id=translation_id,
                usage_type=usage_type,
                amount=amount,
                description=description or f"Quota usage: {usage_type}"
            )
            self.db.add(usage_record)
            self.db.commit()
            
            logger.info(f"Used {amount} quota from free tier for user {user_id}")
            return {
                "success": True,
                "remaining": user.remaining_quota,
                "plan_type": "free"
            }
        
        return {
            "success": False,
            "error": "Failed to use quota",
            "remaining": user.remaining_quota
        }
    
    def reset_quota(self, user_id: int, new_quota_limit: Optional[int] = None) -> bool:
        """Reset user's quota for new period."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Reset subscription quota
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            subscription.reset_quota()
            
            # Create usage record for quota reset
            usage_record = UsageRecord(
                user_id=user_id,
                usage_type="quota_reset",
                amount=0,
                description=f"Monthly quota reset for {subscription.plan_type}"
            )
            self.db.add(usage_record)
        else:
            # Reset free user quota
            if new_quota_limit is not None:
                user.reset_quota(new_quota_limit)
            else:
                user.reset_quota(user.quota_limit)
            
            # Create usage record for quota reset
            usage_record = UsageRecord(
                user_id=user_id,
                usage_type="quota_reset",
                amount=0,
                description="Free tier quota reset"
            )
            self.db.add(usage_record)
        
        self.db.commit()
        logger.info(f"Reset quota for user {user_id}")
        return True
    
    def get_quota_usage_history(
        self,
        user_id: int,
        limit: int = 50,
        usage_type: Optional[str] = None
    ) -> list:
        """Get user's quota usage history."""
        query = self.db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id
        )
        
        if usage_type:
            query = query.filter(UsageRecord.usage_type == usage_type)
        
        return query.order_by(
            UsageRecord.created_at.desc()
        ).limit(limit).all()
    
    def get_quota_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's quota usage statistics."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Get subscription info
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        # Get usage records
        total_usage = self.db.query(UsageRecord).filter(
            UsageRecord.user_id == user_id
        ).count()
        
        translation_usage = self.db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.usage_type == "translation"
            )
        ).count()
        
        # Get current month usage
        from datetime import timedelta
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = self.db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.created_at >= month_start
            )
        ).count()
        
        if subscription:
            return {
                "plan_type": subscription.plan_type,
                "monthly_quota": subscription.monthly_quota,
                "used_quota": subscription.used_quota,
                "remaining_quota": subscription.remaining_quota,
                "total_usage": total_usage,
                "translation_usage": translation_usage,
                "monthly_usage": monthly_usage,
                "reset_date": subscription.end_date
            }
        else:
            return {
                "plan_type": "free",
                "monthly_quota": user.quota_limit,
                "used_quota": user.quota_used,
                "remaining_quota": user.remaining_quota,
                "total_usage": total_usage,
                "translation_usage": translation_usage,
                "monthly_usage": monthly_usage,
                "reset_date": user.quota_reset_date
            }
    
    def check_and_reset_expired_quotas(self) -> int:
        """Check and reset quotas for expired subscriptions."""
        from datetime import timedelta
        
        # Check for subscriptions that expired yesterday
        yesterday = datetime.utcnow() - timedelta(days=1)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        expired_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.end_date >= yesterday,
                Subscription.end_date < today_start
            )
        ).all()
        
        reset_count = 0
        for subscription in expired_subscriptions:
            # Reset to free tier
            user = self.db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.reset_quota(1)  # Free tier gets 1 translation
                subscription.status = "expired"
                
                # Create usage record
                usage_record = UsageRecord(
                    user_id=user.id,
                    usage_type="subscription_expired",
                    amount=0,
                    description=f"Subscription {subscription.plan_type} expired, reset to free tier"
                )
                self.db.add(usage_record)
                
                reset_count += 1
                logger.info(f"Reset quota for expired subscription user {user.id}")
        
        if reset_count > 0:
            self.db.commit()
        
        return reset_count
    
    def add_bonus_quota(
        self,
        user_id: int,
        bonus_amount: int,
        reason: str,
        expiry_days: Optional[int] = None
    ) -> bool:
        """Add bonus quota to user account."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # For free users, increase quota limit
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            # Add to subscription quota
            subscription.monthly_quota += bonus_amount
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                usage_type="bonus_quota",
                amount=bonus_amount,
                description=reason
            )
            self.db.add(usage_record)
        else:
            # Add to free user quota
            user.quota_limit += bonus_amount
            
            # Create usage record
            usage_record = UsageRecord(
                user_id=user_id,
                usage_type="bonus_quota",
                amount=bonus_amount,
                description=reason
            )
            self.db.add(usage_record)
        
        self.db.commit()
        logger.info(f"Added {bonus_amount} bonus quota to user {user_id}: {reason}")
        return True
    
    def get_quota_warning_threshold(self, user_id: int) -> Dict[str, Any]:
        """Get quota warning information for user."""
        quota_info = self.check_quota_availability(user_id)
        if not quota_info["available"] and quota_info["remaining"] == 0:
            return {
                "warning_level": "exhausted",
                "message": "翻译次数已用完，请升级套餐",
                "show_upgrade_prompt": True
            }
        
        remaining = quota_info["remaining"]
        monthly_quota = quota_info.get("monthly_quota", 1)
        usage_percent = ((monthly_quota - remaining) / monthly_quota) * 100 if monthly_quota > 0 else 100
        
        if remaining <= 1:
            return {
                "warning_level": "critical",
                "message": f"剩余 {remaining} 次翻译机会",
                "show_upgrade_prompt": True
            }
        elif usage_percent >= 80:
            return {
                "warning_level": "warning",
                "message": f"已使用 {usage_percent:.0f}% 的翻译次数",
                "show_upgrade_prompt": True
            }
        else:
            return {
                "warning_level": "normal",
                "message": f"剩余 {remaining} 次翻译机会",
                "show_upgrade_prompt": False
            }
    
    def get_quota_reset_schedule(self, user_id: int) -> Dict[str, Any]:
        """Get quota reset schedule information."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Check subscription
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            # Subscription resets at end_date
            return {
                "plan_type": subscription.plan_type,
                "reset_date": subscription.end_date.isoformat() if subscription.end_date else None,
                "next_reset": subscription.end_date.isoformat() if subscription.end_date else None,
                "days_until_reset": self._calculate_days_until(subscription.end_date) if subscription.end_date else None
            }
        else:
            # Free user quota resets daily
            reset_date = user.quota_reset_date
            return {
                "plan_type": "free",
                "reset_date": reset_date.isoformat() if reset_date else None,
                "next_reset": reset_date.isoformat() if reset_date else None,
                "days_until_reset": self._calculate_days_until(reset_date) if reset_date else None
            }
    
    def check_quota_period_reset_needed(self, user_id: int) -> Dict[str, Any]:
        """Check if user's quota period needs to be reset."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        now = datetime.utcnow()
        
        # Check subscription
        subscription = self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
        
        if subscription:
            # Check if subscription has expired
            if subscription.end_date and now >= subscription.end_date:
                return {
                    "needs_reset": True,
                    "plan_type": subscription.plan_type,
                    "current_quota": subscription.remaining_quota,
                    "new_quota": subscription.monthly_quota,
                    "reset_date": now.isoformat()
                }
            else:
                return {
                    "needs_reset": False,
                    "plan_type": subscription.plan_type,
                    "current_quota": subscription.remaining_quota,
                    "new_quota": subscription.remaining_quota
                }
        else:
            # Check if free user quota needs reset (daily reset)
            reset_date = user.quota_reset_date
            if reset_date and now >= reset_date:
                return {
                    "needs_reset": True,
                    "plan_type": "free",
                    "current_quota": user.remaining_quota,
                    "new_quota": user.quota_limit,
                    "reset_date": now.isoformat()
                }
            else:
                return {
                    "needs_reset": False,
                    "plan_type": "free",
                    "current_quota": user.remaining_quota,
                    "new_quota": user.remaining_quota
                }
    
    def get_quota_usage_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get quota usage analytics for a time period."""
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get usage records for the period
        usage_records = self.db.query(UsageRecord).filter(
            and_(
                UsageRecord.user_id == user_id,
                UsageRecord.created_at >= start_date,
                UsageRecord.created_at <= end_date,
                UsageRecord.usage_type == "translation"
            )
        ).all()
        
        # Calculate daily usage
        daily_usage = {}
        for record in usage_records:
            date_str = record.created_at.strftime("%Y-%m-%d")
            daily_usage[date_str] = daily_usage.get(date_str, 0) + record.amount
        
        total_used = len(usage_records)
        
        # Get current quota info
        quota_info = self.check_quota_availability(user_id)
        total_quota = quota_info.get("monthly_quota", 1)
        utilization_percent = (total_used / total_quota) * 100 if total_quota > 0 else 100
        average_daily = total_used / days if days > 0 else 0
        
        return {
            "period_days": days,
            "total_used": total_used,
            "total_quota": total_quota,
            "utilization_percent": round(utilization_percent, 2),
            "daily_usage": daily_usage,
            "average_daily": round(average_daily, 2),
            "quota_info": quota_info
        }
    
    def _calculate_days_until(self, target_date: Optional[datetime]) -> Optional[int]:
        """Calculate days until target date."""
        if not target_date:
            return None
        
        now = datetime.utcnow()
        diff = target_date - now
        return max(0, diff.days)