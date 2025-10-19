from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_type = Column(String(20), nullable=False)  # free, basic_vip, premium_vip
    status = Column(String(20), nullable=False, default="active")  # active, cancelled, expired
    start_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    monthly_quota = Column(Integer, nullable=False)  # 1 for free, 10 for basic, 100 for premium
    used_quota = Column(Integer, nullable=False, default=0)
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscription")
    payment_orders = relationship("PaymentOrder", back_populates="subscription")

    @property
    def remaining_quota(self) -> int:
        return max(0, self.monthly_quota - self.used_quota)

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.end_date and self.end_date < func.now():
            return False
        return True

    @property
    def is_quota_available(self) -> bool:
        return self.is_active and self.remaining_quota > 0

    def use_quota(self, amount: int = 1) -> bool:
        """Use quota, returns True if successful"""
        if not self.is_quota_available:
            return False
        self.used_quota += amount
        return True

    def reset_quota(self):
        """Reset monthly quota"""
        self.used_quota = 0

class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    plan_type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="CNY")
    payment_method = Column(String(20), nullable=False)  # wechat, alipay
    payment_status = Column(String(20), default="pending")  # pending, paid, failed, cancelled
    transaction_id = Column(String(64), nullable=True)  # Third-party payment transaction ID
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="payment_orders")
    subscription = relationship("Subscription", back_populates="payment_orders")

    @property
    def is_paid(self) -> bool:
        return self.payment_status == "paid"

class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    translation_id = Column(Integer, ForeignKey("translations.id"), nullable=True)
    usage_type = Column(String(20), nullable=False)  # translation, quota_reset, etc.
    amount = Column(Integer, nullable=False, default=1)  # Number of quota units used
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_records")
    translation = relationship("Translation", back_populates="usage_record")