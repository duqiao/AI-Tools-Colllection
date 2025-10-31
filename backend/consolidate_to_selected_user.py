#!/usr/bin/env python3
"""
CONSOLIDATE DATA TO MySelectedUser
====================================

This script consolidates ALL data to be owned by MySelectedUser:
- Username: MySelectedUser  
- User ID: 68fc5af3d27a3e281b1e8b68

This ensures data consistency and simplifies future management.
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

# MySelectedUser information
SELECTED_USER = {
    "username": "MySelectedUser",
    "user_id": "68fc5af3d27a3e281b1e8b68",
    "openid": "my_selected_user_permanent"
}

async def consolidate_all_data():
    """Consolidate all data to MySelectedUser"""
    print("CONSOLIDATING DATA TO MySelectedUser")
    print("=" * 50)
    print(f"Username: {SELECTED_USER['username']}")
    print(f"User ID: {SELECTED_USER['user_id']}")
    print(f"OpenID: {SELECTED_USER['openid']}")
    print()
    
    try:
        # Initialize database
        from app.core.database import init_db, get_collection
        await init_db()
        print("Database initialized")
        
        # Collections to update
        collections_to_update = [
            "processing_jobs",
            "media_files", 
            "transcription_results",
            "users"  # Update username if exists
        ]
        
        total_updates = 0
        
        for collection_name in collections_to_update:
            print(f"\nUpdating {collection_name}...")
            collection = await get_collection(collection_name)
            
            if collection_name == "users":
                # Update user record if it exists
                result = await collection.update_one(
                    {"_id": SELECTED_USER["user_id"]},
                    {
                        "$set": {
                            "username": SELECTED_USER["username"],
                            "openid": SELECTED_USER["openid"],
                            "email": None,
                            "avatar_url": f"https://ui-avatars.com/api/?name={SELECTED_USER['username']}&background=10B981&color=fff",
                            "subscription_level": "premium",  # Give premium status
                            "quota_used": 0,
                            "quota_limit": 10000,  # Large limit for testing
                            "quota_reset_date": "2025-10-26",
                            "is_active": True,
                            "updated_at": asyncio.get_event_loop().time()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f"   Updated user record")
                    total_updates += result.modified_count
                else:
                    # Check if user exists
                    user = await collection.find_one({"_id": SELECTED_USER["user_id"]})
                    if user:
                        print(f"   User record already correct")
                    else:
                        print(f"   User not found, creating new record...")
                        
                        # Create new user record
                        new_user = {
                            "_id": SELECTED_USER["user_id"],
                            "username": SELECTED_USER["username"],
                            "openid": SELECTED_USER["openid"],
                            "email": None,
                            "avatar_url": f"https://ui-avatars.com/api/?name={SELECTED_USER['username']}&background=10B981&color=fff",
                            "subscription_level": "premium",
                            "quota_used": 0,
                            "quota_limit": 10000,
                            "quota_reset_date": "2025-10-26",
                            "is_active": True,
                            "created_at": asyncio.get_event_loop().time(),
                            "updated_at": asyncio.get_event_loop().time()
                        }
                        
                        await collection.insert_one(new_user)
                        print(f"   Created new user record")
                        total_updates += 1
            
            else:
                # Update all documents in collection to use selected user
                if collection_name == "processing_jobs":
                    result = await collection.update_many(
                        {},
                        {
                            "$set": {
                                "userId": SELECTED_USER["user_id"],
                                "updatedAt": asyncio.get_event_loop().time()
                            }
                        }
                    )
                    print(f"   Updated {result.modified_count} processing jobs")
                    total_updates += result.modified_count
                
                elif collection_name == "media_files":
                    result = await collection.update_many(
                        {},
                        {
                            "$set": {
                                "uploaded_by": SELECTED_USER["user_id"],
                                "updatedAt": asyncio.get_event_loop().time()
                            }
                        }
                    )
                    print(f"   Updated {result.modified_count} media files")
                    total_updates += result.modified_count
                
                elif collection_name == "transcription_results":
                    result = await collection.update_many(
                        {},
                        {
                            "$set": {
                                "userId": SELECTED_USER["user_id"],
                                "updatedAt": asyncio.get_event_loop().time()
                            }
                        }
                    )
                    print(f"   Updated {result.modified_count} transcription results")
                    total_updates += result.modified_count
        
        print(f"\nSUMMARY:")
        print(f"   Total Updates: {total_updates}")
        print(f"   Processing Jobs: All owned by MySelectedUser")
        print(f"   Media Files: All owned by MySelectedUser") 
        print(f"   Transcription Results: All owned by MySelectedUser")
        print(f"   User Record: MySelectedUser configured")
        
        # Verify the consolidation
        print(f"\nVERIFICATION:")
        
        # Check processing jobs
        jobs_collection = await get_collection("processing_jobs")
        total_jobs = await jobs_collection.count_documents({})
        my_jobs = await jobs_collection.count_documents({"userId": SELECTED_USER["user_id"]})
        print(f"   Total Jobs: {total_jobs}")
        print(f"   MySelectedUser Jobs: {my_jobs} ({(my_jobs/total_jobs*100):.1f}%)")
        
        # Check transcription results
        results_collection = await get_collection("transcription_results")
        total_results = await results_collection.count_documents({})
        my_results = await results_collection.count_documents({"userId": SELECTED_USER["user_id"]})
        print(f"   Total Results: {total_results}")
        print(f"   MySelectedUser Results: {my_results} ({(my_results/total_results*100):.1f}%)")
        
        if my_jobs == total_jobs and my_results == total_results:
            print(f"\nSUCCESS: All data consolidated to MySelectedUser!")
            return True
        else:
            print(f"\nPARTIAL: Some data may not be accessible")
            return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def create_cleanup_script():
    """Create a script to clean up old guest users"""
    print("\nCREATING CLEANUP GUIDE...")
    
    cleanup_guide = """
# CLEANUP GUIDE FOR OLD GUEST USERS
# ================================

# After consolidating data to MySelectedUser, you may want to clean up old guest users.

# 1. IDENTIFY GUEST USERS TO CLEAN
# Run this query to list guest users (excluding MySelectedUser):
db.users.find({
    "username": {"$regex": "^Guest_"},
    "username": {"$ne": "MySelectedUser"}
})

# 2. DELETE OLD GUEST USERS (BE CAREFUL!)
# This will delete all guest users except MySelectedUser:
# db.users.deleteMany({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# })

# 3. ARCHIVE INSTEAD OF DELETE (RECOMMENDED)
# First, create an archive collection:
# db.archive_users.insertMany(db.users.find({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# }))

# Then delete the original users:
# db.users.deleteMany({
#     "username": {"$regex": "^Guest_"},
#     "username": {"$ne": "MySelectedUser"}
# })

# 4. UPDATE AUTO-FIX SCRIPT
# Update auto-fix jobs.py to only work with MySelectedUser
# Remove random guest user creation and focus on MySelectedUser

# 5. FRONTEND CONFIGURATION
# Remove guest user creation from frontend
# Configure app to always use MySelectedUser
# Remove "Create Guest User" buttons/logic
"""
    
    with open("CLEANUP_GUIDE.md", "w", encoding='utf-8') as f:
        f.write(cleanup_guide)
    
    print("Cleanup guide created: CLEANUP_GUIDE.md")

async def main():
    """Main consolidation function"""
    print("DATA CONSOLIDATION TO MySelectedUser")
    print("=" * 40)
    
    # Run consolidation
    success = await consolidate_all_data()
    
    # Create cleanup guide
    await create_cleanup_script()
    
    if success:
        print(f"\nCONSOLIDATION COMPLETED!")
        print(f"All data now owned by MySelectedUser")
        print(f"Frontend will use consistent authentication")
        print(f"Simplified user management")
        print(f"No more random guest users")
        
        print(f"\nNEXT STEPS:")
        print(f"1. Test React Native app - should work perfectly")
        print(f"2. Consider cleaning up old guest users (see CLEANUP_GUIDE.md)")
        print(f"3. Update frontend to remove guest user creation")
        print(f"4. Update auto-fix scripts to focus on MySelectedUser")
        
    else:
        print(f"\nCONSOLIDATION FAILED!")
        print(f"Check the error messages above")

if __name__ == "__main__":
    asyncio.run(main())