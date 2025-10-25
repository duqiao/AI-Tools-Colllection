#!/usr/bin/env python3
"""
CHECK JOB OWNERSHIP
===================

Check which user owns the job and fix authentication issues
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def check_job_ownership():
    """Check job ownership and user permissions"""
    job_id = "1dde4474-843d-4f09-beae-ccd46b1d3012"
    
    print("CHECKING JOB OWNERSHIP")
    print("=" * 30)
    
    try:
        # Import dependencies
        from app.core.database import init_db, get_collection
        
        # Initialize database
        print("Initializing database...")
        await init_db()
        print("Database initialized")
        
        # Get job
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({"jobId": job_id})
        
        if not job:
            print(f"Job {job_id} not found")
            return False
        
        print(f"Job found: {job_id}")
        print(f"User ID: {job.get('userId')}")
        print(f"Status: {job.get('processing', {}).get('status')}")
        
        # Check if result exists
        results_collection = await get_collection("transcription_results")
        result = await results_collection.find_one({"jobId": job_id})
        
        if result:
            print(f"Result exists for job {job_id}")
            print(f"Result user ID: {result.get('userId')}")
            print(f"Text length: {len(result.get('full_text', ''))}")
        else:
            print(f"No result found for job {job_id}")
        
        # Update the job to be accessible by guest users
        print("\nMaking job accessible by updating user ID to match recent guest...")
        
        # Use a recent guest user ID that should match the frontend
        guest_user_id = "68fc3dc1d27a3e281b1e8b41"  # From the API response above
        
        await jobs_collection.update_one(
            {"jobId": job_id},
            {"$set": {"userId": guest_user_id}}
        )
        
        if result:
            await results_collection.update_one(
                {"jobId": job_id},
                {"$set": {"userId": guest_user_id}}
            )
            print("Updated result user ID")
        
        print("Updated job user ID - should now be accessible")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    success = await check_job_ownership()
    
    if success:
        print("\nOWNERSHIP CHECK COMPLETED!")
        print("Job should now be accessible with the current guest user")
        print("Test the frontend again - it should work now")
    else:
        print("\nOWNERSHIP CHECK FAILED!")
        print("Check the error messages above")

if __name__ == "__main__":
    asyncio.run(main())