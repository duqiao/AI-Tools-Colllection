#!/usr/bin/env python3
"""
DEBUG SPECIFIC JOB
==================

Debug and manually process job 3aa31365-fe47-4453-a5c5-a7cd005f78e8
"""

import asyncio
import sys
import os
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def debug_job():
    """Debug specific job"""
    job_id = "3aa31365-fe47-4453-a5c5-a7cd005f78e8"
    
    print(f"DEBUGGING JOB: {job_id}")
    print("=" * 50)
    
    try:
        # Import dependencies
        from app.core.database import init_db, get_collection
        from app.core.config import settings
        from app.services.media_processor import MediaProcessor
        
        # Initialize database
        print("Initializing database...")
        await init_db()
        print("Database initialized successfully")
        
        # Check job in database
        print("Checking job in database...")
        jobs_collection = await get_collection("processing_jobs")
        job = await jobs_collection.find_one({"jobId": job_id})
        
        if not job:
            print(f"Job {job_id} not found in database")
            return False
        
        print(f"Job found in database")
        print(f"   Job ID: {job.get('jobId')}")
        print(f"   Status: {job.get('processing', {}).get('status', 'unknown')}")
        print(f"   Progress: {job.get('processing', {}).get('progress', 0)}%")
        print(f"   Created: {job.get('createdAt')}")
        print(f"   User ID: {job.get('userId')}")
        print(f"   Media File ID: {job.get('mediaFileId')}")
        
        # Check media file
        media_file_id = job.get("mediaFileId")
        if not media_file_id:
            print(f"No mediaFileId in job")
            return False
            
        print(f"\nChecking media file...")
        media_collection = await get_collection("media_files")
        media_file = await media_collection.find_one({"_id": media_file_id})
        
        if not media_file:
            print(f"Media file not found: {media_file_id}")
            return False
        
        print(f"Media file found")
        print(f"   Available fields: {list(media_file.keys())}")
        print(f"   Filename (fileName): {media_file.get('fileName')}")
        print(f"   Original name (originalName): {media_file.get('originalName')}")
        print(f"   File size (fileSize): {media_file.get('fileSize', 0)} bytes")
        print(f"   Mime type (mimeType): {media_file.get('mimeType')}")
        
        # Check if file exists on disk - use correct field name
        filename = media_file.get("fileName")
        if not filename:
            print(f"No filename found in media file record")
            return False
            
        file_path = Path(settings.UPLOAD_DIR) / filename
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"File exists on disk: {file_path}")
            print(f"   File size on disk: {file_size} bytes")
        else:
            print(f"File NOT found on disk: {file_path}")
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
                # Try to create it
                try:
                    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
                    print(f"   Created upload directory: {settings.UPLOAD_DIR}")
                except Exception as e:
                    print(f"   Failed to create directory: {e}")
        
        # Check job settings
        job_settings = job.get("job", {})
        print(f"\nJob settings:")
        print(f"   Provider: {job_settings.get('provider', 'unknown')}")
        print(f"   Model: {job_settings.get('model', 'unknown')}")
        print(f"   Language: {job_settings.get('settings', {}).get('language', 'auto')}")
        print(f"   Speaker Diarization: {job_settings.get('settings', {}).get('speakerDiarization', False)}")
        
        # Check if job is still in uploaded status
        current_status = job.get("processing", {}).get("status")
        if current_status == "uploaded":
            print(f"\nJob is in 'uploaded' status - processing needs to start")
            
            # Update job status to indicate processing is starting
            await jobs_collection.update_one(
                {"jobId": job_id},
                {
                    "$set": {
                        "processing.status": "processing_started",
                        "processing.progress": 5,
                        "updatedAt": asyncio.get_event_loop().time()
                    }
                }
            )
            print(f"Updated job status to 'processing_started'")
            
            # Now manually process the job
            print(f"\nStarting manual transcription...")
            
            processor = MediaProcessor()
            
            print(f"   Using STT service: {type(processor.stt_service).__name__}")
            
            # Test STT service connection
            if hasattr(processor.stt_service, 'test_connection'):
                print(f"Testing STT service connection...")
                try:
                    connection_ok = await processor.stt_service.test_connection()
                    print(f"   STT Connection: {'OK' if connection_ok else 'Failed'}")
                    
                    if not connection_ok:
                        print(f"   STT service connection failed - this is likely the problem")
                        return False
                except Exception as e:
                    print(f"   STT connection test error: {e}")
                    return False
            
            # Update progress
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
            if not file_path.exists():
                print(f"Cannot process - file not found: {file_path}")
                return False
                
            transcription_options = {
                "language": job_settings.get('settings', {}).get('language', 'auto'),
                "enable_timestamps": job_settings.get('settings', {}).get('speakerDiarization', False),
                "enable_speaker_diarization": job_settings.get('settings', {}).get('speakerDiarization', False)
            }
            
            print(f"   Starting transcription with options: {transcription_options}")
            print(f"   File: {file_path}")
            
            try:
                result = await processor.stt_service.transcribe(
                    str(file_path),
                    transcription_options
                )
                
                print(f"Transcription completed!")
                print(f"   Text length: {len(result.get('full_text', ''))}")
                print(f"   Language: {result.get('language', 'unknown')}")
                print(f"   Confidence: {result.get('confidence', 0):.2f}")
                print(f"   Text preview: {result.get('full_text', '')[:200]}...")
                
                # Save results
                results_collection = await get_collection("transcription_results")
                await results_collection.insert_one({
                    "jobId": job_id,
                    "userId": job.get("userId"),
                    "mediaFile_id": media_file_id,
                    "full_text": result.get("full_text", ""),
                    "language": result.get("language", "unknown"),
                    "confidence": result.get("confidence", 0.0),
                    "segments": result.get("segments", []),
                    "metadata": result.get("metadata", {}),
                    "createdAt": asyncio.get_event_loop().time(),
                    "processing_model": job_settings.get("model")
                })
                
                # Mark job as completed
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
                
                print(f"Job processing completed successfully!")
                return True
                
            except Exception as e:
                print(f"Transcription failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Mark job as failed
                await jobs_collection.update_one(
                    {"jobId": job_id},
                    {
                        "$set": {
                            "processing.status": "failed",
                            "processing.error": str(e),
                            "processing.progress": 0,
                            "updatedAt": asyncio.get_event_loop().time()
                        }
                    }
                )
                
                return False
        else:
            print(f"\nJob status is: {current_status}")
            print(f"   Job may have already been processed or failed")
            
            # Check for existing results
            results_collection = await get_collection("transcription_results")
            result = await results_collection.find_one({"jobId": job_id})
            
            if result:
                print(f"Found existing transcription result")
                print(f"   Text length: {len(result.get('full_text', ''))}")
                print(f"   Language: {result.get('language', 'unknown')}")
                print(f"   Text preview: {result.get('full_text', '')[:100]}...")
                return True
            else:
                print(f"No existing results found")
                return False
        
    except Exception as e:
        print(f"Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main debug function"""
    print("JOB DEBUG AND PROCESSING")
    print("=" * 35)
    
    success = await debug_job()
    
    if success:
        print(f"\nJOB PROCESSING COMPLETED!")
        print(f"Job should now show as completed in frontend")
        print(f"Frontend should display transcription results")
    else:
        print(f"\nJOB PROCESSING FAILED")
        print(f"Check the error messages above for details")

if __name__ == "__main__":
    success = asyncio.run(main())