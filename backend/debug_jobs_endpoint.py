#!/usr/bin/env python3
"""
Debug the jobs endpoint
"""

import asyncio
import sys
import json
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def debug_jobs():
    from app.core.database import init_db, get_collection
    import time
    
    await init_db()
    
    print("DEBUG: Testing jobs endpoint manually")
    print("=" * 50)
    
    # Create or get a test user (MySelectedUser)
    selected_user_id = "68fc5af3d27a3e281b1e8b68"
    
    # Mock current_user object
    mock_current_user = {
        "id": selected_user_id,
        "username": "MySelectedUser",
        "openid": "my_selected_user_permanent"
    }
    
    print(f"Mock user: {mock_current_user}")
    
    # Test the database query directly
    collection = await get_collection("processing_jobs")
    
    # Build query (same as in the endpoint)
    query = {"userId": mock_current_user["id"]}
    print(f"Query: {query}")
    
    # Get total count
    total = await collection.count_documents(query)
    print(f"Total jobs found: {total}")
    
    # Get jobs with pagination
    jobs = await collection.find(query).sort("createdAt", -1).skip(0).limit(5).to_list(None)
    print(f"Jobs returned: {len(jobs)}")
    
    if jobs:
        print("First job:")
        job = jobs[0]
        print(f"  Job ID: {job['jobId']}")
        print(f"  Status: {job['processing']['status']}")
        print(f"  User ID: {job['userId']}")
    
    # Test if the user exists in the users collection
    users_collection = await get_collection("users")
    user = await users_collection.find_one({"_id": selected_user_id})
    if user:
        print(f"User found in database: {user.get('username')}")
    else:
        print("User NOT found in database")
    
    return total > 0

if __name__ == "__main__":
    has_jobs = asyncio.run(debug_jobs())
    print(f"\nResult: {'SUCCESS' if has_jobs else 'NO JOBS FOUND'}")