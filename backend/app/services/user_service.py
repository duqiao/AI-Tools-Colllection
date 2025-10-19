"""
User service for managing user accounts and authentication.

This module provides business logic for user management, including
registration, authentication, and profile management.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, date
from app.models.user import User
from app.models.subscription import Subscription
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_openid(self, openid: str) -> Optional[User]:
        """Get user by WeChat OpenID."""
        return self.db.query(User).filter(User.openid == openid).first()
    
    def create_user(self, openid: str, **kwargs) -> User:
        """Create a new user with WeChat OpenID."""
        user = User(
            openid=openid,
            **kwargs
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Create free subscription for new user
        self._create_free_subscription(user.id)
        
        logger.info(f"Created new user with ID: {user.id}")
        return user
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user information."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def get_or_create_user(self, openid: str, **kwargs) -> tuple[User, bool]:
        """Get existing user or create new one."""
        user = self.get_user_by_openid(openid)
        if user:
            return user, False
        
        user = self.create_user(openid, **kwargs)
        return user, True
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            )
        ).first()
    
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Update user preferences (stored as JSON)."""
        import json
        
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Merge with existing preferences
        existing_prefs = {}
        if user.preferences:
            try:
                existing_prefs = json.loads(user.preferences)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in user preferences for user {user_id}")
        
        existing_prefs.update(preferences)
        user.preferences = json.dumps(existing_prefs)
        
        self.db.commit()
        return True
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics and usage information."""
        from app.models.translation import Translation
        from app.models.usage_record import UsageRecord
        
        user = self.get_user_by_id(user_id)
        if not user:
            return {}
        
        # Get translation statistics
        total_translations = self.db.query(Translation).filter(
            Translation.user_id == user_id
        ).count()
        
        completed_translations = self.db.query(Translation).filter(
            and_(
                Translation.user_id == user_id,
                Translation.processing_status == "completed"
            )
        ).count()
        
        # Get current subscription info
        subscription = self.get_user_subscription(user_id)
        
        return {
            "user_id": user.id,
            "total_translations": total_translations,
            "completed_translations": completed_translations,
            "current_plan": subscription.plan_type if subscription else "free",
            "remaining_quota": subscription.remaining_quota if subscription else user.remaining_quota,
            "subscription_active": subscription.is_active if subscription else user.is_subscription_active,
            "created_at": user.created_at,
            "last_login": user.last_login_at
        }
    
    def _create_free_subscription(self, user_id: int) -> Subscription:
        """Create a free subscription for new user."""
        subscription = Subscription(
            user_id=user_id,
            plan_type="free",
            status="active",
            monthly_quota=1,
            used_quota=0
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription