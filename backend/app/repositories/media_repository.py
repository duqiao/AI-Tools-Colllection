"""
Media File Repository for PostgreSQL

This module provides media file-specific database operations using the repository pattern.
It extends BaseRepository with media file-specific functionality.
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


class MediaRepository(BaseRepository):
    """Repository for media file database operations"""
    
    def __init__(self):
        super().__init__("media_files")
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new media file record"""
        try:
            # Set default values if not provided
            if "processing_info" not in data:
                data["processing_info"] = {
                    "status": "uploaded",
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "virus_scan_status": "pending",
                    "backup_status": "pending"
                }
            
            if "metadata" not in data:
                data["metadata"] = {}
            
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
            logger.debug(f"Created media file with ID: {result}")
            return result
            
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to create media file: {e}")
            raise PostgresErrorHandler.handle_error(e, {"operation": "create_media_file", "data": data})
        except Exception as e:
            logger.error(f"Unexpected error creating media file: {e}")
            raise QueryError(f"Create media file failed: {e}")
    
    async def get_by_user_id(self, user_id: Union[str, uuid.UUID], limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get media files by user ID with pagination"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE user_id = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            elif offset > 0:
                query += f" OFFSET {offset}"
            
            rows = await self.connection.fetch(query, str(user_id))
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get media files by user ID {user_id}: {e}")
            raise QueryError(f"Get media files by user ID failed: {e}")
    
    async def get_by_file_name(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get a media file by filename"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE file_name = $1"
            row = await self.connection.fetchrow(query, file_name)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved media file by filename: {file_name}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get media file by filename {file_name}: {e}")
            raise QueryError(f"Get media file by filename failed: {e}")
    
    async def get_by_original_file_name(self, original_file_name: str) -> Optional[Dict[str, Any]]:
        """Get a media file by original filename"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE original_file_name = $1"
            row = await self.connection.fetchrow(query, original_file_name)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved media file by original filename: {original_file_name}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get media file by original filename {original_file_name}: {e}")
            raise QueryError(f"Get media file by original filename failed: {e}")
    
    async def get_by_file_type(self, file_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get media files by file type"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE file_type = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, file_type)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get media files by type {file_type}: {e}")
            raise QueryError(f"Get media files by type failed: {e}")
    
    async def get_by_mime_type(self, mime_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get media files by MIME type"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE mime_type = $1 ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, mime_type)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get media files by MIME type {mime_type}: {e}")
            raise QueryError(f"Get media files by MIME type failed: {e}")
    
    async def update_processing_info(self, media_id: Union[str, uuid.UUID], processing_info: Dict[str, Any]) -> bool:
        """Update processing information for a media file"""
        try:
            # Get current media file data
            current_media = await self.get_by_id(media_id)
            if not current_media:
                return False
            
            # Merge with existing processing info
            current_processing = current_media.get("processing_info", {})
            updated_processing = {**current_processing, **processing_info}
            
            # Update the media file
            update_data = {
                "processing_info": updated_processing,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(media_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update processing info {media_id}: {e}")
            raise QueryError(f"Update processing info failed: {e}")
    
    async def update_metadata(self, media_id: Union[str, uuid.UUID], metadata: Dict[str, Any]) -> bool:
        """Update metadata for a media file"""
        try:
            # Get current media file data
            current_media = await self.get_by_id(media_id)
            if not current_media:
                return False
            
            # Merge with existing metadata
            current_metadata = current_media.get("metadata", {})
            updated_metadata = {**current_metadata, **metadata}
            
            # Update the media file
            update_data = {
                "metadata": updated_metadata,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(media_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update metadata {media_id}: {e}")
            raise QueryError(f"Update metadata failed: {e}")
    
    async def update_file_path(self, media_id: Union[str, uuid.UUID], new_file_path: str) -> bool:
        """Update the file path for a media file"""
        try:
            update_data = {
                "file_path": new_file_path,
                "updated_at": datetime.utcnow()
            }
            return await self.update(media_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update file path {media_id}: {e}")
            raise QueryError(f"Update file path failed: {e}")
    
    async def get_files_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get media files by processing status"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE processing_info->>'status' = $1 
                ORDER BY created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query, status)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get files by status {status}: {e}")
            raise QueryError(f"Get files by status failed: {e}")
    
    async def get_files_by_user_and_status(self, user_id: Union[str, uuid.UUID], status: str) -> List[Dict[str, Any]]:
        """Get media files by user and processing status"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE user_id = $1 AND processing_info->>'status' = $2 
                ORDER BY created_at DESC
            """
            
            rows = await self.connection.fetch(query, str(user_id), status)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get files by user and status {user_id}, {status}: {e}")
            raise QueryError(f"Get files by user and status failed: {e}")
    
    async def count_by_user(self, user_id: Union[str, uuid.UUID]) -> int:
        """Count media files by user"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id = $1"
            result = await self.connection.fetchval(query, str(user_id))
            return result
        except Exception as e:
            logger.error(f"Failed to count media files by user: {e}")
            raise QueryError(f"Count media files by user failed: {e}")
    
    async def count_by_type(self, file_type: str) -> int:
        """Count media files by type"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE file_type = $1"
            result = await self.connection.fetchval(query, file_type)
            return result
        except Exception as e:
            logger.error(f"Failed to count media files by type: {e}")
            raise QueryError(f"Count media files by type failed: {e}")
    
    async def count_by_status(self, status: str) -> int:
        """Count media files by processing status"""
        try:
            query = f"""
                SELECT COUNT(*) FROM {self.table_name} 
                WHERE processing_info->>'status' = $1
            """
            result = await self.connection.fetchval(query, status)
            return result
        except Exception as e:
            logger.error(f"Failed to count media files by status: {e}")
            raise QueryError(f"Count media files by status failed: {e}")
    
    async def get_storage_stats(self, user_id: Optional[Union[str, uuid.UUID]] = None) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            if user_id:
                query = f"""
                    SELECT 
                        COUNT(*) as file_count,
                        SUM(file_size) as total_size,
                        AVG(file_size) as avg_size,
                        MIN(file_size) as min_size,
                        MAX(file_size) as max_size
                    FROM {self.table_name} 
                    WHERE user_id = $1
                """
                row = await self.connection.fetchrow(query, str(user_id))
            else:
                query = f"""
                    SELECT 
                        COUNT(*) as file_count,
                        SUM(file_size) as total_size,
                        AVG(file_size) as avg_size,
                        MIN(file_size) as min_size,
                        MAX(file_size) as max_size
                    FROM {self.table_name}
                """
                row = await self.connection.fetchrow(query)
            
            return dict(row) if row else {
                "file_count": 0,
                "total_size": 0,
                "avg_size": 0,
                "min_size": 0,
                "max_size": 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise QueryError(f"Get storage stats failed: {e}")
    
    async def search_media_files(self, search_term: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search media files in multiple fields"""
        if search_fields is None:
            search_fields = ["file_name", "original_file_name", "metadata"]
        
        return await self.search(search_term, search_fields)
    
    async def get_recent_files(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently uploaded files"""
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
            logger.error(f"Failed to get recent files: {e}")
            raise QueryError(f"Get recent files failed: {e}")
    
    async def get_large_files(self, size_mb: int = 100, limit: int = 50) -> List[Dict[str, Any]]:
        """Get large files above specified size in MB"""
        try:
            size_bytes = size_mb * 1024 * 1024
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE file_size >= $1
                ORDER BY file_size DESC
                LIMIT $2
            """
            
            rows = await self.connection.fetch(query, size_bytes, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get large files: {e}")
            raise QueryError(f"Get large files failed: {e}")
    
    async def get_files_by_duration_range(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get files within a duration range"""
        try:
            conditions = []
            params = []
            param_count = 0
            
            if min_seconds is not None:
                param_count += 1
                conditions.append(f"duration_seconds >= ${param_count}")
                params.append(min_seconds)
            
            if max_seconds is not None:
                param_count += 1
                conditions.append(f"duration_seconds <= ${param_count}")
                params.append(max_seconds)
            
            if not conditions:
                return []
            
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE {' AND '.join(conditions)}
                ORDER BY duration_seconds DESC
            """
            
            rows = await self.connection.fetch(query, *params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get files by duration range: {e}")
            raise QueryError(f"Get files by duration range failed: {e}")
    
    async def update_virus_scan_status(self, media_id: Union[str, uuid.UUID], status: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """Update virus scan status"""
        try:
            processing_update = {
                "virus_scan_status": status,
                "virus_scanned_at": datetime.utcnow().isoformat()
            }
            
            if details:
                processing_update["virus_scan_details"] = details
            
            return await self.update_processing_info(media_id, processing_update)
            
        except Exception as e:
            logger.error(f"Failed to update virus scan status {media_id}: {e}")
            raise QueryError(f"Update virus scan status failed: {e}")
    
    async def get_user_storage_usage(self, user_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Get detailed storage usage for a user"""
        try:
            query = f"""
                SELECT 
                    file_type,
                    COUNT(*) as file_count,
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size
                FROM {self.table_name} 
                WHERE user_id = $1
                GROUP BY file_type
                ORDER BY total_size DESC
            """
            
            rows = await self.connection.fetch(query, str(user_id))
            usage_by_type = [dict(row) for row in rows]
            
            # Get total usage
            total_query = f"""
                SELECT 
                    COUNT(*) as total_files,
                    SUM(file_size) as total_size
                FROM {self.table_name} 
                WHERE user_id = $1
            """
            
            total_row = await self.connection.fetchrow(total_query, str(user_id))
            total_info = dict(total_row) if total_row else {"total_files": 0, "total_size": 0}
            
            return {
                "user_id": str(user_id),
                "usage_by_type": usage_by_type,
                "total_files": total_info["total_files"],
                "total_size": total_info["total_size"] or 0,
                "total_size_mb": (total_info["total_size"] or 0) / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user storage usage {user_id}: {e}")
            raise QueryError(f"Get user storage usage failed: {e}")
    
    async def delete_user_media_files(self, user_id: Union[str, uuid.UUID]) -> int:
        """Delete all media files for a user and return count"""
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
            logger.error(f"Failed to delete user media files {user_id}: {e}")
            raise QueryError(f"Delete user media files failed: {e}")
    
    async def get_files_needing_virus_scan(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get files that need virus scanning"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE processing_info->>'virus_scan_status' = 'pending'
                OR processing_info->>'virus_scan_status' IS NULL
                ORDER BY created_at ASC
                LIMIT $1
            """
            
            rows = await self.connection.fetch(query, limit)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get files needing virus scan: {e}")
            raise QueryError(f"Get files needing virus scan failed: {e}")