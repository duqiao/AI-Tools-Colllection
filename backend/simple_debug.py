#!/usr/bin/env python3
"""
SIMPLE DEBUG SCRIPT
===================

Debug job 8cf33ea1-9c1e-43c7-82d0-cf3ad4edc1e5
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def debug_specific_job():
    """Debug the specific job"""
    job_id = "8cf33ea1-9c1e-43c7-82d0-cf3ad4edc1e5"
    
    print(f"🔍 DEBUGGING JOB: {job_id}")
    print("=" * 50)
    
    try:
        # Import required modules
        from app.core.database import get_collection
        from app.core.config import settings
        
        # Check job in database
        print("📋 Checking job in database...")
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({"jobId": job_id})
        
        if not job:
            print(f"❌ Job {job_id} not found in database")
            return False
        
        print(f"✅ Job found in database")
        print(f"   Job ID: {job.get('jobId')}")
        print(f"   Status: {job.get('processing', {}).get('status', 'unknown')}")
        print(f"   Progress: {job.get('processing', {}).get('progress', 0)}%")
        print(f"   Created: {job.get('createdAt')}")
        print(f"   User ID: {job.get('userId')}")
        print(f"   Media File ID: {job.get('mediaFileId')}")
        
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
                file_path = Path(settings.UPLOAD_DIR) / media_file.get("filename")
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"✅ File exists on disk: {file_path}")
                    print(f"   File size on disk: {file_size} bytes")
                else:
                    print(f"❌ File NOT found on disk: {file_path}")
                    print(f"   Upload directory: {settings.UPLOAD_DIR}")
                    
                    # List files in upload directory
                    if Path(settings.UPLOAD_DIR).exists():
                        files = list(Path(settings.UPLOAD_DIR).glob('*'))
                        print(f"   Files in directory ({len(files)}):")
                        for f in files[:5]:  # Show first 5 files
                            print(f"     - {f.name} ({f.stat().st_size} bytes)")
                        if len(files) > 5:
                            print(f"     ... and {len(files) - 5} more files")
                    else:
                        print(f"   Upload directory does not exist!")
            else:
                print(f"❌ Media file not found: {media_file_id}")
        
        # Check transcription results
        print(f"\n📄 Checking transcription results...")
        results_collection = await get_collection("transcription_results")
        result = await results_collection.find_one({"jobId": job_id})
        if result:
            print(f"✅ Transcription result found")
            print(f"   Language: {result.get('language')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Text length: {len(result.get('full_text', ''))}")
            print(f"   Text preview: {result.get('full_text', '')[:100]}...")
        else:
            print(f"❌ No transcription results found")
        
        # Check job settings
        job_settings = job.get("job", {})
        print(f"\n⚙️  Job settings:")
        print(f"   Provider: {job_settings.get('provider', 'unknown')}")
        print(f"   Model: {job_settings.get('model', 'unknown')}")
        print(f"   Language: {job_settings.get('settings', {}).get('language', 'auto')}")
        print(f"   Speaker Diarization: {job_settings.get('settings', {}).get('speakerDiarization', False)}")
        
        # Manual processing attempt
        print(f"\n🔄 Attempting to manually process job...")
        
        try:
            from app.services.media_processor import MediaProcessor
            processor = MediaProcessor()
            
            print(f"   Using STT service: {type(processor.stt_service).__name__}")
            
            # Test STT service
            print(f"   Testing STT service connection...")
            
            if hasattr(processor.stt_service, 'test_connection'):
                connection_ok = await processor.stt_service.test_connection()
                print(f"   STT connection: {'✅ OK' if connection_ok else '❌ Failed'}")
            
            # If file exists, try to process it
            if media_file and file_path and file_path.exists():
                print(f"   Processing file: {file_path}")
                
                # Update job status
                await jobs_collection.update_one(
                    {"jobId": job_id},
                    {
                        "$set": {
                            "processing.status": "processing",
                            "processing.progress": 25,
                            "processing.startedAt": asyncio.get_event_loop().time(),
                            "updatedAt": asyncio.get_event_loop().time()
                        }
                    }
                )
                
                # Try transcription
                transcription_options = {
                    "language": job_settings.get('settings', {}).get('language', 'auto'),
                    "enable_timestamps": job_settings.get('settings', {}).get('speakerDiarization', False),
                    "enable_speaker_diarization": job_settings.get('settings', {}).get('speakerDiarization', False)
                }
                
                print(f"   Starting transcription with options: {transcription_options}")
                
                result = await processor.stt_service.transcribe(
                    str(file_path),
                    transcription_options
                )
                
                print(f"✅ Transcription completed!")
                print(f"   Text length: {len(result.get('full_text', ''))}")
                print(f"   Language: {result.get('language', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                
                # Save results
                await results_collection.insert_one({
                    "jobId": job_id,
                    "userId": job.get("userId"),
                    "mediaFileId": media_file_id,
                    "full_text": result.get("full_text", ""),
                    "language": result.get("language", "unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "segments": result.get("segments", []),
                    "metadata": result.get("metadata", {}),
                    "createdAt": asyncio.get_event_loop().time(),
                    "processing_model": job_settings.get("model")
                })
                
                # Update job as completed
                await jobs_collection.update_one(
                    {"jobId": job_id},
                    {
                        "$set": {
                            "processing.status": "completed",
                            "processing.progress": 100,
                            "processing.completedAt": asyncio.get_event_loop().time(),
                            "updatedAt": asyncio.get_event_loop().time()
                        }
                    }
                )
                
                print(f"✅ Job processing completed successfully!")
                return True
                
            else:
                print(f"❌ Cannot process - file not available")
                return False
                
        except Exception as e:
            print(f"❌ Manual processing failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_specific_job())
    
    if success:
        print(f"\n🎉 JOB DEBUGGING AND PROCESSING COMPLETED!")
        print(f"✅ The job should now show as completed in your frontend app")
    else:
        print(f"\n❌ JOB DEBUGGING FAILED")
        print(f"Check the error messages above for more details")