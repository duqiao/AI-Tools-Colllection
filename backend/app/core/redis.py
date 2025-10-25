import redis.asyncio as redis
import logging
from typing import Optional
from datetime import datetime
import json

from app.core.config import settings

logger = logging.getLogger(__name__)

class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class RedisConnection:
    client: Optional[redis.Redis] = None

async def init_redis():
    """Initialize Redis connection"""
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            health_check_interval=30
        )
        
        # Test the connection
        await client.ping()
        
        RedisConnection.client = client
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        logger.warning("Application will continue without Redis (caching disabled)")
        RedisConnection.client = None

async def get_redis():
    """Get Redis client"""
    if RedisConnection.client is None:
        raise Exception("Redis not initialized. Call init_redis() first.")
    return RedisConnection.client

async def close_redis():
    """Close Redis connection"""
    if RedisConnection.client:
        await RedisConnection.client.close()
        logger.info("Redis connection closed")

# Redis helper functions
async def set_progress(task_id: str, progress_data: dict, expire_seconds: int = 86400):
    """Set progress data for a task"""
    try:
        client = await get_redis()
        import json
        await client.setex(
            f"progress:{task_id}",
            expire_seconds,
            json.dumps(progress_data)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to set progress for task {task_id}: {e}")
        return False

async def get_progress(task_id: str):
    """Get progress data for a task"""
    try:
        client = await get_redis()
        import json
        data = await client.get(f"progress:{task_id}")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Failed to get progress for task {task_id}: {e}")
        return None

async def delete_progress(task_id: str):
    """Delete progress data for a task"""
    try:
        client = await get_redis()
        await client.delete(f"progress:{task_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete progress for task {task_id}: {e}")
        return False

async def set_user_cache(user_id: str, data: dict, expire_seconds: int = 3600):
    """Set user data in cache"""
    try:
        client = await get_redis()
        await client.setex(
            f"user:{user_id}",
            expire_seconds,
            json.dumps(data, cls=DateTimeJSONEncoder)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to set user cache for {user_id}: {e}")
        return False

async def get_user_cache(user_id: str):
    """Get user data from cache"""
    try:
        client = await get_redis()
        import json
        data = await client.get(f"user:{user_id}")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Failed to get user cache for {user_id}: {e}")
        return None

async def increment_user_quota(user_id: str):
    """Increment user's quota usage"""
    try:
        client = await get_redis()
        key = f"quota:{user_id}"
        current = await client.incr(key)
        await client.expire(key, 86400)  # Reset after 24 hours
        return current
    except Exception as e:
        logger.error(f"Failed to increment quota for {user_id}: {e}")
        return None