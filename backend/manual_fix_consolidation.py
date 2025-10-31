#!/usr/bin/env python3
"""
MANUAL FIX FOR DATA CONSOLIDATION
=================================

Force update all jobs to use MySelectedUser
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def manual_fix():
    from app.core.database import init_db, get_collection
    await init_db()
    
    selected_user_id = "68fc5af3d27a3e281b1e8b68"
    
    print("MANUAL FIX FOR DATA CONSOLIDATION")
    print("=" * 40)
    print(f"Target User ID: {selected_user_id}")
    print()
    
    # Update processing jobs
    print("Updating processing_jobs...")
    jobs_collection = await get_collection("processing_jobs")
    
    # Get all jobs
    all_jobs = await jobs_collection.find({}).to_list(None)
    print(f"Found {len(all_jobs)} jobs")
    
    # Update each job individually
    updated_count = 0
    for job in all_jobs:
        current_user_id = job["userId"]
        if current_user_id != selected_user_id:
            result = await jobs_collection.update_one(
                {"_id": job["_id"]},
                {"$set": {"userId": selected_user_id}}
            )
            if result.modified_count > 0:
                updated_count += 1
                print(f"  Updated job {job['jobId']}: {current_user_id} -> {selected_user_id}")
    
    print(f"Updated {updated_count} jobs")
    
    # Update transcription results
    print("\nUpdating transcription_results...")
    results_collection = await get_collection("transcription_results")
    
    # Get all results
    all_results = await results_collection.find({}).to_list(None)
    print(f"Found {len(all_results)} results")
    
    # Update each result individually
    updated_results = 0
    for result in all_results:
        current_user_id = result["userId"]
        if current_user_id != selected_user_id:
            result_update = await results_collection.update_one(
                {"_id": result["_id"]},
                {"$set": {"userId": selected_user_id}}
            )
            if result_update.modified_count > 0:
                updated_results += 1
                print(f"  Updated result for job {result['jobId']}: {current_user_id} -> {selected_user_id}")
    
    print(f"Updated {updated_results} results")
    
    # Verify the fix
    print("\nVerifying fix...")
    
    # Count jobs by user
    jobs_by_user = {}
    for job in await jobs_collection.find({}).to_list(None):
        user_id = job["userId"]
        jobs_by_user[user_id] = jobs_by_user.get(user_id, 0) + 1
    
    print("Jobs by user after fix:")
    for user_id, count in jobs_by_user.items():
        print(f"  {user_id}: {count} jobs")
    
    # Count results by user
    results_by_user = {}
    for result in await results_collection.find({}).to_list(None):
        user_id = result["userId"]
        results_by_user[user_id] = results_by_user.get(user_id, 0) + 1
    
    print("Results by user after fix:")
    for user_id, count in results_by_user.items():
        print(f"  {user_id}: {count} results")
    
    # Final verification
    selected_user_jobs = jobs_by_user.get(selected_user_id, 0)
    selected_user_results = results_by_user.get(selected_user_id, 0)
    total_jobs = sum(jobs_by_user.values())
    total_results = sum(results_by_user.values())
    
    print(f"\nFINAL SUMMARY:")
    print(f"  Selected User Jobs: {selected_user_jobs}/{total_jobs} ({(selected_user_jobs/total_jobs*100):.1f}%)")
    print(f"  Selected User Results: {selected_user_results}/{total_results} ({(selected_user_results/total_results*100):.1f}%)")
    
    if selected_user_jobs == total_jobs and selected_user_results == total_results:
        print(f"  SUCCESS: All data now belongs to selected user!")
        return True
    else:
        print(f"  PARTIAL: Some data still belongs to other users")
        return False

if __name__ == "__main__":
    success = asyncio.run(manual_fix())
    if success:
        print("\nManual fix completed successfully!")
    else:
        print("\nManual fix partially completed - check logs above")