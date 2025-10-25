#!/usr/bin/env python3
"""
DEBUG JOB STATUS
================

Debug specific job status and manually trigger processing
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import get_collection
from app.core.redis import get_redis, set_progress
from app.services.media_processor import MediaProcessor
from datetime import datetime

async def debug_job(job_id: str):
    """Debug specific job"""
    print(f"🔍 DEBUGGING JOB: {job_id}")
    print("=" * 50)
    
    try:
        # Check job in database
        print("📋 Checking job in database...")
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({"jobId": job_id})
        
        if not job:
            print(f"❌ Job {job_id} not found in database")
            return False
        
        print(f"✅ Job found in database")
        print(f"   Status: {job.get('processing', {}).get('status', 'unknown')}")
        print(f"   Progress: {job.get('processing', {}).get('progress', 0)}%")
        print(f"   Created: {job.get('createdAt')}")
        print(f"   User ID: {job.get('userId')}")
        
        # Check media file
        media_file_id = job.get("mediaFileId")
        if media_file_id:
            print(f"\n📁 Checking media file...")
            media_collection = await get_collection("media_files")
            media_file = await media_collection.find_one({"_id": media_file_id})
            
            if media_file:
                print(f"✅ Media file found")
                print(f"   Filename: {media_file.get('filename')}")
                print(f"   Original name: {media_file.get('original_name')}")
                print(f"   File size: {media_file.get('file_size', 0)} bytes")
                print(f"   Mime type: {media_file.get('mimeType')}")
                
                # Check if file exists on disk
                from app.core.config import settings
                file_path = Path(settings.UPLOAD_DIR) / media_file.get("filename")
                if file_path.exists():
                    print(f"✅ File exists on disk: {file_path}")
                else:
                    print(f"❌ File NOT found on disk: {file_path}")
                    print(f"   Upload directory: {settings.UPLOAD_DIR}")
                    print(f"   Files in directory: {list(Path(settings.UPLOAD_DIR).glob('*'))}")
            else:
                print(f"❌ Media file not found: {media_file_id}")
        
        # Check Redis
        print(f"\n🔴 Checking Redis...")
        try:
            redis_client = await get_redis()
            progress_data = await redis_client.get(f"progress:{job_id}")
            if progress_data:
                print(f"✅ Progress data found in Redis: {progress_data}")
            else:
                print(f"❌ No progress data in Redis")
        except Exception as e:
            print(f"⚠️ Redis not available: {e}")
        
        # Check transcription results
        print(f"\n📄 Checking transcription results...")
        results_collection = await get_collection("transcription_results")
        result = await results_collection.find_one({"jobId": job_id})
        if result:
            print(f"✅ Transcription result found")
            print(f"   Language: {result.get('language')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Text length: {len(result.get('full_text', ''))}")
        else:
            print(f"❌ No transcription results found")
        
        return job
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def manually_process_job(job_id: str):
    """Manually trigger job processing"""
    print(f"\n🔄 MANUALLY PROCESSING JOB: {job_id}")
    print("-" * 45)
    
    try:
        # Get job info
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({"jobId": job_id})
        
        if not job:
            print(f"❌ Cannot process - job not found")
            return False
        
        media_file_id = job.get("mediaFileId")
        user_id = job.get("userId")
        
        if not media_file_id or not user_id:
            print(f"❌ Cannot process - missing media_file_id or user_id")
            return False
        
        print(f"📋 Job info: media_file_id={media_file_id}, user_id={user_id}")
        
        # Create and run MediaProcessor
        processor = MediaProcessor()
        
        print(f"🚀 Starting manual transcription...")
        
        # Update status to processing
        await jobs_collection.update_one(
            {"jobId": job_id},
            {
                "$set": {
                    "processing.status": "processing",
                    "processing.progress": 10,
                    "processing.startedAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
            }
        )
        
        await set_progress(job_id, {
            "jobId": job_id,
            "status": "processing",
            "progress": 10,
            "stage": "manual_transcription"
        })
        
        # Run transcription
        await processor.process_transcription_job(job_id, media_file_id, user_id)
        
        print(f"✅ Manual processing completed!")
        
        # Check results
        results_collection = await get_collection("transcription_results")
        result = await results_collection.find_one({"jobId": job_id})
        
        if result:
            print(f"📄 Transcription result:")
            print(f"   Text: {result.get('full_text', 'No text')[:200]}...")
            print(f"   Language: {result.get('language', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            return True
        else:
            print(f"❌ No transcription result after processing")
            return False
            
    except Exception as e:
        print(f"❌ Manual processing error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main debug function"""
    if len(sys.argv) != 2:
        print("Usage: python debug_job_status.py <job_id>")
        print("Example: python debug_job_status.py 8cf33ea1-9c1e-43c7-82d0-cf3ad4edc1e5")
        return
    
    job_id = sys.argv[1]
    
    # Debug job
    job_info = await debug_job(job_id)
    
    if job_info and job_info.get("processing", {}).get("status") == "uploaded":
        print(f"\n💡 Job is still in 'uploaded' status")
        print(f"   This suggests background task processing may not be working")
        
        # Ask user if they want to manually process
        try:
            user_input = input("\n🤔 Do you want to manually process this job? (y/n): ")
            if user_input.lower() == 'y':
                success = await manually_process_job(job_id)
                if success:
                    print(f"\n🎉 Manual processing successful!")
                    print(f"   Check your frontend app for updated results")
                else:
                    print(f"\n❌ Manual processing failed")
        except KeyboardInterrupt:
            print(f"\n👋 User cancelled")
        except Exception as e:
            print(f"\n❌ Input error: {e}")

if __name__ == "__main__":
    asyncio.run(main())