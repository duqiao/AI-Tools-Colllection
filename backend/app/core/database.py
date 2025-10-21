from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

async def init_db():
    """Initialize database connection"""
    try:
        # Create MongoDB client
        client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=5000,  # 5 seconds
            connectTimeoutMS=10000,  # 10 seconds
            retryWrites=True,
            w="majority"
        )
        
        # Test the connection
        await client.admin.command('ping')
        
        Database.client = client
        Database.database = client.get_database()  # Extract database name from URI
        
        # Create indexes for performance
        await create_indexes()
        
        logger.info("MongoDB connection established successfully")
        
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Media files indexes
        await Database.database.media_files.create_index([("uploaded_by", ASCENDING), ("upload_date", DESCENDING)])
        await Database.database.media_files.create_index([("file_name", 1)], unique=True)
        
        # Processing jobs indexes
        await Database.database.processing_jobs.create_index([("job_id", 1)], unique=True)
        await Database.database.processing_jobs.create_index([("user", ASCENDING), ("status", ASCENDING)])
        await Database.database.processing_jobs.create_index([("status", ASCENDING), ("created_at", DESCENDING)])
        
        # Users indexes
        await Database.database.users.create_index([("openid", 1)], unique=True)
        await Database.database.users.create_index([("is_active", ASCENDING)])
        
        # Transcription results indexes
        await Database.database.transcription_results.create_index([("job_id", 1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")

async def get_db():
    """Get database instance"""
    if Database.database is None:
        raise Exception("Database not initialized. Call init_db() first.")
    return Database.database

async def close_db():
    """Close database connection"""
    if Database.client:
        Database.client.close()
        logger.info("MongoDB connection closed")

# Collection helpers
async def get_collection(collection_name: str):
    """Get a collection from the database"""
    db = await get_db()
    return db[collection_name]