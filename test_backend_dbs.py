#!/usr/bin/env python3
"""
Test Backend Database Connectivity
Tests if backend can connect to running Docker services
"""

import sys
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_database_connections():
    """Test backend database connections"""
    print("🔍 Testing Backend Database Connectivity")
    print("=" * 50)
    
    # Test MongoDB connection
    print("\n📊 Testing MongoDB Connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_mongo():
            try:
                client = AsyncIOMotorClient("mongodb://admin:dev123456@localhost:27018/ai_media_translation?authSource=admin")
                await client.admin.command('ping')
                print("✅ MongoDB connection successful!")
                await client.close()
                return True
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                return False
        
        result = asyncio.run(test_mongo())
        
    except ImportError as e:
        print(f"❌ MongoDB import error: {e}")
        result = False
    
    # Test Redis connection
    print("\n🔴 Testing Redis Connection...")
    try:
        import redis.asyncio as redis
        
        async def test_redis():
            try:
                client = redis.Redis.from_url("redis://:dev123456@localhost:6379/0")
                await client.ping()
                print("✅ Redis connection successful!")
                await client.close()
                return True
            except Exception as e:
                print(f"❌ Redis connection failed: {e}")
                return False
        
        redis_result = asyncio.run(test_redis())
        
    except ImportError as e:
        print(f"❌ Redis import error: {e}")
        redis_result = False
    
    # Test configuration
    print("\n⚙️  Testing Configuration...")
    try:
        from app.core.config import settings
        print(f"✅ Configuration loaded successfully!")
        print(f"   MongoDB URI: {settings.MONGODB_URI}")
        print(f"   Redis URL: {settings.REDIS_URL}")
        print(f"   Debug Mode: {settings.DEBUG}")
        config_ok = True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        config_ok = False
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    
    if result and redis_result and config_ok:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Backend is ready to start!")
        print("\n🚀 Run the following command:")
        print("   cd backend")
        print("   venv\\Scripts\\python.exe run.py")
        return True
    else:
        print("❌ Some tests failed!")
        print("\n🛠️  Troubleshooting:")
        if not result:
            print("   - MongoDB: Check Docker container is running")
        if not redis_result:
            print("   - Redis: Check Docker container is running")
        if not config_ok:
            print("   - Configuration: Check environment variables")
        return False

if __name__ == "__main__":
    success = test_database_connections()
    print(f"\n{'='*50}")
    if success:
        print("✅ Ready to start backend!")
    else:
        print("❌ Fix issues before starting backend")
    
    input("\nPress Enter to continue...")
    sys.exit(0 if success else 1)