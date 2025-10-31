#!/usr/bin/env python3
"""
Create Test User Script

This script creates a persistent test user that can be used for development and testing.
The test user has consistent credentials that can be used across the application.
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.repositories.user_repository import UserRepository
from app.models.schemas import SubscriptionLevel
from app.core.postgres_db import Database
from passlib.context import CryptContext

async def create_test_user():
    """Create a persistent test user"""
    print("🚀 Creating test user...")
    
    try:
        # Initialize database connection
        db = Database()
        await db.init_connection_pool()
        
        # Test user data
        test_user_data = {
            "username": "test_user",
            "email": "test_user@example.com",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0K.WdIlKW6",  # "test123456"
            "subscription_level": SubscriptionLevel.FREE,
            "profile": {
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": "https://ui-avatars.com/api/?name=Test+User&background=10B981&color=fff",
                "is_test_user": True,
                "created_by": "init_script"
            },
            "usage_stats": {
                "total_files_processed": 0,
                "total_audio_duration": 0,
                "api_calls_count": 0,
                "storage_used_bytes": 0
            }
        }
        
        # Create the user
        async with UserRepository() as user_repo:
            # Check if test user already exists
            existing_user = await user_repo.get_by_username("test_user")
            if existing_user:
                print(f"✅ Test user already exists: {existing_user['id']}")
                user_id = existing_user["id"]
            else:
                print("📝 Creating new test user...")
                user_id = await user_repo.create(test_user_data)
                print(f"✅ Test user created successfully: {user_id}")
            
            # Verify the user can be retrieved
            created_user = await user_repo.get_by_id(user_id)
            if created_user:
                print("✅ Test user verification successful")
                print(f"   Username: {created_user['username']}")
                print(f"   Email: {created_user['email']}")
                print(f"   Subscription: {created_user['subscription_level']}")
                print(f"   User ID: {created_user['id']}")
                print(f"   Created at: {created_user.get('created_at')}")
                return True
            else:
                print("❌ Failed to retrieve created user")
                return False
                
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False
    finally:
        # Close database connection
        if 'db' in locals():
            await db.close_connection_pool()

async def create_guest_test_user():
    """Create a guest test user with openid"""
    print("\n🔓 Creating guest test user...")
    
    try:
        # Initialize database connection
        db = Database()
        await db.init_connection_pool()
        
        # Guest test user data
        guest_user_data = {
            "username": "test_user",
            "email": "guest_test_user@test.ai",
            "password_hash": "guest_user_no_password",  # Guest users don't have passwords
            "subscription_level": SubscriptionLevel.FREE,
            "profile": {
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": "https://ui-avatars.com/api/?name=Test+User&background=10B981&color=fff",
                "is_guest": True,
                "openid": "test_user_ai",
                "created_by": "init_script"
            },
            "usage_stats": {
                "total_files_processed": 0,
                "total_audio_duration": 0,
                "api_calls_count": 0,
                "storage_used_bytes": 0
            }
        }
        
        # Create the guest user
        async with UserRepository() as user_repo:
            # Check if guest test user already exists
            existing_user = await user_repo.get_by_email("guest_test_user@test.ai")
            if existing_user:
                print(f"✅ Guest test user already exists: {existing_user['id']}")
                user_id = existing_user["id"]
            else:
                print("📝 Creating new guest test user...")
                user_id = await user_repo.create(guest_user_data)
                print(f"✅ Guest test user created successfully: {user_id}")
            
            # Verify the guest user can be retrieved
            created_user = await user_repo.get_by_id(user_id)
            if created_user:
                print("✅ Guest test user verification successful")
                print(f"   Username: {created_user['username']}")
                print(f"   Email: {created_user['email']}")
                print(f"   OpenID: {created_user.get('profile', {}).get('openid', 'N/A')}")
                print(f"   Subscription: {created_user['subscription_level']}")
                print(f"   User ID: {created_user['id']}")
                print(f"   Created at: {created_user.get('created_at')}")
                return True
            else:
                print("❌ Failed to retrieve created guest user")
                return False
                
    except Exception as e:
        print(f"❌ Error creating guest test user: {e}")
        return False
    finally:
        # Close database connection
        if 'db' in locals():
            await db.close_connection_pool()

async def main():
    """Main function to create test users"""
    print("🎯 AI Media Translation - Test User Initialization")
    print("=" * 60)
    
    # Create regular test user
    regular_success = await create_test_user()
    
    # Create guest test user  
    guest_success = await create_guest_test_user()
    
    print("\n" + "=" * 60)
    if regular_success and guest_success:
        print("🎉 All test users created successfully!")
        print("\n📋 Test User Credentials:")
        print("   Regular User:")
        print("     - Username: test_user")
        print("     - Email: test_user@example.com")
        print("     - Password: test123456")
        print("\n   Guest User:")
        print("     - Username: test_user")
        print("     - OpenID: test_user_ai")
        print("     - Email: guest_test_user@test.ai")
        print("\n✅ Ready for testing!")
    else:
        print("❌ Some test user creation failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())