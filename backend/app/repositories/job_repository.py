"""
Processing Job Repository for PostgreSQL

This module provides processing job-specific database operations using the repository pattern.
It extends BaseRepository with job-specific functionality.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import uuid

from .base import BaseRepository
from ..core.postgres_db import Database, QueryError
from ..utils.postgres_errors import PostgresErrorHandler, PostgresError

logger = logging.getLogger(__name__)


class ProcessingJobRepository(BaseRepository):
    """Repository for processing job database operations"""
    
    def __init__(self):
        super().__init__("processing_jobs")
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new processing job"""
        try:
            # Set default values if not provided
            if "status" not in data:
                data["status"] = "pending"
            
            if "priority" not in data:
                data["priority"] = "normal"
            
            if "progress" not in data:
                data["progress"] = {
                    "percentage": 0,
                    "current_stage": "queued",
                    "estimated_time_remaining": None
                }
            
            if "config" not in data:
                data["config"] = {}
            
            # Set timestamps
            now = datetime.utcnow()
            data["created_at"] = now
            data["updated_at"] = now
            
            # Build the query
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = list(data.values())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """
            
            result = await self.connection.fetchval(query, *values)
            logger.debug(f"Created processing job with ID: {result}")
            return result
            
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to create processing job: {e}")
            raise PostgresErrorHandler.handle_error(e, {"operation": "create_job", "data": data})
        except Exception as e:
            logger.error(f"Unexpected error creating processing job: {e}")
            raise QueryError(f"Create processing job failed: {e}")
    
    async def get_by_user_id(self, user_id: Union[str, uuid.UUID], limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get processing jobs by user ID with pagination"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE user_id = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            elif offset > 0:
                query += f" OFFSET {offset}"
            
            rows = await self.connection.fetch(query, str(user_id))
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by user ID {user_id}: {e}")
            raise QueryError(f"Get processing jobs by user ID failed: {e}")
    
    async def get_by_media_file_id(self, media_file_id: Union[str, uuid.UUID]) -> List[Dict[str, Any]]:
        """Get processing jobs by media file ID"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE media_file_id = $1 ORDER BY created_at DESC"
            rows = await self.connection.fetch(query, str(media_file_id))
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by media file ID {media_file_id}: {e}")
            raise QueryError(f"Get processing jobs by media file ID failed: {e}")
    
    async def get_by_job_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a processing job by job_id (external identifier)"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE job_id = $1"
            row = await self.connection.fetchrow(query, job_id)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved processing job by job_id: {job_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get processing job by job_id {job_id}: {e}")
            raise QueryError(f"Get processing job by job_id failed: {e}")
    
    async def get_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get processing jobs by status"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE status = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, status)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by status {status}: {e}")
            raise QueryError(f"Get processing jobs by status failed: {e}")
    
    async def get_by_type(self, job_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get processing jobs by type"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE job_type = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, job_type)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by type {job_type}: {e}")
            raise QueryError(f"Get processing jobs by type failed: {e}")
    
    async def get_by_priority(self, priority: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get processing jobs by priority"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE priority = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, priority)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by priority {priority}: {e}")
            raise QueryError(f"Get processing jobs by priority failed: {e}")
    
    async def update_status(self, job_id: Union[str, uuid.UUID], status: str, progress_update: Optional[Dict[str, Any]] = None) -> bool:
        """Update job status and optionally progress"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            # Set timestamps based on status
            if status == "processing" and not await self._has_field(job_id, "started_at"):
                update_data["started_at"] = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                update_data["completed_at"] = datetime.utcnow()
            
            # Update progress if provided
            if progress_update:
                current_job = await self.get_by_id(job_id)
                if current_job:
                    current_progress = current_job.get("progress", {})
                    updated_progress = {**current_progress, **progress_update}
                    update_data["progress"] = updated_progress
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job status {job_id}: {e}")
            raise QueryError(f"Update job status failed: {e}")
    
    async def update_progress(self, job_id: Union[str, uuid.UUID], progress_data: Dict[str, Any]) -> bool:
        """Update job progress information"""
        try:
            # Get current job data
            current_job = await self.get_by_id(job_id)
            if not current_job:
                return False
            
            # Merge with existing progress data
            current_progress = current_job.get("progress", {})
            updated_progress = {**current_progress, **progress_data}
            
            # Update the job
            update_data = {
                "progress": updated_progress,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job progress {job_id}: {e}")
            raise QueryError(f"Update job progress failed: {e}")
    
    async def update_result(self, job_id: Union[str, uuid.UUID], result_data: Dict[str, Any]) -> bool:
        """Update job result data"""
        try:
            update_data = {
                "result": result_data,
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job result {job_id}: {e}")
            raise QueryError(f"Update job result failed: {e}")
    
    async def update_error(self, job_id: Union[str, uuid.UUID], error_data: Dict[str, Any]) -> bool:
        """Update job error information"""
        try:
            update_data = {
                "error": error_data,
                "status": "failed",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job error {job_id}: {e}")
            raise QueryError(f"Update job error failed: {e}")
    
    async def count_by_user(self, user_id: Union[str, uuid.UUID]) -> int:
        """Count processing jobs by user"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id = $1"
            result = await self.connection.fetchval(query, str(user_id))
            return result
        except Exception as e:
            logger.error(f"Failed to count processing jobs by user: {e}")
            raise QueryError(f"Count processing jobs by user failed: {e}")
    
    async def count_by_status(self, status: str) -> int:
        """Count processing jobs by status"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE status = $1"
            result = await self.connection.fetchval(query, status)
            return result
        except Exception as e:
            logger.error(f"Failed to count processing jobs by status: {e}")
            raise QueryError(f"Count processing jobs by status failed: {e}")
    
    async def count_by_type(self, job_type: str) -> int:
        """Count processing jobs by type"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE job_type = $1"
            result = await self.connection.fetchval(query, job_type)
            return result
        except Exception as e:
            logger.error(f"Failed to count processing jobs by type: {e}")
            raise QueryError(f"Count processing jobs by type failed: {e}")
    
    async def get_pending_jobs(self, job_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending jobs, optionally filtered by type"""
        try:
            if job_type:
                query = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE status = 'pending' AND job_type = $1 
                    ORDER BY priority DESC, created_at ASC
                    LIMIT $2
                """
                rows = await self.connection.fetch(query, job_type, limit)
            else:
                query = f"""
                    SELECT * FROM {self.table_name} 
                    WHERE status = 'pending' 
                    ORDER BY priority DESC, created_at ASC
                    LIMIT $1
                """
                rows = await self.connection.fetch(query, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            raise QueryError(f"Get pending jobs failed: {e}")
    
    async def get_processing_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get currently processing jobs"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE status = 'processing' 
                ORDER BY started_at ASC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs: {e}")
            raise QueryError(f"Get processing jobs failed: {e}")
    
    async def get_stalled_jobs(self, hours: int = 2, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs that have been processing too long (stalled)"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE status = 'processing' 
                AND started_at < NOW() - INTERVAL '{hours} hours'
                ORDER BY started_at ASC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get stalled jobs: {e}")
            raise QueryError(f"Get stalled jobs failed: {e}")
    
    async def get_job_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get job statistics for the last N days"""
        try:
            # Overall stats
            overall_query = f"""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
                    AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                        ELSE NULL END) as avg_processing_time_seconds
                FROM {self.table_name} 
                WHERE created_at >= NOW() - INTERVAL '{days} days'
            """
            
            overall_stats = await self.connection.fetchrow(overall_query)
            
            # Stats by job type
            type_query = f"""
                SELECT 
                    job_type,
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                    AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                        ELSE NULL END) as avg_processing_time
                FROM {self.table_name} 
                WHERE created_at >= NOW() - INTERVAL '{days} days'
                GROUP BY job_type
                ORDER BY total_count DESC
            """
            
            type_stats = await self.connection.fetch(type_query)
            
            return {
                "period_days": days,
                "overall": dict(overall_stats) if overall_stats else {},
                "by_type": [dict(row) for row in type_stats]
            }
            
        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            raise QueryError(f"Get job statistics failed: {e}")
    
    async def get_user_job_statistics(self, user_id: Union[str, uuid.UUID], days: int = 30) -> Dict[str, Any]:
        """Get job statistics for a specific user"""
        try:
            query = f"""
                SELECT 
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_jobs,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_jobs,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_jobs,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_jobs,
                    AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM (completed_at - started_at)) 
                        ELSE NULL END) as avg_processing_time_seconds
                FROM {self.table_name} 
                WHERE user_id = $1 AND created_at >= NOW() - INTERVAL '{days} days'
            """
            
            row = await self.connection.fetchrow(query, str(user_id))
            return dict(row) if row else {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "processing_jobs": 0,
                "pending_jobs": 0,
                "avg_processing_time_seconds": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get user job statistics {user_id}: {e}")
            raise QueryError(f"Get user job statistics failed: {e}")
    
    async def search_jobs(self, search_term: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search processing jobs in multiple fields"""
        if search_fields is None:
            search_fields = ["job_id", "config", "result"]
        
        return await self.search(search_term, search_fields)
    
    async def get_recent_jobs(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently created jobs"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE created_at >= NOW() - INTERVAL '{hours} hours'
                ORDER BY created_at DESC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get recent jobs: {e}")
            raise QueryError(f"Get recent jobs failed: {e}")
    
    async def get_long_running_jobs(self, hours: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs that have been running longer than specified hours"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE status = 'processing' 
                AND started_at <= NOW() - INTERVAL '{hours} hours'
                ORDER BY started_at ASC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get long running jobs: {e}")
            raise QueryError(f"Get long running jobs failed: {e}")
    
    async def cancel_job(self, job_id: Union[str, uuid.UUID], reason: Optional[str] = None) -> bool:
        """Cancel a job"""
        try:
            update_data = {
                "status": "cancelled",
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if reason:
                update_data["error"] = {
                    "type": "cancelled",
                    "message": reason,
                    "cancelled_at": datetime.utcnow().isoformat()
                }
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            raise QueryError(f"Cancel job failed: {e}")
    
    async def retry_job(self, job_id: Union[str, uuid.UUID]) -> bool:
        """Retry a failed job"""
        try:
            update_data = {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "error": None,
                "progress": {
                    "percentage": 0,
                    "current_stage": "queued",
                    "estimated_time_remaining": None
                },
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to retry job {job_id}: {e}")
            raise QueryError(f"Retry job failed: {e}")
    
    async def delete_user_jobs(self, user_id: Union[str, uuid.UUID]) -> int:
        """Delete all jobs for a user and return count"""
        try:
            result = await self.connection.execute(
                f"DELETE FROM {self.table_name} WHERE user_id = $1",
                str(user_id)
            )
            
            # Parse result like "DELETE 5" to get count
            if result.startswith("DELETE "):
                return int(result.split()[1])
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete user jobs {user_id}: {e}")
            raise QueryError(f"Delete user jobs failed: {e}")
    
    async def delete_completed_jobs(self, days: int = 30) -> int:
        """Delete completed jobs older than specified days"""
        try:
            result = await self.connection.execute(
                f"""
                DELETE FROM {self.table_name} 
                WHERE status = 'completed' 
                AND completed_at < NOW() - INTERVAL '{days} days'
                """
            )
            
            # Parse result like "DELETE 15" to get count
            if result.startswith("DELETE "):
                return int(result.split()[1])
            return 0
            
        except Exception as e:
            logger.error(f"Failed to delete completed jobs: {e}")
            raise QueryError(f"Delete completed jobs failed: {e}")
    
    async def _has_field(self, job_id: Union[str, uuid.UUID], field: str) -> bool:
        """Check if a job has a specific field set (helper method)"""
        try:
            query = f"SELECT {field} FROM {self.table_name} WHERE id = $1"
            result = await self.connection.fetchval(query, str(job_id))
            return result is not None
        except Exception:
            return False
    
    async def get_jobs_with_progress_filter(self, min_percentage: int = 0, max_percentage: int = 100) -> List[Dict[str, Any]]:
        """Get jobs within a progress percentage range"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE (progress->>'percentage')::numeric >= $1 
                AND (progress->>'percentage')::numeric <= $2
                ORDER BY created_at DESC
            """
            
            rows = await self.connection.fetch(query, min_percentage, max_percentage)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get jobs by progress range: {e}")
            raise QueryError(f"Get jobs by progress range failed: {e}")
    
    async def get_by_user_and_status(self, user_id: Union[str, uuid.UUID], status: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get processing jobs by user ID and status with pagination"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE user_id = $1 AND processing->>'status' = $2 
                ORDER BY created_at DESC 
                LIMIT $3 OFFSET $4
            """
            rows = await self.connection.fetch(query, str(user_id), status, limit, offset)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get processing jobs by user ID {user_id} and status {status}: {e}")
            raise QueryError(f"Get processing jobs by user ID and status failed: {e}")
    
    async def count_by_user_and_status(self, user_id: Union[str, uuid.UUID], status: str) -> int:
        """Count processing jobs by user and status"""
        try:
            query = f"""
                SELECT COUNT(*) FROM {self.table_name} 
                WHERE user_id = $1 AND processing->>'status' = $2
            """
            result = await self.connection.fetchval(query, str(user_id), status)
            return result
        except Exception as e:
            logger.error(f"Failed to count processing jobs by user and status: {e}")
            raise QueryError(f"Count processing jobs by user and status failed: {e}")
    
    async def get_by_job_id_and_user(self, job_id: str, user_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get a processing job by job_id and user_id"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE job_id = $1 AND user_id = $2"
            row = await self.connection.fetchrow(query, job_id, str(user_id))
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved processing job by job_id: {job_id}, user_id: {user_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get processing job by job_id {job_id} and user_id {user_id}: {e}")
            raise QueryError(f"Get processing job by job_id and user_id failed: {e}")
    
    async def get_by_job_id_field(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a processing job by the job_id field (external identifier)"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE job_id = $1"
            row = await self.connection.fetchrow(query, job_id)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved processing job by job_id field: {job_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get processing job by job_id field {job_id}: {e}")
            raise QueryError(f"Get processing job by job_id field failed: {e}")