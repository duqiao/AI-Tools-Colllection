#!/usr/bin/env python3
"""
Test Backend Database Connectivity
Tests if backend can connect to running Docker services
"""

import sys
import time
import asyncio
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_connections():
    """Test database connections"""
    print("Testing Backend Database Connectivity")
    print("=" * 50)
    
    # Test MongoDB connection
    print("\nTesting MongoDB Connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        
        client = AsyncIOMotorClient("mongodb://admin:dev123456@localhost:27018/ai_media_translation?authSource=admin")
        await client.admin.command('ping')
        print("SUCCESS: MongoDB connection successful!")
        await client.close()
        mongo_ok = True
        
    except Exception as e:
        print(f"FAILED: MongoDB connection failed: {e}")
        mongo_ok = False
    
    # Test Redis connection
    print("\nTesting Redis Connection...")
    try:
        import redis.asyncio as redis
        
        client = redis.Redis.from_url("redis://:dev123456@localhost:6379/0")
        await client.ping()
        print("SUCCESS: Redis connection successful!")
        await client.close()
        redis_ok = True
        
    except Exception as e:
        print(f"FAILED: Redis connection failed: {e}")
        redis_ok = False
    
    # Test configuration
    print("\nTesting Configuration...")
    try:
        from app.core.config import settings
        print("SUCCESS: Configuration loaded!")
        print(f"   MongoDB URI: {settings.MONGODB_URI}")
        print(f"   Redis URL: {settings.REDIS_URL}")
        config_ok = True
    except Exception as e:
        print(f"FAILED: Configuration error: {e}")
        config_ok = False
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"   MongoDB: {'OK' if mongo_ok else 'FAILED'}")
    print(f"   Redis: {'OK' if redis_ok else 'FAILED'}")
    print(f"   Config: {'OK' if config_ok else 'FAILED'}")
    
    if mongo_ok and redis_ok and config_ok:
        print("\nALL TESTS PASSED!")
        print("Backend is ready to start!")
        return True
    else:
        print("\nSome tests failed!")
        print("Fix issues before starting backend")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connections())
    print("\n" + "="*50)
    if success:
        print("READY: You can start the backend now!")
        print("\nCommand to run:")
        print("   cd backend")
        print("   venv\\\\Scripts\\\\python.exe run.py")
    else:
        print("FAILED: Fix database connections first")
    
    input("\nPress Enter to continue...")
    sys.exit(0 if success else 1)