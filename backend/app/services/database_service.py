"""
PostgreSQL Database Service Layer

This service layer provides high-level database operations and business logic
that span across multiple repositories. It acts as a middle layer between
the API endpoints and the individual repositories.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass

from app.core.postgres_db import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.job_repository import ProcessingJobRepository
from app.utils.postgres_errors import PostgresErrorHandler

logger = logging.getLogger(__name__)


@dataclass
class UserSummary:
    """Data class for user summary statistics"""
    total_files: int
    total_duration: float
    storage_used: int
    completed_jobs: int
    failed_jobs: int
    processing_jobs: int


@dataclass
class JobSummary:
    """Data class for job summary information"""
    job_id: str
    status: str
    progress: int
    file_name: str
    file_size: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class DatabaseService:
    """
    High-level database service that orchestrates operations across multiple repositories.
    Provides business logic and transaction management for complex operations.
    """
    
    def __init__(self):
        self.error_handler = PostgresErrorHandler()
    
    async def get_user_summary(self, user_id: str) -> UserSummary:
        """
        Get comprehensive user statistics including files, jobs, and storage usage.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            UserSummary object with user statistics
        """
        try:
            # Get file statistics
            async with MediaRepository() as media_repo:
                total_files = await media_repo.count_by_user(user_id)
                storage_stats = await media_repo.get_storage_stats(user_id)
            
            # Get job statistics  
            async with ProcessingJobRepository() as job_repo:
                job_stats = await job_repo.get_user_job_statistics(user_id)
            
            return UserSummary(
                total_files=total_files,
                total_duration=storage_stats.get('total_duration', 0),
                storage_used=storage_stats.get('total_size', 0),
                completed_jobs=job_stats.get('completed_jobs', 0),
                failed_jobs=job_stats.get('failed_jobs', 0),
                processing_jobs=job_stats.get('processing_jobs', 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting user summary for {user_id}: {e}")
            raise self.error_handler.handle_error(e, "get_user_summary")
    
    async def get_user_jobs_with_details(
        self, 
        user_id: str, 
        status: Optional[str] = None,
        limit: int = 20, 
        offset: int = 0
    ) -> Tuple[List[JobSummary], int]:
        """
        Get user's jobs with detailed information including media file details.
        
        Args:
            user_id: UUID of the user
            status: Optional filter by job status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            
        Returns:
            Tuple of (JobSummary list, total count)
        """
        try:
            # Get jobs using job repository
            async with ProcessingJobRepository() as job_repo:
                if status:
                    jobs = await job_repo.get_by_user_and_status(user_id, status, limit, offset)
                    total = await job_repo.count_by_user_and_status(user_id, status)
                else:
                    jobs = await job_repo.get_by_user(user_id, limit, offset)
                    total = await job_repo.count_by_user(user_id)
            
            # Enrich jobs with media file information
            job_summaries = []
            async with MediaRepository() as media_repo:
                for job in jobs:
                    # Get media file details
                    media_file = await media_repo.get_by_id(job['media_file_id'])
                    
                    job_summary = JobSummary(
                        job_id=job['job_id'],
                        status=job.get('processing', {}).get('status', 'uploaded'),
                        progress=job.get('processing', {}).get('progress', 0),
                        file_name=media_file.get('original_name', 'Unknown') if media_file else 'Unknown',
                        file_size=media_file.get('file_size', 0) if media_file else 0,
                        created_at=job.get('created_at', datetime.utcnow()),
                        started_at=job.get('processing', {}).get('startedAt'),
                        completed_at=job.get('processing', {}).get('completedAt'),
                        error=job.get('processing', {}).get('error')
                    )
                    job_summaries.append(job_summary)
            
            return job_summaries, total
            
        except Exception as e:
            logger.error(f"Error getting user jobs for {user_id}: {e}")
            raise self.error_handler.handle_error(e, "get_user_jobs_with_details")
    
    async def create_upload_and_job(
        self,
        user_id: str,
        media_data: Dict[str, Any],
        job_data: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Create both a media file record and a processing job record in a transaction-like operation.
        
        Args:
            user_id: UUID of the user
            media_data: Media file data for creation
            job_data: Job data for creation
            
        Returns:
            Tuple of (media_id, job_id)
        """
        try:
            # Create media file first
            async with MediaRepository() as media_repo:
                media_id = await media_repo.create(media_data)
            
            # Link job to media file and create job
            job_data['mediaFileId'] = media_id
            async with ProcessingJobRepository() as job_repo:
                job_id_db = await job_repo.create(job_data)
            
            logger.info(f"Created media {media_id} and job {job_id_db} for user {user_id}")
            return media_id, job_id_db
            
        except Exception as e:
            logger.error(f"Error creating upload and job for user {user_id}: {e}")
            # In a real implementation, you might want to rollback the media creation
            # if job creation fails, but for now we'll log the error
            raise self.error_handler.handle_error(e, "create_upload_and_job")
    
    async def delete_user_job_and_media(self, user_id: str, job_id: str) -> bool:
        """
        Delete a job and its associated media file, with proper authorization checks.
        
        Args:
            user_id: UUID of the user making the request
            job_id: Job ID to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            # Get job and verify ownership
            async with ProcessingJobRepository() as job_repo:
                jobs = await job_repo.get_by_job_id_and_user(job_id, user_id)
                if not jobs:
                    logger.warning(f"Job {job_id} not found or not owned by user {user_id}")
                    return False
                
                job = jobs[0]
                media_file_id = job.get('media_file_id')
                
                # Delete the job
                await job_repo.delete(job['id'])
            
            # Delete associated media file if it exists
            if media_file_id:
                async with MediaRepository() as media_repo:
                    await media_repo.delete(media_file_id)
            
            logger.info(f"Deleted job {job_id} and media {media_file_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting job {job_id} for user {user_id}: {e}")
            raise self.error_handler.handle_error(e, "delete_user_job_and_media")
    
    async def update_user_usage_stats(
        self, 
        user_id: str, 
        file_size_increment: int = 0,
        duration_increment: float = 0.0,
        files_processed_increment: int = 0
    ) -> bool:
        """
        Update user usage statistics incrementally.
        
        Args:
            user_id: UUID of the user
            file_size_increment: Bytes to add to storage usage
            duration_increment: Seconds to add to audio duration
            files_processed_increment: Number of files to add to processed count
            
        Returns:
            True if update was successful
        """
        try:
            async with UserRepository() as user_repo:
                await user_repo.increment_usage_stats(
                    user_id,
                    storage_bytes=file_size_increment,
                    audio_duration=duration_increment,
                    files_processed=files_processed_increment
                )
            
            logger.debug(f"Updated usage stats for user {user_id}: "
                        f"+{file_size_increment} bytes, +{duration_increment}s, +{files_processed_increment} files")
            return True
            
        except Exception as e:
            logger.error(f"Error updating usage stats for user {user_id}: {e}")
            raise self.error_handler.handle_error(e, "update_user_usage_stats")
    
    async def get_job_with_full_details(self, job_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive job details including media file and user information.
        
        Args:
            job_id: Job ID to fetch
            user_id: UUID of the user requesting the job
            
        Returns:
            Job details dictionary or None if not found
        """
        try:
            # Get job with ownership verification
            async with ProcessingJobRepository() as job_repo:
                jobs = await job_repo.get_by_job_id_and_user(job_id, user_id)
                if not jobs:
                    return None
                job = jobs[0]
            
            # Get media file details
            async with MediaRepository() as media_repo:
                media_file = await media_repo.get_by_id(job['media_file_id'])
            
            # Get user details
            async with UserRepository() as user_repo:
                user = await user_repo.get_by_id(user_id)
            
            # Combine all information
            job_details = {
                **job,
                'media_file': media_file,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'subscription_level': user['subscription_level']
                } if user else None
            }
            
            return job_details
            
        except Exception as e:
            logger.error(f"Error getting job details for {job_id}: {e}")
            raise self.error_handler.handle_error(e, "get_job_with_full_details")
    
    async def cleanup_expired_files(self, days_old: int = 30) -> int:
        """
        Clean up expired media files and their associated jobs.
        This is typically run as a scheduled maintenance task.
        
        Args:
            days_old: Age in days after which files should be cleaned up
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            cleanup_count = 0
            
            # Get expired media files
            async with MediaRepository() as media_repo:
                expired_files = await media_repo.get_expired_files(cutoff_date)
                
                for media_file in expired_files:
                    try:
                        # Delete associated jobs first
                        async with ProcessingJobRepository() as job_repo:
                            jobs_by_media = await job_repo.get_by_media_file(media_file['id'])
                            for job in jobs_by_media:
                                await job_repo.delete(job['id'])
                        
                        # Delete the media file
                        await media_repo.delete(media_file['id'])
                        cleanup_count += 1
                        
                        logger.info(f"Cleaned up expired media file: {media_file['id']}")
                        
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up media file {media_file['id']}: {cleanup_error}")
                        continue
            
            logger.info(f"Cleanup completed: {cleanup_count} files removed")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup of expired files: {e}")
            raise self.error_handler.handle_error(e, "cleanup_expired_files")
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide statistics for administrative purposes.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            stats = {}
            
            # User statistics
            async with UserRepository() as user_repo:
                stats['total_users'] = await user_repo.count_total()
                stats['active_users'] = await user_repo.count_active_users()
                stats['users_by_subscription'] = await user_repo.get_subscription_stats()
            
            # Media statistics
            async with MediaRepository() as media_repo:
                stats['total_files'] = await media_repo.count_total()
                stats['total_storage_used'] = await media_repo.get_total_storage()
                stats['files_by_type'] = await media_repo.get_file_type_stats()
            
            # Job statistics
            async with ProcessingJobRepository() as job_repo:
                stats['total_jobs'] = await job_repo.count_total()
                stats['jobs_by_status'] = await job_repo.get_status_stats()
                stats['avg_processing_time'] = await job_repo.get_average_processing_time()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            raise self.error_handler.handle_error(e, "get_system_statistics")


# Singleton instance for application-wide use
database_service = DatabaseService()