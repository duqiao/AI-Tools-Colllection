"""
PostgreSQL Database Module

This module provides PostgreSQL database connection and pooling functionality
using asyncpg for high-performance async database operations.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL database connection manager"""
    
    pool: Optional[asyncpg.Pool] = None
    
    @classmethod
    async def init_db(cls):
        """Initialize database connection pool"""
        try:
            logger.info("Initializing PostgreSQL database connection pool...")
            
            cls.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=settings.DATABASE_MIN_CONNECTIONS,
                max_size=settings.DATABASE_POOL_SIZE,
                command_timeout=settings.DATABASE_COMMAND_TIMEOUT,
                # Connection configuration
                server_settings={
                    'application_name': 'ai_media_translation_api',
                    'timezone': 'UTC',
                }
            )
            
            # Test the connection
            async with cls.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info(f"PostgreSQL connection pool initialized successfully")
            logger.info(f"Pool configuration: min={settings.DATABASE_MIN_CONNECTIONS}, max={settings.DATABASE_POOL_SIZE}")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close database connection pool"""
        if cls.pool:
            await cls.pool.close()
            cls.pool = None
            logger.info("PostgreSQL connection pool closed")
    
    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """Get database connection pool"""
        if cls.pool is None:
            await cls.init_db()
        return cls.pool
    
    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Get database connection from pool"""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            yield connection


# Dependency injection for FastAPI
async def get_db_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """FastAPI dependency for database pool"""
    pool = await Database.get_pool()
    yield pool


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency for database connection"""
    async with Database.get_connection() as connection:
        yield connection


class DatabaseError(Exception):
    """Custom database error"""
    pass


class ConnectionError(DatabaseError):
    """Connection-related errors"""
    pass


class QueryError(DatabaseError):
    """Query execution errors"""
    pass


# Database health check
async def check_database_health() -> Dict[str, Any]:
    """Check database health and connection status"""
    try:
        pool = await Database.get_pool()
        
        async with pool.acquire() as conn:
            # Test basic connectivity
            start_time = time.time()
            await conn.fetchval("SELECT 1")
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Get connection pool stats
            pool_stats = pool.get_size()
            
            # Get database version
            version = await conn.fetchval("SELECT version()")
            
            # Check table existence
            tables = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            )
            
            return {
                "status": "healthy",
                "connection": {
                    "status": "connected",
                    "response_time_ms": round(response_time, 2),
                    "pool_size": pool_stats,
                    "database_url": settings.DATABASE_URL.split('@')[0] + '@***',  # Hide credentials
                },
                "database": {
                    "version": version.split(',')[0],
                    "tables_count": len(tables),
                    "tables": [row["table_name"] for row in tables]
                }
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": {
                "status": "disconnected",
                "response_time_ms": None,
                "pool_size": None,
                "database_url": "unknown"
            },
            "database": {
                "version": None,
                "tables_count": 0,
                "tables": []
            }
        }


# Utility functions for common database operations
async def execute_query(query: str, *args) -> List[Dict[str, Any]]:
    """Execute a query and return results"""
    try:
        async with Database.get_connection() as conn:
            if args:
                result = await conn.fetch(query, *args)
            else:
                result = await conn.fetch(query)
            
            return [dict(row) for row in result]
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise QueryError(f"Query failed: {e}")


async def execute_query_single(query: str, *args) -> Optional[Dict[str, Any]]:
    """Execute a query and return a single result"""
    try:
        async with Database.get_connection() as conn:
            if args:
                row = await conn.fetchrow(query, *args)
            else:
                row = await conn.fetchrow(query)
            
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise QueryError(f"Query failed: {e}")


async def execute_command(query: str, *args) -> str:
    """Execute a command (INSERT, UPDATE, DELETE) and return result"""
    try:
        async with Database.get_connection() as conn:
            if args:
                result = await conn.execute(query, *args)
            else:
                result = await conn.execute(query)
            
            return str(result)
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        raise QueryError(f"Command failed: {e}")


# Time utility for database operations
import time


# Initialize database on module import (optional)
async def ensure_database_connected():
    """Ensure database is connected, useful for startup"""
    try:
        pool = await Database.get_pool()
        logger.info("Database connection verified")
    except Exception as e:
        logger.warning(f"Database connection verification failed: {e}")


# Module-level functions for backward compatibility
async def init_db():
    """Initialize database connection pool (module-level function for compatibility)"""
    await Database.init_db()


def get_db():
    """Get database instance (module-level function for compatibility)"""
    return Database


# Export the database class for backward compatibility
database = Database