import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import os
import json
import time

from app.core.config import settings
from app.core.database import get_collection
from app.core.redis import set_progress
from app.services.speech_to_text import get_speech_to_text_service
from app.services.translation import get_translation_service
from app.services.audio_processor import AudioProcessor
from app.models.schemas import JobStatus, ProcessingStage

logger = logging.getLogger(__name__)

class MediaProcessor:
    def __init__(self):
        self.stt_service = get_speech_to_text_service()
        self.translation_service = get_translation_service()
        self.audio_processor = AudioProcessor()
    
    async def process_transcription_job(self, job_id: str, media_file_id: str, user_id: str):
        """Process a transcription job (background task)"""
        logger.info(f"Starting transcription job: {job_id}", extra={
            "job_id": job_id,
            "media_file_id": media_file_id,
            "user_id": user_id
        })
        
        try:
            # Update job status to processing
            jobs_collection = await get_collection("processing_jobs")
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
            
            # Update Redis progress
            await set_progress(job_id, {
                "jobId": job_id,
                "status": "processing",
                "progress": 10,
                "stage": "starting_transcription"
            })
            
            # Get media file info
            media_collection = await get_collection("media_files")
            media_file = await media_collection.find_one({"_id": media_file_id})
            
            if not media_file:
                raise Exception(f"Media file {media_file_id} not found")
            
            # Get job details
            job = await jobs_collection.find_one({"jobId": job_id})
            if not job:
                raise Exception(f"Job {job_id} not found")
            
            # Get file path
            file_path = Path(settings.UPLOAD_DIR) / media_file["filename"]
            if not file_path.exists():
                raise Exception(f"File not found: {file_path}")
            
            # Update progress
            await set_progress(job_id, {
                "jobId": job_id,
                "status": "processing",
                "progress": 25,
                "stage": "transcribing"
            })
            
            # Prepare transcription options
            transcription_options = {
                "language": job["job"]["settings"]["language"],
                "enable_timestamps": job["job"]["settings"]["speakerDiarization"],
                "enable_speaker_diarization": job["job"]["settings"]["speakerDiarization"]
            }
            
            # Perform transcription
            logger.info(f"Starting transcription for {file_path}")
            transcription_result = await self.stt_service.transcribe(
                str(file_path),
                transcription_options
            )
            
            # Update progress
            await set_progress(job_id, {
                "jobId": job_id,
                "status": "processing",
                "progress": 80,
                "stage": "saving_results"
            })
            
            # Save transcription results
            results_collection = await get_collection("transcription_results")
            await results_collection.insert_one({
                "jobId": job_id,
                "userId": user_id,
                "mediaFileId": media_file_id,
                "full_text": transcription_result.get("full_text", ""),
                "language": transcription_result.get("language", "unknown"),
                "confidence": transcription_result.get("confidence", 0.0),
                "segments": transcription_result.get("segments", []),
                "metadata": transcription_result.get("metadata", {}),
                "createdAt": datetime.utcnow(),
                "processing_model": job["job"]["model"]
            })
            
            # Mark job as completed
            await jobs_collection.update_one(
                {"jobId": job_id},
                {
                    "$set": {
                        "processing.status": "completed",
                        "processing.progress": 100,
                        "processing.completedAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            # Final progress update
            await set_progress(job_id, {
                "jobId": job_id,
                "status": "completed",
                "progress": 100,
                "stage": "completed"
            })
            
            logger.info(f"Transcription job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Transcription job {job_id} failed: {e}", exc_info=True)
            
            # Mark job as failed
            try:
                jobs_collection = await get_collection("processing_jobs")
                await jobs_collection.update_one(
                    {"jobId": job_id},
                    {
                        "$set": {
                            "processing.status": "failed",
                            "processing.error": str(e),
                            "processing.progress": 0,
                            "updatedAt": datetime.utcnow()
                        }
                    }
                )
                
                # Update Redis progress with error
                await set_progress(job_id, {
                    "jobId": job_id,
                    "status": "failed",
                    "progress": 0,
                    "stage": "failed",
                    "error": str(e)
                })
                
            except Exception as update_error:
                logger.error(f"Failed to update job {job_id} as failed: {update_error}")
    
    async def process_translation(self, task_id: str, user_id: str):
        """Process translation for a media file"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Get job details
            jobs_collection = await get_collection("processing_jobs")
            job = await jobs_collection.find_one({"job_id": task_id})
            
            if not job:
                raise Exception(f"Job {task_id} not found")
            
            # Get media file details
            media_collection = await get_collection("media_files")
            media_file = await media_collection.find_one({"_id": job["media_file"]})
            
            if not media_file:
                raise Exception(f"Media file not found for job {task_id}")
            
            logger.info(f"Starting media processing for task: {task_id}", extra={
                "user_id": user_id,
                "file_name": media_file["original_name"],
                "file_type": media_file["file_type"]
            })
            
            # Step 1: Audio extraction (for video files)
            if media_file["file_type"] == "video":
                await self._update_progress(task_id, {
                    "progress": 20,
                    "stage": ProcessingStage.EXTRACTING_AUDIO,
                    "message": "Extracting audio from video..."
                })
                
                audio_path = await self.audio_processor.extract_audio(media_file["file_path"])
            else:
                audio_path = media_file["file_path"]
            
            # Step 2: Speech-to-text
            await self._update_progress(task_id, {
                "progress": 40,
                "stage": ProcessingStage.SPEECH_RECOGNITION,
                "message": "Converting speech to text..."
            })
            
            transcription_result = await self.stt_service.transcribe(
                audio_path,
                {
                    "language": job["source_language"] if job["source_language"] != "auto" else None,
                    "enable_timestamps": True,
                    "enable_speaker_diarization": True
                }
            )
            
            # Step 3: Translation
            await self._update_progress(task_id, {
                "progress": 70,
                "stage": ProcessingStage.TRANSLATING,
                "message": "Translating text..."
            })
            
            translation_result = await self.translation_service.translate(
                transcription_result["full_text"],
                transcription_result.get("language", "auto"),
                job["target_language"]
            )
            
            # Step 4: Finalize
            await self._update_progress(task_id, {
                "progress": 90,
                "stage": ProcessingStage.FINALIZING,
                "message": "Finalizing results..."
            })
            
            # Save results
            processing_time = int((asyncio.get_event_loop().time() - start_time) * 1000)  # milliseconds
            
            result_data = {
                "originalText": transcription_result["full_text"],
                "translatedText": translation_result["translated_text"],
                "confidence": min(
                    transcription_result.get("confidence", 0.8),
                    translation_result.get("confidence", 0.8)
                ),
                "language": transcription_result.get("language", "unknown"),
                "duration": transcription_result.get("metadata", {}).get("audio_duration"),
                "processedAt": asyncio.get_event_loop().time(),
                "metadata": {
                    "speakerCount": transcription_result.get("metadata", {}).get("speaker_count", 1),
                    "wordCount": transcription_result.get("metadata", {}).get("word_count", 0),
                    "segmentCount": len(transcription_result.get("segments", [])),
                    "sourceLanguage": translation_result.get("source_language"),
                    "targetLanguage": job["target_language"],
                    "processingTime": processing_time
                }
            }
            
            # Update job with results
            await jobs_collection.update_one(
                {"_id": job["_id"]},
                {
                    "$set": {
                        "status": JobStatus.COMPLETED,
                        "progress": 100,
                        "current_stage": ProcessingStage.COMPLETED,
                        "result": result_data,
                        "completed_at": asyncio.get_event_loop().time(),
                        "updated_at": asyncio.get_event_loop().time()
                    }
                }
            )
            
            # Update media file as processed
            await media_collection.update_one(
                {"_id": media_file["_id"]},
                {"$set": {"is_processed": True, "processing_job": job["_id"]}}
            )
            
            # Final progress update
            final_progress = {
                "task_id": task_id,
                "progress": 100,
                "stage": ProcessingStage.COMPLETED,
                "message": "Translation completed successfully",
                "result": {
                    "taskId": task_id,
                    "originalText": result_data["originalText"],
                    "translatedText": result_data["translatedText"],
                    "confidence": result_data["confidence"],
                    "language": result_data["language"],
                    "duration": result_data["duration"],
                    "processedAt": result_data["processedAt"],
                    "metadata": result_data["metadata"]
                }
            }
            
            await self._update_progress(task_id, final_progress)
            
            # Cleanup temporary files
            if media_file["file_type"] == "video" and audio_path != media_file["file_path"]:
                try:
                    os.unlink(audio_path)
                    logger.info(f"Temporary audio file cleaned up: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
            
            logger.info(f"Translation completed successfully: {task_id}", extra={
                "user_id": user_id,
                "processing_time": processing_time,
                "original_text_length": len(result_data["originalText"]),
                "translated_text_length": len(result_data["translatedText"])
            })
            
        except Exception as e:
            logger.error(f"Translation processing failed for task {task_id}: {e}", exc_info=True)
            
            # Update job with error
            error_data = {
                "code": "PROCESSING_ERROR",
                "message": str(e),
                "details": str(e)
            }
            
            await jobs_collection.update_one(
                {"job_id": task_id},
                {
                    "$set": {
                        "status": JobStatus.FAILED,
                        "error": error_data,
                        "completed_at": asyncio.get_event_loop().time(),
                        "updated_at": asyncio.get_event_loop().time()
                    }
                }
            )
            
            # Update Redis progress with error
            error_progress = {
                "task_id": task_id,
                "progress": 0,
                "stage": "processing_failed",
                "error": str(e)
            }
            
            await self._update_progress(task_id, error_progress)
            
            raise
    
    async def _update_progress(self, task_id: str, progress_data: Dict[str, Any]):
        """Update progress in Redis and database"""
        try:
            # Update Redis for real-time tracking
            await set_progress(task_id, progress_data)
            
            # Update database periodically (not for every small change)
            if progress_data.get("progress", 0) % 20 == 0:
                jobs_collection = await get_collection("processing_jobs")
                update_fields = {
                    "progress": progress_data["progress"],
                    "current_stage": progress_data["stage"],
                    "updated_at": asyncio.get_event_loop().time()
                }
                
                await jobs_collection.update_one(
                    {"job_id": task_id},
                    {"$set": update_fields}
                )
                
        except Exception as e:
            logger.error(f"Failed to update progress for task {task_id}: {e}")
    
    def get_supported_formats(self) -> Dict[str, list]:
        """Get supported file formats"""
        return {
            "audio": settings.ALLOWED_AUDIO_TYPES,
            "video": settings.ALLOWED_VIDEO_TYPES
        }
    
    def is_supported_format(self, mime_type: str) -> bool:
        """Check if file format is supported"""
        return mime_type in settings.ALLOWED_AUDIO_TYPES + settings.ALLOWED_VIDEO_TYPES