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
        # Clean up any documents with null values that would violate unique indexes
        await Database.database.media_files.delete_many({"fileName": None})
        await Database.database.processing_jobs.delete_many({"jobId": None})
        await Database.database.users.delete_many({"openid": None})
        
        # Drop existing indexes to avoid conflicts
        await Database.database.media_files.drop_indexes()
        await Database.database.processing_jobs.drop_indexes()
        await Database.database.users.drop_indexes()
        await Database.database.transcription_results.drop_indexes()
        
        # Media files indexes
        await Database.database.media_files.create_index([("uploaded_by", ASCENDING), ("upload_date", DESCENDING)])
        await Database.database.media_files.create_index([("fileName", 1)], unique=True)  # camelCase to match upload.py
        
        # Processing jobs indexes
        await Database.database.processing_jobs.create_index([("jobId", 1)], unique=True)  # camelCase to match upload.py
        await Database.database.processing_jobs.create_index([("userId", ASCENDING), ("processing.status", ASCENDING)])  # camelCase userId
        await Database.database.processing_jobs.create_index([("processing.status", ASCENDING), ("createdAt", DESCENDING)])
        
        # Users indexes
        await Database.database.users.create_index([("openid", 1)], unique=True)
        await Database.database.users.create_index([("is_active", ASCENDING)])
        
        # Transcription results indexes
        await Database.database.transcription_results.create_index([("jobId", 1)])  # camelCase to match upload.py
        
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