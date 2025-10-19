"""
Translation service for media transcription tasks.

This module provides business logic for translation processing,
including file handling, speech recognition, and result management.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from pathlib import Path

from app.models.translation import Translation
from app.models.user import User
from app.models.subscription import UsageRecord
from app.core.logging import get_logger
from app.services.speech_service import SpeechService, SpeechProvider
from app.utils.audio_extractor import AudioExtractor
from app.utils.media_detector import MediaDetector
from app.services.quota_service import QuotaService

logger = get_logger(__name__)


class TranslationService:
    """Service for translation and transcription operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.speech_service = SpeechService()
        self.audio_extractor = AudioExtractor()
        self.media_detector = MediaDetector()
        self.quota_service = QuotaService(db)
    
    def create_translation_task(
        self,
        user_id: int,
        file_type: str,
        original_filename: Optional[str] = None,
        original_file_url: Optional[str] = None,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Translation:
        """Create a new translation task."""
        translation = Translation(
            user_id=user_id,
            task_id=uuid.uuid4(),
            file_type=file_type,
            original_filename=original_filename,
            original_file_url=original_file_url,
            file_size=file_size,
            mime_type=mime_type,
            duration_seconds=duration_seconds,
            metadata=str(metadata) if metadata else None
        )
        
        self.db.add(translation)
        self.db.commit()
        self.db.refresh(translation)
        
        logger.info(f"Created translation task: {translation.task_id}")
        return translation
    
    def get_translation_by_id(self, translation_id: int) -> Optional[Translation]:
        """Get translation by database ID."""
        return self.db.query(Translation).filter(Translation.id == translation_id).first()
    
    def get_translation_by_task_id(self, task_id: str) -> Optional[Translation]:
        """Get translation by task ID."""
        try:
            task_uuid = uuid.UUID(task_id)
            return self.db.query(Translation).filter(Translation.task_id == task_uuid).first()
        except ValueError:
            return None
    
    def get_user_translations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Translation]:
        """Get user's translation history."""
        query = self.db.query(Translation).filter(Translation.user_id == user_id)
        
        if status:
            query = query.filter(Translation.processing_status == status)
        
        return query.order_by(Translation.created_at.desc()).offset(offset).limit(limit).all()
    
    def start_translation_processing(self, task_id: str) -> bool:
        """Mark translation as started processing."""
        translation = self.get_translation_by_task_id(task_id)
        if not translation:
            return False
        
        translation.mark_as_started()
        self.db.commit()
        
        logger.info(f"Started processing translation: {task_id}")
        return True
    
    def complete_translation(
        self,
        task_id: str,
        transcribed_text: str,
        confidence_score: float = 0.0,
        service_provider: Optional[str] = None,
        service_request_id: Optional[str] = None,
        service_cost: Optional[float] = None
    ) -> bool:
        """Complete translation with results."""
        translation = self.get_translation_by_task_id(task_id)
        if not translation:
            return False
        
        translation.mark_as_completed(transcribed_text, confidence_score)
        
        if service_provider:
            translation.service_provider = service_provider
        if service_request_id:
            translation.service_request_id = service_request_id
        if service_cost is not None:
            translation.service_cost = service_cost
        
        self.db.commit()
        
        logger.info(f"Completed translation: {task_id}")
        return True
    
    def fail_translation(self, task_id: str, error_message: str) -> bool:
        """Mark translation as failed."""
        translation = self.get_translation_by_task_id(task_id)
        if not translation:
            return False
        
        translation.mark_as_failed(error_message)
        self.db.commit()
        
        logger.error(f"Failed translation: {task_id}, error: {error_message}")
        return True
    
    def update_translation_progress(
        self,
        task_id: str,
        **kwargs
    ) -> bool:
        """Update translation metadata and progress."""
        translation = self.get_translation_by_task_id(task_id)
        if not translation:
            return False
        
        for key, value in kwargs.items():
            if hasattr(translation, key):
                setattr(translation, key, value)
        
        self.db.commit()
        return True
    
    def get_pending_translations(self, limit: int = 50) -> List[Translation]:
        """Get translations pending processing."""
        return self.db.query(Translation).filter(
            Translation.processing_status == "pending"
        ).order_by(Translation.created_at).limit(limit).all()
    
    def get_processing_translations(self, limit: int = 50) -> List[Translation]:
        """Get translations currently being processed."""
        return self.db.query(Translation).filter(
            Translation.processing_status == "processing"
        ).order_by(Translation.processing_started_at).limit(limit).all()
    
    def get_translation_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get translation statistics."""
        query = self.db.query(Translation)
        if user_id:
            query = query.filter(Translation.user_id == user_id)
        
        total = query.count()
        completed = query.filter(Translation.processing_status == "completed").count()
        failed = query.filter(Translation.processing_status == "failed").count()
        processing = query.filter(Translation.processing_status == "processing").count()
        pending = query.filter(Translation.processing_status == "pending").count()
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "processing": processing,
            "pending": pending,
            "success_rate": (completed / total * 100) if total > 0 else 0
        }
    
    def use_quota_for_translation(self, task_id: str) -> bool:
        """Mark quota as used for completed translation."""
        translation = self.get_translation_by_task_id(task_id)
        if not translation or not translation.is_completed:
            return False
        
        if translation.is_quota_used:
            return True  # Already used
        
        # Create usage record
        usage_record = UsageRecord(
            user_id=translation.user_id,
            translation_id=translation.id,
            usage_type="translation",
            amount=1,
            description=f"Translation task: {translation.task_id}"
        )
        
        self.db.add(usage_record)
        translation.use_quota()
        self.db.commit()
        
        logger.info(f"Used quota for translation: {task_id}")
        return True
    
    def cleanup_old_translations(self, days: int = 30) -> int:
        """Clean up old completed translations."""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_translations = self.db.query(Translation).filter(
            and_(
                Translation.processing_status.in_(["completed", "failed"]),
                Translation.created_at < cutoff_date
            )
        ).all()
        
        count = len(old_translations)
        
        for translation in old_translations:
            self.db.delete(translation)
        
        self.db.commit()
        
        logger.info(f"Cleaned up {count} old translations")
        return count
    
    def get_translation_status_with_progress(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get detailed translation status with progress information.
        
        Args:
            task_id: Translation task ID
            
        Returns:
            Detailed status information with progress
        """
        try:
            translation = self.get_translation_by_task_id(task_id)
            if not translation:
                return {
                    "task_id": task_id,
                    "status": "not_found",
                    "error": "Translation task not found"
                }
            
            # Calculate progress based on status
            progress_percentage = self._calculate_progress_percentage(translation)
            estimated_completion = self._estimate_completion_time(translation)
            
            status_info = {
                "task_id": task_id,
                "processing_status": translation.processing_status,
                "progress_percentage": progress_percentage,
                "processing_started_at": translation.processing_started_at.isoformat() if translation.processing_started_at else None,
                "processing_completed_at": translation.processing_completed_at.isoformat() if translation.processing_completed_at else None,
                "estimated_completion": estimated_completion,
                "error_message": translation.processing_error,
                "created_at": translation.created_at.isoformat(),
                "file_info": {
                    "original_filename": translation.original_filename,
                    "file_type": translation.file_type,
                    "file_size": translation.file_size,
                    "duration_seconds": translation.duration_seconds
                },
                "result_info": None
            }
            
            # Add result information if completed
            if translation.is_completed:
                status_info["result_info"] = {
                    "transcribed_text": translation.transcribed_text,
                    "confidence_score": translation.confidence_score,
                    "word_count": translation.word_count,
                    "service_provider": translation.service_provider,
                    "processing_duration": translation.processing_duration
                }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Status tracking error for {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"Failed to get status: {str(e)}"
            }
    
    def _calculate_progress_percentage(self, translation: Translation) -> int:
        """Calculate progress percentage based on translation status."""
        if translation.is_completed:
            return 100
        elif translation.is_failed:
            return 0
        elif translation.is_processing:
            # Estimate progress based on time elapsed
            if translation.processing_started_at:
                elapsed = (datetime.utcnow() - translation.processing_started_at).total_seconds()
                
                # Estimate total processing time
                if translation.original_file_url:
                    time_estimate = self.estimate_processing_time(
                        translation.original_file_url,
                        translation.file_type
                    )
                    estimated_total = time_estimate.get("estimated_seconds", 30)
                    
                    # Calculate progress (cap at 95% to avoid showing 100% before completion)
                    progress = min((elapsed / estimated_total) * 100, 95)
                    return int(progress)
            
            return 10  # Started processing but no time estimate yet
        else:
            # Pending status
            return 0
    
    def _estimate_completion_time(self, translation: Translation) -> Optional[str]:
        """Estimate completion time for translation."""
        try:
            if translation.is_completed:
                return translation.processing_completed_at.isoformat()
            elif translation.is_failed:
                return None
            elif translation.is_processing and translation.processing_started_at:
                # Estimate based on file duration and processing time
                if translation.original_file_url:
                    time_estimate = self.estimate_processing_time(
                        translation.original_file_url,
                        translation.file_type
                    )
                    
                    estimated_seconds = time_estimate.get("estimated_seconds", 30)
                    completion_time = translation.processing_started_at + timedelta(seconds=estimated_seconds)
                    return completion_time.isoformat()
            
            return None
            
        except Exception as e:
            logger.error(f"Completion time estimation error: {str(e)}")
            return None
    
    def get_translation_notifications(
        self,
        user_id: int,
        unread_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get translation notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Whether to return only unread notifications
            
        Returns:
            List of notification objects
        """
        try:
            # Get recent translations that might need notifications
            recent_hours = 24
            cutoff_time = datetime.utcnow() - timedelta(hours=recent_hours)
            
            translations = self.db.query(Translation).filter(
                and_(
                    Translation.user_id == user_id,
                    Translation.created_at >= cutoff_time,
                    Translation.processing_status.in_(["completed", "failed"])
                )
            ).order_by(Translation.created_at.desc()).limit(50).all()
            
            notifications = []
            
            for translation in translations:
                notification = {
                    "id": f"trans_{translation.id}",
                    "type": "translation_completed" if translation.is_completed else "translation_failed",
                    "task_id": str(translation.task_id),
                    "title": "翻译完成" if translation.is_completed else "翻译失败",
                    "message": self._generate_notification_message(translation),
                    "data": {
                        "translation_id": translation.id,
                        "filename": translation.original_filename,
                        "status": translation.processing_status,
                        "confidence": translation.confidence_score if translation.is_completed else None,
                        "error": translation.processing_error if translation.is_failed else None
                    },
                    "created_at": translation.processing_completed_at.isoformat() if translation.processing_completed_at else translation.created_at.isoformat(),
                    "read": False  # TODO: Implement read status tracking
                }
                
                notifications.append(notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Notification retrieval error for user {user_id}: {str(e)}")
            return []
    
    def _generate_notification_message(self, translation: Translation) -> str:
        """Generate user-friendly notification message."""
        if translation.is_completed:
            filename = translation.original_filename or "文件"
            confidence = translation.confidence_score or 0
            
            if confidence >= 0.9:
                quality = "高质量"
            elif confidence >= 0.7:
                quality = "中等质量"
            else:
                quality = "基础质量"
            
            return f"文件「{filename}」的语音识别已完成，识别质量：{quality}"
        else:
            filename = translation.original_filename or "文件"
            error = translation.processing_error or "未知错误"
            
            # Truncate long error messages
            if len(error) > 50:
                error = error[:50] + "..."
            
            return f"文件「{filename}」的语音识别失败：{error}"
    
    def handle_translation_error(
        self,
        task_id: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle translation errors with proper logging and recovery.
        
        Args:
            task_id: Translation task ID
            error: The error that occurred
            context: Additional context information
            
        Returns:
            Error handling result
        """
        try:
            logger.error(f"Translation error for task {task_id}: {str(error)}", exc_info=True)
            
            # Categorize error type
            error_type = self._categorize_error(error)
            
            # Determine if retry is appropriate
            should_retry = self._should_retry_error(error_type, context)
            
            # Update translation record
            error_message = f"{error_type}: {str(error)}"
            self.fail_translation(task_id, error_message)
            
            # Log error with context
            context_info = context or {}
            context_info.update({
                "task_id": task_id,
                "error_type": error_type,
                "should_retry": should_retry,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.error(f"Translation error context: {context_info}")
            
            # Return error handling result
            return {
                "task_id": task_id,
                "error_type": error_type,
                "error_message": error_message,
                "should_retry": should_retry,
                "recovery_actions": self._get_recovery_actions(error_type),
                "context": context_info
            }
            
        except Exception as e:
            logger.error(f"Error handling failed for task {task_id}: {str(e)}")
            return {
                "task_id": task_id,
                "error_type": "handling_error",
                "error_message": f"Error handling failed: {str(e)}",
                "should_retry": False,
                "recovery_actions": ["Contact support"]
            }
    
    def _categorize_error(self, error: Exception) -> str:
        """Categorize error type for appropriate handling."""
        error_message = str(error).lower()
        error_class = error.__class__.__name__.lower()
        
        # Network/Connectivity errors
        if any(term in error_message for term in ["connection", "network", "timeout", "unreachable"]):
            return "network_error"
        
        # File system errors
        if any(term in error_message for term in ["file not found", "permission denied", "disk full", "no space"]):
            return "file_system_error"
        
        # API/Service errors
        if any(term in error_message for term in ["api", "service", "authentication", "rate limit", "quota"]):
            return "service_error"
        
        # Audio processing errors
        if any(term in error_message for term in ["audio", "codec", "format", "decode"]):
            return "audio_processing_error"
        
        # Database errors
        if any(term in error_message for term in ["database", "sql", "connection", "timeout"]):
            return "database_error"
        
        # Memory/resource errors
        if any(term in error_message for term in ["memory", "resource", "out of memory"]):
            return "resource_error"
        
        # Validation errors
        if any(term in error_class for term in ["validation", "value"]):
            return "validation_error"
        
        # Default categorization
        return "unknown_error"
    
    def _should_retry_error(self, error_type: str, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if an error type should be retried."""
        retryable_errors = [
            "network_error",
            "service_error", 
            "database_error",
            "resource_error"
        ]
        
        non_retryable_errors = [
            "validation_error",
            "file_system_error",
            "audio_processing_error"
        ]
        
        if error_type in non_retryable_errors:
            return False
        
        if error_type in retryable_errors:
            # Check retry count from context
            if context:
                retry_count = context.get("retry_count", 0)
                max_retries = context.get("max_retries", 3)
                return retry_count < max_retries
            
            return True
        
        # Unknown errors get one retry attempt
        return context is None or context.get("retry_count", 0) == 0
    
    def _get_recovery_actions(self, error_type: str) -> List[str]:
        """Get recommended recovery actions for error type."""
        action_map = {
            "network_error": ["Check internet connection", "Retry after 30 seconds", "Contact support if persistent"],
            "file_system_error": ["Check file permissions", "Verify file exists", "Upload file again"],
            "service_error": ["Check service status", "Retry with different provider", "Contact support"],
            "audio_processing_error": ["Check audio file format", "Try different file", "Convert to supported format"],
            "database_error": ["Retry operation", "Contact support if persistent"],
            "resource_error": ["Wait and retry", "Try with smaller file", "Contact support"],
            "validation_error": ["Check input parameters", "Verify file format", "Correct data and retry"],
            "unknown_error": ["Retry operation", "Contact support", "Check system status"]
        }
        
        return action_map.get(error_type, ["Contact support"])
    
    def create_error_report(
        self,
        task_id: str,
        error_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a detailed error report for debugging.
        
        Args:
            task_id: Translation task ID
            error_info: Error information from handle_translation_error
            
        Returns:
            Detailed error report
        """
        try:
            translation = self.get_translation_by_task_id(task_id)
            
            report = {
                "report_id": f"error_{task_id}_{int(datetime.utcnow().timestamp())}",
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error_info": error_info,
                "translation_details": {
                    "user_id": translation.user_id if translation else None,
                    "original_filename": translation.original_filename if translation else None,
                    "file_type": translation.file_type if translation else None,
                    "file_size": translation.file_size if translation else None,
                    "processing_status": translation.processing_status if translation else None,
                    "created_at": translation.created_at.isoformat() if translation else None,
                    "processing_started_at": translation.processing_started_at.isoformat() if translation and translation.processing_started_at else None
                },
                "system_info": {
                    "version": "1.0.0",
                    "environment": "production"  # TODO: Get from config
                },
                "debug_info": {
                    "stack_trace": error_info.get("context", {}).get("stack_trace"),
                    "file_info": self._get_debug_file_info(task_id) if translation else None,
                    "processing_log": self._get_processing_log(task_id)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to create error report for {task_id}: {str(e)}")
            return {
                "report_id": f"error_{task_id}_failed",
                "error": f"Failed to create error report: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_debug_file_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get debug information about the file being processed."""
        try:
            # In a real implementation, this would gather file metadata,
            # checksum, and other debug information
            return {
                "debug_info": "File debug information would be collected here"
            }
        except Exception:
            return None
    
    def _get_processing_log(self, task_id: str) -> List[str]:
        """Get processing log entries for the task."""
        try:
            # In a real implementation, this would retrieve detailed logs
            # from the logging system or database
            return [
                f"Task {task_id} created",
                "Validation started",
                "Processing initiated",
                "Error occurred"
            ]
        except Exception:
            return []
    
    async def process_translation_task(
        self,
        task_id: str,
        language: str = "zh-CN",
        provider: SpeechProvider = SpeechProvider.ALIBABA
    ) -> Dict[str, Any]:
        """
        Complete speech transcription workflow for a translation task.
        
        This method handles the entire process from file validation to
        transcription result storage, including audio extraction for videos.
        
        Args:
            task_id: Translation task ID
            language: Target language for transcription
            provider: Speech recognition provider
            
        Returns:
            Processing result with transcription data
        """
        try:
            # Get translation task
            translation = self.get_translation_by_task_id(task_id)
            if not translation:
                return {
                    "success": False,
                    "error": "Translation task not found"
                }
            
            # Check quota availability before starting processing
            quota_check = self.quota_service.check_quota_availability(translation.user_id, 1)
            if not quota_check["available"]:
                logger.warning(f"User {translation.user_id} has insufficient quota for translation {task_id}")
                return {
                    "success": False,
                    "error": "Insufficient quota",
                    "quota_info": {
                        "remaining": quota_check["remaining"],
                        "plan_type": quota_check["plan_type"],
                        "show_upgrade_prompt": True,
                        "message": "翻译次数不足，请升级套餐"
                    }
                }
            
            # Mark as started processing
            self.start_translation_processing(task_id)
            
            # Process based on file type
            if translation.file_type == "video":
                result = await self._process_video_file(translation, language, provider)
            else:
                result = await self._process_audio_file(translation, language, provider)
            
            # Store transcription result
            if result["success"]:
                self.complete_translation(
                    task_id=task_id,
                    transcribed_text=result["text"],
                    confidence_score=result["confidence"],
                    service_provider=result["provider"],
                    service_request_id=result.get("request_id"),
                    service_cost=result.get("cost")
                )
                
                # Use quota for successful translation
                quota_usage = self.quota_service.use_quota(
                    user_id=translation.user_id,
                    amount=1,
                    usage_type="translation",
                    description=f"Translation task: {task_id}",
                    translation_id=translation.id
                )
                
                if quota_usage["success"]:
                    logger.info(f"Quota used successfully for translation {task_id}")
                    result["quota_used"] = True
                    result["remaining_quota"] = quota_usage["remaining"]
                else:
                    logger.error(f"Failed to use quota for translation {task_id}: {quota_usage.get('error')}")
                    result["quota_used"] = False
                    result["quota_error"] = quota_usage.get("error")
            else:
                self.fail_translation(task_id, result["error"])
            
            return result
            
        except Exception as e:
            logger.error(f"Translation processing error for {task_id}: {str(e)}")
            self.fail_translation(task_id, f"Processing failed: {str(e)}")
            return {
                "success": False,
                "error": f"Translation processing failed: {str(e)}"
            }
    
    async def _process_video_file(
        self,
        translation: Translation,
        language: str,
        provider: SpeechProvider
    ) -> Dict[str, Any]:
        """Process video file by extracting audio first."""
        try:
            logger.info(f"Processing video file: {translation.original_filename}")
            
            # Extract audio from video
            video_path = translation.original_file_url
            if not video_path or not Path(video_path).exists():
                return {
                    "success": False,
                    "error": "Video file not found or inaccessible"
                }
            
            # Extract audio
            extraction_result = await self.audio_extractor.extract_audio_from_video(
                video_path=video_path,
                output_format="mp3",
                quality="medium"
            )
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": f"Audio extraction failed: {extraction_result['error']}"
                }
            
            audio_path = extraction_result["output_path"]
            
            try:
                # Transcribe extracted audio
                transcription_result = await self.speech_service.transcribe_audio_file(
                    audio_url=audio_path,
                    file_type="audio",
                    language=language,
                    provider=provider
                )
                
                # Clean up extracted audio file
                await asyncio.to_thread(Path(audio_path).unlink)
                
                return transcription_result
                
            except Exception as e:
                # Clean up audio file on error
                try:
                    await asyncio.to_thread(Path(audio_path).unlink)
                except:
                    pass
                raise e
                
        except Exception as e:
            logger.error(f"Video processing error: {str(e)}")
            return {
                "success": False,
                "error": f"Video processing failed: {str(e)}"
            }
    
    async def _process_audio_file(
        self,
        translation: Translation,
        language: str,
        provider: SpeechProvider
    ) -> Dict[str, Any]:
        """Process audio file directly."""
        try:
            logger.info(f"Processing audio file: {translation.original_filename}")
            
            audio_url = translation.original_file_url
            if not audio_url:
                return {
                    "success": False,
                    "error": "Audio file URL not found"
                }
            
            # Transcribe audio directly
            result = await self.speech_service.transcribe_audio_file(
                audio_url=audio_url,
                file_type=translation.file_type,
                language=language,
                provider=provider
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Audio processing error: {str(e)}")
            return {
                "success": False,
                "error": f"Audio processing failed: {str(e)}"
            }
    
    def estimate_processing_time(
        self,
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Estimate processing time for a media file.
        
        Args:
            file_path: Path to the media file
            file_type: Type of media file
            
        Returns:
            Processing time estimation
        """
        try:
            # Get media metadata
            metadata = self.media_detector.get_media_metadata(file_path)
            
            if "error" in metadata:
                return {
                    "estimated_seconds": 30,
                    "confidence": "low"
                }
            
            duration = metadata.get("duration_seconds", 30)
            
            if file_type == "video":
                # Video needs audio extraction + transcription
                estimated_time = duration * 0.4  # 40% of duration
            else:
                # Audio only needs transcription
                estimated_time = duration * 0.25  # 25% of duration
            
            # Add base overhead
            estimated_time += 5  # 5 seconds base overhead
            
            return {
                "estimated_seconds": max(estimated_time, 10),  # Minimum 10 seconds
                "estimated_minutes": max(estimated_time / 60, 0.2),
                "confidence": "medium" if duration > 0 else "low",
                "factors": {
                    "duration": duration,
                    "file_type": file_type,
                    "base_overhead": 5
                }
            }
            
        except Exception as e:
            logger.error(f"Processing time estimation error: {str(e)}")
            return {
                "estimated_seconds": 30,
                "confidence": "low"
            }
    
    def validate_media_file(
        self,
        file_path: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Validate media file before processing.
        
        Args:
            file_path: Path to the media file
            user_id: User ID requesting validation
            
        Returns:
            Validation result with file information
        """
        try:
            # Check if file exists
            if not Path(file_path).exists():
                return {
                    "valid": False,
                    "error": "File not found"
                }
            
            # Get file information
            metadata = self.media_detector.get_media_metadata(file_path)
            
            if "error" in metadata:
                return {
                    "valid": False,
                    "error": f"File analysis failed: {metadata['error']}"
                }
            
            # Validate file size
            file_size_mb = metadata["file_size_mb"]
            
            # Check size limits
            if metadata["category"] == "video":
                max_size_mb = 200  # 200MB for videos
            elif metadata["category"] == "audio":
                max_size_mb = 50   # 50MB for audio
            else:
                max_size_mb = 10   # 10MB for other files
            
            if file_size_mb > max_size_mb:
                return {
                    "valid": False,
                    "error": f"File too large: {file_size_mb:.1f}MB. Maximum: {max_size_mb}MB"
                }
            
            # Check if format is supported
            if not metadata["is_supported"]:
                return {
                    "valid": False,
                    "error": f"Unsupported file format: {metadata.get('format', 'unknown')}"
                }
            
            # Get processing requirements
            requirements = self.media_detector.get_processing_requirements(file_path)
            
            return {
                "valid": True,
                "file_info": metadata,
                "processing_requirements": requirements,
                "max_size_mb": max_size_mb
            }
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return {
                "valid": False,
                "error": f"File validation failed: {str(e)}"
            }
    
    async def queue_translation_task(
        self,
        task_id: str,
        priority: str = "normal"
    ) -> bool:
        """
        Queue translation task for background processing.
        
        Args:
            task_id: Translation task ID
            priority: Processing priority (high, normal, low)
            
        Returns:
            True if successfully queued
        """
        try:
            # In a production system, this would integrate with a job queue
            # like Celery, RQ, or Azure Queue Storage
            
            # For now, we'll simulate queuing by returning True
            # The actual processing would be handled by background workers
            
            logger.info(f"Queued translation task {task_id} with priority {priority}")
            
            # TODO: Integrate with actual job queue system
            # Example with Celery:
            # from app.tasks import process_translation_task
            # process_translation_task.delay(task_id, priority)
            
            return True
            
        except Exception as e:
            logger.error(f"Task queuing error for {task_id}: {str(e)}")
            return False
    
    def get_processing_queue_status(self) -> Dict[str, Any]:
        """
        Get current status of the translation processing queue.
        
        Returns:
            Queue status information
        """
        try:
            # In production, this would query the actual job queue system
            
            # Mock implementation
            pending_count = self.db.query(Translation).filter(
                Translation.processing_status == "pending"
            ).count()
            
            processing_count = self.db.query(Translation).filter(
                Translation.processing_status == "processing"
            ).count()
            
            return {
                "pending_tasks": pending_count,
                "processing_tasks": processing_count,
                "queue_capacity": 1000,
                "queue_health": "healthy",
                "estimated_wait_time": max(pending_count * 30, 0),  # seconds
                "workers_available": 5,
                "workers_busy": processing_count
            }
            
        except Exception as e:
            logger.error(f"Queue status error: {str(e)}")
            return {
                "error": str(e),
                "queue_health": "error"
            }