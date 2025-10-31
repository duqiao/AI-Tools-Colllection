"""
User Repository for PostgreSQL

This module provides user-specific database operations using the repository pattern.
It extends BaseRepository with user-specific functionality.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import uuid

from .base import BaseRepository
from ..core.postgres_db import Database, QueryError
from ..utils.postgres_errors import PostgresError, safe_execute, PostgresErrorType

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user database operations"""
    
    def __init__(self):
        super().__init__("users")
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new user"""
        try:
            # Set default values if not provided
            if "subscription_level" not in data:
                data["subscription_level"] = "free"
            
            if "profile" not in data:
                data["profile"] = {}
            
            if "usage_stats" not in data:
                data["usage_stats"] = {
                    "total_files_processed": 0,
                    "total_audio_duration": 0,
                    "api_calls_count": 0,
                    "storage_used_bytes": 0
                }
            
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
            logger.debug(f"Created user with ID: {result}")
            return result
            
        except asyncpg.PostgresError as e:
            logger.error(f"Failed to create user: {e}")
            raise PostgresErrorHandler.handle_error(e, {"operation": "create_user", "data": data})
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            raise QueryError(f"Create user failed: {e}")
    
    async def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE username = $1"
            row = await self.connection.fetchrow(query, username)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved user by username: {username}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            raise QueryError(f"Get user by username failed: {e}")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by email"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE email = $1"
            row = await self.connection.fetchrow(query, email)
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved user by email: {email}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise QueryError(f"Get user by email failed: {e}")
    
    async def update_profile(self, user_id: Union[str, uuid.UUID], profile_data: Dict[str, Any]) -> bool:
        """Update user profile data"""
        try:
            # Get current user data
            current_user = await self.get_by_id(user_id)
            if not current_user:
                return False
            
            # Merge with existing profile data
            current_profile = current_user.get("profile", {})
            updated_profile = {**current_profile, **profile_data}
            
            # Update the user
            update_data = {
                "profile": updated_profile,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {e}")
            raise QueryError(f"Update user profile failed: {e}")
    
    async def update_usage_stats(self, user_id: Union[str, uuid.UUID], stats_update: Dict[str, Any]) -> bool:
        """Update user usage statistics"""
        try:
            # Get current user data
            current_user = await self.get_by_id(user_id)
            if not current_user:
                return False
            
            # Merge with existing usage stats
            current_stats = current_user.get("usage_stats", {})
            
            # For numeric fields, add to existing values
            updated_stats = current_stats.copy()
            for key, value in stats_update.items():
                if key in current_stats and isinstance(current_stats[key], (int, float)) and isinstance(value, (int, float)):
                    updated_stats[key] = current_stats[key] + value
                else:
                    updated_stats[key] = value
            
            # Update the user
            update_data = {
                "usage_stats": updated_stats,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update usage stats {user_id}: {e}")
            raise QueryError(f"Update usage stats failed: {e}")
    
    async def update_subscription_level(self, user_id: Union[str, uuid.UUID], subscription_level: str) -> bool:
        """Update user subscription level"""
        try:
            update_data = {
                "subscription_level": subscription_level,
                "updated_at": datetime.utcnow()
            }
            return await self.update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update subscription level {user_id}: {e}")
            raise QueryError(f"Update subscription level failed: {e}")
    
    async def increment_usage_stats(self, user_id: Union[str, uuid.UUID], increments: Dict[str, Union[int, float]]) -> bool:
        """Increment usage statistics by specified amounts"""
        try:
            # Get current user data
            current_user = await self.get_by_id(user_id)
            if not current_user:
                return False
            
            # Increment existing stats
            current_stats = current_user.get("usage_stats", {})
            updated_stats = current_stats.copy()
            
            for key, increment in increments.items():
                if key in updated_stats:
                    updated_stats[key] += increment
                else:
                    updated_stats[key] = increment
            
            # Update the user
            update_data = {
                "usage_stats": updated_stats,
                "updated_at": datetime.utcnow()
            }
            
            return await self.update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to increment usage stats {user_id}: {e}")
            raise QueryError(f"Increment usage stats failed: {e}")
    
    async def get_users_by_subscription_level(self, subscription_level: str) -> List[Dict[str, Any]]:
        """Get users by subscription level"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE subscription_level = $1 ORDER BY created_at DESC"
            rows = await self.connection.fetch(query, subscription_level)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get users by subscription level {subscription_level}: {e}")
            raise QueryError(f"Get users by subscription level failed: {e}")
    
    async def search_users(self, search_term: str, search_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search users in multiple fields"""
        if search_fields is None:
            search_fields = ["username", "email", "profile"]
        
        return await self.search(search_term, search_fields)
    
    async def get_active_users(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get users who have been active within the specified number of days"""
        try:
            query = f"""
                SELECT * FROM {self.table_name} 
                WHERE updated_at >= NOW() - INTERVAL '{days} days'
                ORDER BY updated_at DESC
            """
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            raise QueryError(f"Get active users failed: {e}")
    
    async def get_user_stats(self, user_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get user statistics including media counts and job counts"""
        try:
            # Get basic user info
            user = await self.get_by_id(user_id)
            if not user:
                return None
            
            # Get counts from related tables
            media_count_query = """
                SELECT COUNT(*) as count 
                FROM media_files 
                WHERE user_id = $1
            """
            jobs_count_query = """
                SELECT COUNT(*) as count 
                FROM processing_jobs 
                WHERE user_id = $1
            """
            
            media_count = await self.connection.fetchval(media_count_query, str(user_id))
            jobs_count = await self.connection.fetchval(jobs_count_query, str(user_id))
            
            return {
                "user": user,
                "stats": {
                    "media_files_count": media_count,
                    "processing_jobs_count": jobs_count,
                    "usage_stats": user.get("usage_stats", {}),
                    "subscription_level": user.get("subscription_level", "free")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats {user_id}: {e}")
            raise QueryError(f"Get user stats failed: {e}")
    
    async def update_last_login(self, user_id: Union[str, uuid.UUID]) -> bool:
        """Update the last login timestamp for a user"""
        try:
            update_data = {
                "last_login": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            return await self.update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update last login {user_id}: {e}")
            raise QueryError(f"Update last login failed: {e}")
    
    async def count_by_subscription_level(self, subscription_level: str) -> int:
        """Count users by subscription level"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE subscription_level = $1"
            result = await self.connection.fetchval(query, subscription_level)
            return result
        except Exception as e:
            logger.error(f"Failed to count users by subscription level: {e}")
            raise QueryError(f"Count users by subscription level failed: {e}")
    
    async def get_users_with_usage_stats(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get users with their usage statistics"""
        try:
            query = f"""
                SELECT 
                    u.*,
                    COUNT(DISTINCT mf.id) as media_files_count,
                    COUNT(DISTINCT pj.id) as processing_jobs_count
                FROM {self.table_name} u
                LEFT JOIN media_files mf ON u.id = mf.user_id
                LEFT JOIN processing_jobs pj ON u.id = pj.user_id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get users with usage stats: {e}")
            raise QueryError(f"Get users with usage stats failed: {e}")
    
    async def delete_user_cascade(self, user_id: Union[str, uuid.UUID]) -> bool:
        """Delete user and all related data (media files, jobs, etc.)"""
        try:
            async with self.connection.transaction():
                # Delete related processing jobs
                await self.connection.execute(
                    "DELETE FROM processing_jobs WHERE user_id = $1",
                    str(user_id)
                )
                
                # Delete related media files
                await self.connection.execute(
                    "DELETE FROM media_files WHERE user_id = $1",
                    str(user_id)
                )
                
                # Delete related transcription results
                await self.connection.execute(
                    "DELETE FROM transcription_results WHERE user_id = $1",
                    str(user_id)
                )
                
                # Delete the user
                result = await self.connection.execute(
                    f"DELETE FROM {self.table_name} WHERE id = $1",
                    str(user_id)
                )
                
                return result == "DELETE 1"
                
        except Exception as e:
            logger.error(f"Failed to delete user cascade {user_id}: {e}")
            raise QueryError(f"Delete user cascade failed: {e}")


# Import PostgresErrorHandler for error handling
from ..utils.postgres_errors import PostgresErrorHandler