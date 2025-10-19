"""
Translation model for media transcription tasks.

This module defines the Translation model for handling media files,
transcription results, and processing status.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, BigInteger, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models import Base


class Translation(Base):
    """Translation task model for media transcription processing."""
    
    __tablename__ = "translations"
    
    # Primary fields
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Source media information
    original_filename = Column(String(255), nullable=True)
    original_file_url = Column(String(1024), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String(50), nullable=False)  # audio, video, wechat_video, link
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Processing information
    processing_status = Column(String(50), default="pending", nullable=False, index=True)
    processing_error = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    transcribed_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    word_count = Column(Integer, nullable=True)
    
    # Third-party service information
    service_provider = Column(String(100), nullable=True)
    service_request_id = Column(String(128), nullable=True)
    service_cost = Column(Float, nullable=True)
    
    # Usage tracking
    is_quota_used = Column(Boolean, default=False, nullable=False)
    quota_deducted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata (stored as JSON)
    metadata = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="translations")
    usage_record = relationship("UsageRecord", back_populates="translation", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index("idx_translations_task_id", "task_id"),
        Index("idx_translations_user_id", "user_id"),
        Index("idx_translations_status", "processing_status"),
        Index("idx_translations_created_at", "created_at"),
        Index("idx_translations_user_status", "user_id", "processing_status"),
    )
    
    def __repr__(self):
        return f"<Translation(id={self.id}, task_id='{self.task_id}', status='{self.processing_status}')>"
    
    @property
    def is_completed(self) -> bool:
        """Check if translation processing is completed."""
        return self.processing_status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if translation processing has failed."""
        return self.processing_status == "failed"
    
    @property
    def is_processing(self) -> bool:
        """Check if translation is currently being processed."""
        return self.processing_status == "processing"
    
    @property
    def processing_duration(self) -> float:
        """Calculate processing duration in seconds."""
        if not self.processing_started_at or not self.processing_completed_at:
            return 0.0
        
        return (self.processing_completed_at - self.processing_started_at).total_seconds()
    
    def mark_as_started(self):
        """Mark translation as started processing."""
        self.processing_status = "processing"
        self.processing_started_at = func.now()
    
    def mark_as_completed(self, text: str, confidence: float = 0.0):
        """Mark translation as completed with results."""
        self.processing_status = "completed"
        self.processing_completed_at = func.now()
        self.transcribed_text = text
        self.confidence_score = confidence
        self.word_count = len(text.split()) if text else 0
    
    def mark_as_failed(self, error_message: str):
        """Mark translation as failed with error information."""
        self.processing_status = "failed"
        self.processing_completed_at = func.now()
        self.processing_error = error_message
    
    def use_quota(self):
        """Mark that quota has been used for this translation."""
        self.is_quota_used = True
        self.quota_deducted_at = func.now()