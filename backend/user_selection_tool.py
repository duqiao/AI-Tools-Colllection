#!/usr/bin/env python3
"""
USER SELECTION TOOL
==================

List, select, and work with specific users
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def list_all_users():
    """List all users in the database"""
    from app.core.database import init_db, get_collection
    
    await init_db()
    users_collection = await get_collection("users")
    
    users = await users_collection.find({}).sort("createdAt", -1).to_list(None)
    
    print("ALL USERS IN DATABASE")
    print("=" * 50)
    
    if not users:
        print("No users found in database")
        return []
    
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.get('username', 'Unknown')}")
        print(f"   ID: {user['_id']}")
        print(f"   Email: {user.get('email', 'N/A')}")
        print(f"   OpenID: {user.get('openid', 'N/A')}")
        print(f"   Subscription: {user.get('subscription_level', 'free')}")
        print(f"   Quota: {user.get('quota_used', 0)}/{user.get('quota_limit', 10)}")
        print(f"   Active: {user.get('is_active', True)}")
        print(f"   Created: {user.get('createdAt', 'Unknown')}")
        print()
    
    return users

async def create_test_user(username=None):
    """Create a new test user"""
    from app.core.database import init_db, get_collection
    from app.api.auth import guest_login
    from app.models.schemas import UserCreate
    
    await init_db()
    
    if not username:
        username = f"TestUser_{int(asyncio.get_event_loop().time())}"
    
    guest_data = UserCreate(
        username=username,
        openid=f"test_{username}_{uuid.uuid4().hex[:8]}"
    )
    
    try:
        guest_user = await guest_login(guest_data)
        user_id = guest_user.user.id
        print(f"✅ Created test user: {username}")
        print(f"   User ID: {user_id}")
        return user_id
    except Exception as e:
        print(f"❌ Failed to create user: {e}")
        return None

async def transfer_jobs_to_user(from_user_id=None, to_user_id=None):
    """Transfer all jobs from one user to another"""
    from app.core.database import init_db, get_collection
    
    await init_db()
    jobs_collection = await get_collection("processing_jobs")
    results_collection = await get_collection("transcription_results")
    
    if not to_user_id:
        print("❌ Target user ID required")
        return
    
    # Update jobs
    if from_user_id:
        job_filter = {"userId": from_user_id}
        print(f"Transferring jobs from user {from_user_id}")
    else:
        job_filter = {}  # All jobs
        print(f"Transferring ALL jobs to user {to_user_id}")
    
    # Update processing jobs
    job_result = await jobs_collection.update_many(
        job_filter,
        {"$set": {"userId": to_user_id, "updatedAt": asyncio.get_event_loop().time()}}
    )
    
    # Update transcription results
    result_result = await results_collection.update_many(
        job_filter,
        {"$set": {"userId": to_user_id}}
    )
    
    print(f"✅ Updated {job_result.modified_count} processing jobs")
    print(f"✅ Updated {result_result.modified_count} transcription results")

async def get_user_token(user_id):
    """Get a fresh token for a specific user"""
    from app.core.database import init_db, get_collection
    from app.api.auth import create_access_token
    
    await init_db()
    users_collection = await get_collection("users")
    
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        print(f"❌ User {user_id} not found")
        return None
    
    token = create_access_token(data={"sub": str(user["_id"])})
    
    print(f"✅ Token for user {user.get('username')}:")
    print(f"   {token}")
    return token

async def main():
    """Main user selection interface"""
    print("USER SELECTION TOOL")
    print("=" * 30)
    
    while True:
        print("\nOptions:")
        print("1. List all users")
        print("2. Create test user")
        print("3. Get user token")
        print("4. Transfer jobs to user")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            await list_all_users()
        
        elif choice == "2":
            username = input("Enter username (leave blank for auto): ").strip()
            if not username:
                username = None
            await create_test_user(username)
        
        elif choice == "3":
            user_id = input("Enter user ID: ").strip()
            await get_user_token(user_id)
        
        elif choice == "4":
            from_user = input("Enter from user ID (leave blank for ALL): ").strip()
            to_user = input("Enter to user ID: ").strip()
            
            from_user_id = from_user if from_user else None
            to_user_id = to_user if to_user else None
            
            await transfer_jobs_to_user(from_user_id, to_user_id)
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())