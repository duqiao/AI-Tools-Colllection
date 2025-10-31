#!/usr/bin/env python3
"""
Compare user IDs in jobs vs authentication
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def compare_user_ids():
    from app.core.database import init_db, get_collection
    
    await init_db()
    
    print("COMPARING USER IDS")
    print("=" * 30)
    
    # Get user ID from authentication
    auth_user_id = "68fc5af3d27a3e281b1e8b68"
    print(f"Auth user ID: {auth_user_id}")
    
    # Check jobs collection
    collection = await get_collection("processing_jobs")
    
    # Get all unique user IDs from jobs
    jobs = await collection.find({}).to_list(None)
    user_ids_in_jobs = set(job["userId"] for job in jobs)
    
    print(f"User IDs found in jobs ({len(user_ids_in_jobs)} unique):")
    for user_id in sorted(user_ids_in_jobs):
        count = await collection.count_documents({"userId": user_id})
        match = "MATCH" if user_id == auth_user_id else "NO MATCH"
        print(f"  {user_id}: {count} jobs {match}")
    
    # Check if there are any jobs with the auth user ID
    auth_user_jobs = await collection.find({"userId": auth_user_id}).to_list(None)
    print(f"\nJobs for auth user {auth_user_id}: {len(auth_user_jobs)}")
    
    if auth_user_jobs:
        job = auth_user_jobs[0]
        print(f"Sample job: {job['jobId']}")

if __name__ == "__main__":
    asyncio.run(compare_user_ids())