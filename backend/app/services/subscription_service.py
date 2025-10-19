"""
Subscription service for managing user subscriptions and payments.

This module provides business logic for subscription management,
including plan upgrades, payments, and quota management.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.subscription import Subscription, PaymentOrder
from app.models.user import User
from app.core.logging import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    """Service for subscription management operations."""
    
    # Subscription plan definitions
    PLANS = {
        "free": {
            "name": "免费版",
            "monthly_quota": 1,
            "price": Decimal("0.00"),
            "duration_days": None,  # Unlimited
            "features": ["每月1次翻译", "基础语音识别"]
        },
        "basic_vip": {
            "name": "基础VIP",
            "monthly_quota": 10,
            "price": Decimal("9.90"),
            "duration_days": 30,
            "features": ["每月10次翻译", "高质量语音识别", "优先处理"]
        },
        "premium_vip": {
            "name": "高级VIP", 
            "monthly_quota": 100,
            "price": Decimal("29.90"),
            "duration_days": 30,
            "features": ["每月100次翻译", "最高质量语音识别", "最快处理", "客服支持"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
    
    def create_subscription(
        self,
        user_id: int,
        plan_type: str,
        payment_order_id: Optional[int] = None
    ) -> Subscription:
        """Create a new subscription for user."""
        if plan_type not in self.PLANS:
            raise ValueError(f"Invalid plan type: {plan_type}")
        
        plan = self.PLANS[plan_type]
        
        # Calculate end date
        end_date = None
        if plan["duration_days"]:
            end_date = datetime.utcnow() + timedelta(days=plan["duration_days"])
        
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            status="active",
            start_date=datetime.utcnow(),
            end_date=end_date,
            monthly_quota=plan["monthly_quota"],
            used_quota=0
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        logger.info(f"Created {plan_type} subscription for user {user_id}")
        return subscription
    
    def upgrade_subscription(
        self,
        user_id: int,
        new_plan_type: str,
        payment_method: str = "wechat"
    ) -> PaymentOrder:
        """Upgrade user subscription to a new plan."""
        if new_plan_type not in self.PLANS:
            raise ValueError(f"Invalid plan type: {new_plan_type}")
        
        plan = self.PLANS[new_plan_type]
        
        # Create payment order
        order = PaymentOrder(
            user_id=user_id,
            plan_type=new_plan_type,
            amount=plan["price"],
            payment_method=payment_method,
            payment_status="pending",
            order_no=self._generate_order_no()
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Created payment order {order.order_no} for plan upgrade to {new_plan_type}")
        return order
    
    def process_payment_success(
        self,
        order_no: str,
        transaction_id: str,
        payment_method: str = "wechat"
    ) -> bool:
        """Process successful payment and activate subscription."""
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).first()
        
        if not order:
            logger.error(f"Payment order not found: {order_no}")
            return False
        
        if order.is_paid:
            logger.warning(f"Order already paid: {order_no}")
            return True
        
        # Update payment status
        order.payment_status = "paid"
        order.transaction_id = transaction_id
        order.paid_at = datetime.utcnow()
        
        # Deactivate existing subscription
        existing_subscription = self.get_user_subscription(order.user_id)
        if existing_subscription:
            existing_subscription.status = "cancelled"
        
        # Create new subscription
        self.create_subscription(
            user_id=order.user_id,
            plan_type=order.plan_type,
            payment_order_id=order.id
        )
        
        # Link subscription to order
        new_subscription = self.get_user_subscription(order.user_id)
        if new_subscription:
            order.subscription_id = new_subscription.id
        
        self.db.commit()
        
        logger.info(f"Successfully processed payment for order: {order_no}")
        return True
    
    def cancel_subscription(self, user_id: int) -> bool:
        """Cancel user's active subscription."""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False
        
        subscription.status = "cancelled"
        self.db.commit()
        
        logger.info(f"Cancelled subscription for user {user_id}")
        return True
    
    def use_quota(self, user_id: int, amount: int = 1) -> bool:
        """Deduct quota from user's subscription."""
        subscription = self.get_user_subscription(user_id)
        if not subscription or not subscription.is_quota_available:
            return False
        
        success = subscription.use_quota(amount)
        if success:
            self.db.commit()
            logger.info(f"Used {amount} quota for user {user_id}")
        
        return success
    
    def reset_monthly_quota(self, user_id: int) -> bool:
        """Reset user's monthly quota."""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            return False
        
        subscription.reset_quota()
        self.db.commit()
        
        logger.info(f"Reset monthly quota for user {user_id}")
        return True
    
    def get_subscription_plans(self) -> Dict[str, Any]:
        """Get available subscription plans."""
        return self.PLANS
    
    def check_quota_availability(self, user_id: int, required_quota: int = 1) -> bool:
        """Check if user has enough quota available."""
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            # Check free user quota
            user = self.db.query(User).filter(User.id == user_id).first()
            return user.remaining_quota >= required_quota if user else False
        
        return subscription.remaining_quota >= required_quota
    
    def get_user_quota_info(self, user_id: int) -> Dict[str, Any]:
        """Get user's quota information."""
        subscription = self.get_user_subscription(user_id)
        
        if subscription:
            return {
                "plan_type": subscription.plan_type,
                "plan_name": self.PLANS[subscription.plan_type]["name"],
                "monthly_quota": subscription.monthly_quota,
                "used_quota": subscription.used_quota,
                "remaining_quota": subscription.remaining_quota,
                "is_active": subscription.is_active,
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None
            }
        else:
            # Free user info
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "plan_type": "free",
                    "plan_name": "免费版",
                    "monthly_quota": user.quota_limit,
                    "used_quota": user.quota_used,
                    "remaining_quota": user.remaining_quota,
                    "is_active": True,
                    "end_date": None
                }
        
        return {}
    
    def get_payment_history(self, user_id: int, limit: int = 20) -> List[PaymentOrder]:
        """Get user's payment history."""
        return self.db.query(PaymentOrder).filter(
            PaymentOrder.user_id == user_id
        ).order_by(PaymentOrder.created_at.desc()).limit(limit).all()
    
    def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """Get subscriptions expiring within specified days."""
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        return self.db.query(Subscription).filter(
            and_(
                Subscription.status == "active",
                Subscription.end_date <= cutoff_date,
                Subscription.end_date > datetime.utcnow()
            )
        ).all()
    
    def _generate_order_no(self) -> str:
        """Generate unique payment order number."""
        import time
        import random
        
        timestamp = str(int(time.time()))
        random_suffix = str(random.randint(1000, 9999))
        return f"SUB{timestamp}{random_suffix}"