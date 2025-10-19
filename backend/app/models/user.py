"""
User model for authentication and account management.

This module defines the User model for handling user accounts,
authentication, and subscription information.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models import Base


class User(Base):
    """User account model for authentication and profile management."""
    
    __tablename__ = "users"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String(128), unique=True, nullable=False, index=True)
    unionid = Column(String(128), nullable=True, index=True)
    
    # Profile information
    username = Column(String(100), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Subscription information
    subscription_level = Column(String(50), default="free", nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Quota management
    quota_used = Column(Integer, default=0, nullable=False)
    quota_limit = Column(Integer, default=1, nullable=False)
    quota_reset_date = Column(Date, nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Usage tracking
    total_translations = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences (stored as JSON)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    # Relationships
    translations = relationship("Translation", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payment_orders = relationship("PaymentOrder", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_openid", "openid"),
        Index("idx_users_subscription", "subscription_level"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_subscription_status", "subscription_status"),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, openid='{self.openid}', subscription_level='{self.subscription_level}')>"
    
    @property
    def remaining_quota(self) -> int:
        """Calculate remaining quota for current period."""
        return max(0, self.quota_limit - self.quota_used)
    
    @property
    def is_subscription_active(self) -> bool:
        """Check if user's subscription is currently active."""
        if self.subscription_level == "free":
            return True
        
        if not self.subscription_expires_at:
            return False
            
        return self.subscription_expires_at > func.now()
    
    def increment_quota_used(self):
        """Increment quota used by 1."""
        self.quota_used += 1
        
    def reset_quota(self, new_limit: int):
        """Reset quota for new period."""
        self.quota_used = 0
        self.quota_limit = new_limit