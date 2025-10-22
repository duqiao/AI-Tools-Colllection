#!/usr/bin/env python3
"""
Docker Database Connectivity Test
Tests MongoDB and Redis connections from Docker containers
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

async def test_docker_databases():
    """Test connections to Docker databases"""
    print("🔍 Testing Docker Database Connections...")
    print("=" * 50)
    
    # Test MongoDB via Docker
    print("\n📊 Testing MongoDB Connection:")
    try:
        import motor.motor_asyncio
        
        # Use MongoDB Docker container connection string
        mongo_uri = "mongodb://admin:dev123456@localhost:27018/ai_media_translation?authSource=admin"
        client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        
        # Test the connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        print(f"   Connected to: localhost:27018")
        
        # Test database operations
        db = client.ai_media_translation
        await db.test_collection.insert_one({"test": "docker_connection", "status": "success"})
        count = await db.test_collection.count_documents({"test": "docker_connection"})
        print(f"   Database operations working: {count} test documents")
        
        # Cleanup
        await db.test_collection.delete_many({"test": "docker_connection"})
        await client.close()
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
    
    # Test Redis via Docker
    print("\n🔴 Testing Redis Connection:")
    try:
        import redis.asyncio as redis
        
        # Use Redis Docker container connection string
        redis_url = "redis://:dev123456@localhost:6379/0"
        client = redis.Redis.from_url(redis_url)
        
        # Test the connection
        await client.ping()
        print("✅ Redis connection successful!")
        print(f"   Connected to: localhost:6379")
        
        # Test basic operations
        await client.set("docker_test", "connection_success")
        value = await client.get("docker_test")
        print(f"   Redis operations working: {value.decode() if value else 'None'}")
        
        # Cleanup
        await client.delete("docker_test")
        await client.close()
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Docker database connectivity test completed!")

if __name__ == "__main__":
    asyncio.run(test_docker_databases())