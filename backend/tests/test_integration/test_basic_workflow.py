"""
Basic Workflow Integration Tests

This test module verifies the complete basic workflow of user registration,
file upload, and job processing using PostgreSQL repositories.
These tests should FAIL before the repository implementations are complete.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from app.repositories.user_repository import UserRepository
    from app.repositories.media_repository import MediaRepository
    from app.repositories.job_repository import ProcessingJobRepository
    from app.core.postgres_db import Database
    from app.utils.postgres_errors import PostgresError, PostgresErrorType
except ImportError as e:
    pytest.skip(f"Repository modules not available: {e}", allow_module_level=True)


class TestBasicWorkflow:
    """Test complete basic workflow integration"""
    
    @pytest.fixture
    async def repositories(self):
        """Fixture to provide all repository instances"""
        try:
            await Database.init_db()
            
            user_repo = UserRepository()
            media_repo = MediaRepository()
            job_repo = ProcessingJobRepository()
            
            yield {
                "user_repo": user_repo,
                "media_repo": media_repo,
                "job_repo": job_repo
            }
            
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup repositories: {e}")
    
    @pytest.mark.asyncio
    async def test_complete_user_registration_and_file_upload_workflow(self, repositories: Dict[str, Any]):
        """Test complete workflow: user registration → file upload → job creation"""
        try:
            user_repo = repositories["user_repo"]
            media_repo = repositories["media_repo"]
            job_repo = repositories["job_repo"]
            
            # Step 1: User Registration
            user_data = {
                "username": "workflow_test_user",
                "email": "workflow@example.com",
                "password_hash": "hashed_password_123",
                "subscription_level": "free",
                "profile": {
                    "first_name": "Workflow",
                    "last_name": "Test",
                    "preferences": {
                        "language": "en",
                        "notifications": True
                    }
                }
            }
            
            user_id = await user_repo.create(user_data)
            assert user_id is not None
            
            # Verify user was created
            created_user = await user_repo.get_by_id(user_id)
            assert created_user is not None
            assert created_user["username"] == "workflow_test_user"
            
            # Step 2: File Upload Simulation
            media_data = {
                "user_id": user_id,
                "file_name": "workflow_test_audio.mp3",
                "original_file_name": "meeting_recording.mp3",
                "file_path": "/uploads/workflow_test_audio.mp3",
                "file_size": 2048576,  # 2MB
                "mime_type": "audio/mpeg",
                "file_type": "audio",
                "duration_seconds": 180.5,
                "sample_rate": 44100,
                "channels": 2,
                "bitrate": 128000,
                "format": "mp3",
                "metadata": {
                    "title": "Team Meeting Recording",
                    "description": "Weekly team sync meeting",
                    "tags": ["meeting", "team", "weekly"],
                    "recorded_at": "2024-01-15T10:00:00Z"
                },
                "processing_info": {
                    "status": "uploaded",
                    "uploaded_at": datetime.utcnow().isoformat(),
                    "checksum": "workflow_checksum_123"
                }
            }
            
            media_id = await media_repo.create(media_data)
            assert media_id is not None
            
            # Verify media file was created
            created_media = await media_repo.get_by_id(media_id)
            assert created_media is not None
            assert created_media["file_name"] == "workflow_test_audio.mp3"
            assert created_media["user_id"] == user_id
            
            # Step 3: Job Creation
            job_data = {
                "user_id": user_id,
                "media_file_id": media_id,
                "job_id": f"job_workflow_{uuid.uuid4().hex[:8]}",
                "job_type": "transcription",
                "status": "pending",
                "priority": "normal",
                "config": {
                    "language": "en",
                    "model": "whisper-base",
                    "enable_timestamps": True,
                    "enable_diarization": False
                },
                "result": None,
                "error": None,
                "started_at": None,
                "completed_at": None,
                "progress": {
                    "percentage": 0,
                    "current_stage": "queued",
                    "estimated_time_remaining": None
                }
            }
            
            processing_job_id = await job_repo.create(job_data)
            assert processing_job_id is not None
            
            # Verify job was created
            created_job = await job_repo.get_by_id(processing_job_id)
            assert created_job is not None
            assert created_job["job_id"].startswith("job_workflow_")
            assert created_job["user_id"] == user_id
            assert created_job["media_file_id"] == media_id
            assert created_job["status"] == "pending"
            
            # Step 4: Verify Relationships
            # Verify user has media files
            user_media = await media_repo.get_by_user_id(user_id)
            assert len(user_media) >= 1
            assert user_media[0]["id"] == media_id
            
            # Verify user has jobs
            user_jobs = await job_repo.get_by_user_id(user_id)
            assert len(user_jobs) >= 1
            assert user_jobs[0]["id"] == processing_job_id
            
            # Verify media file has associated jobs
            media_jobs = await job_repo.get_by_media_file_id(media_id)
            assert len(media_jobs) >= 1
            assert media_jobs[0]["id"] == processing_job_id
            
            # Step 5: Test Job Status Updates
            # Update job to processing
            update_data = {
                "status": "processing",
                "started_at": datetime.utcnow(),
                "progress": {
                    "percentage": 25,
                    "current_stage": "transcribing",
                    "estimated_time_remaining": 120
                }
            }
            
            success = await job_repo.update(processing_job_id, update_data)
            assert success is True
            
            updated_job = await job_repo.get_by_id(processing_job_id)
            assert updated_job["status"] == "processing"
            assert updated_job["progress"]["percentage"] == 25
            
            # Step 6: Complete the Job
            completion_data = {
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "progress": {
                    "percentage": 100,
                    "current_stage": "completed",
                    "estimated_time_remaining": None
                },
                "result": {
                    "transcription": "This is the transcribed text from the meeting...",
                    "confidence": 0.95,
                    "language_detected": "en",
                    "duration_processed": 180.5,
                    "word_count": 250
                }
            }
            
            success = await job_repo.update(processing_job_id, completion_data)
            assert success is True
            
            completed_job = await job_repo.get_by_id(processing_job_id)
            assert completed_job["status"] == "completed"
            assert completed_job["result"]["transcription"] is not None
            assert completed_job["result"]["confidence"] == 0.95
            
            # Step 7: Update User Usage Stats
            usage_update = {
                "total_files_processed": 1,
                "total_audio_duration": 180.5,
                "api_calls_count": 1
            }
            
            success = await user_repo.update_usage_stats(user_id, usage_update)
            assert success is True
            
            final_user = await user_repo.get_by_id(user_id)
            assert final_user["usage_stats"]["total_files_processed"] == 1
            assert final_user["usage_stats"]["total_audio_duration"] == 180.5
            
        except Exception as e:
            pytest.fail(f"Complete workflow test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_multiple_users_and_files_workflow(self, repositories: Dict[str, Any]):
        """Test workflow with multiple users and files"""
        try:
            user_repo = repositories["user_repo"]
            media_repo = repositories["media_repo"]
            job_repo = repositories["job_repo"]
            
            # Create multiple users
            user_ids = []
            for i in range(3):
                user_data = {
                    "username": f"multi_user_{i}",
                    "email": f"multi_user_{i}@example.com",
                    "password_hash": "hashed_password",
                    "subscription_level": "free"
                }
                user_id = await user_repo.create(user_data)
                user_ids.append(user_id)
            
            # Create multiple media files for each user
            media_ids = []
            for user_idx, user_id in enumerate(user_ids):
                for file_idx in range(2):  # 2 files per user
                    media_data = {
                        "user_id": user_id,
                        "file_name": f"multi_user_{user_idx}_file_{file_idx}.mp3",
                        "original_file_name": f"original_{file_idx}.mp3",
                        "file_path": f"/uploads/multi_user_{user_idx}_file_{file_idx}.mp3",
                        "file_size": 1024000 * (file_idx + 1),
                        "mime_type": "audio/mpeg",
                        "file_type": "audio",
                        "duration_seconds": 60.0 * (file_idx + 1),
                        "metadata": {
                            "title": f"File {file_idx} for User {user_idx}",
                            "tags": [f"user_{user_idx}", f"file_{file_idx}"]
                        }
                    }
                    media_id = await media_repo.create(media_data)
                    media_ids.append(media_id)
            
            # Create jobs for each media file
            job_ids = []
            for media_idx, media_id in enumerate(media_ids):
                job_data = {
                    "user_id": user_ids[media_idx // 2],  # Each user gets 2 files
                    "media_file_id": media_id,
                    "job_id": f"multi_job_{media_idx}",
                    "job_type": "transcription",
                    "status": "pending"
                }
                job_id = await job_repo.create(job_data)
                job_ids.append(job_id)
            
            # Verify counts
            total_users = await user_repo.count()
            total_media = await media_repo.count()
            total_jobs = await job_repo.count()
            
            assert total_users >= 3
            assert total_media >= 6
            assert total_jobs >= 6
            
            # Verify each user has correct number of files and jobs
            for i, user_id in enumerate(user_ids):
                user_media = await media_repo.get_by_user_id(user_id)
                user_jobs = await job_repo.get_by_user_id(user_id)
                
                assert len(user_media) == 2
                assert len(user_jobs) == 2
            
        except Exception as e:
            pytest.fail(f"Multiple users workflow test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling_and_rollback_workflow(self, repositories: Dict[str, Any]):
        """Test error handling and rollback scenarios"""
        try:
            user_repo = repositories["user_repo"]
            media_repo = repositories["media_repo"]
            job_repo = repositories["job_repo"]
            
            # Create user successfully
            user_data = {
                "username": "error_test_user",
                "email": "error@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "free"
            }
            
            user_id = await user_repo.create(user_data)
            assert user_id is not None
            
            # Create media file successfully
            media_data = {
                "user_id": user_id,
                "file_name": "error_test.mp3",
                "original_file_name": "error_test.mp3",
                "file_path": "/uploads/error_test.mp3",
                "file_size": 1024,
                "mime_type": "audio/mpeg",
                "file_type": "audio"
            }
            
            media_id = await media_repo.create(media_data)
            assert media_id is not None
            
            # Try to create job with invalid data (should fail)
            invalid_job_data = {
                "user_id": user_id,
                "media_file_id": media_id,
                "job_id": f"error_job_{uuid.uuid4().hex[:8]}",
                "job_type": "invalid_type",  # This should cause validation error
                "status": "pending"
            }
            
            try:
                await job_repo.create(invalid_job_data)
                # If we get here, the job creation succeeded (unexpected)
                pytest.fail("Expected job creation to fail with invalid job type")
            except PostgresError as e:
                # This is expected - job creation should fail
                assert e.error_type in [PostgresErrorType.CONSTRAINT_VIOLATION, PostgresErrorType.DATA_TYPE_MISMATCH]
            
            # Verify user and media still exist (no rollback needed for this test)
            existing_user = await user_repo.get_by_id(user_id)
            assert existing_user is not None
            
            existing_media = await media_repo.get_by_id(media_id)
            assert existing_media is not None
            
            # Try to create media file with invalid user ID (should fail)
            invalid_media_data = {
                "user_id": str(uuid.uuid4()),  # Non-existent user ID
                "file_name": "invalid_user_test.mp3",
                "original_file_name": "invalid_user_test.mp3",
                "file_path": "/uploads/invalid_user_test.mp3",
                "file_size": 1024,
                "mime_type": "audio/mpeg",
                "file_type": "audio"
            }
            
            try:
                await media_repo.create(invalid_media_data)
                pytest.fail("Expected media creation to fail with invalid user ID")
            except PostgresError as e:
                assert e.error_type == PostgresErrorType.FOREIGN_KEY_VIOLATION
            
        except Exception as e:
            pytest.fail(f"Error handling workflow test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_repositories(self, repositories: Dict[str, Any]):
        """Test data consistency across different repositories"""
        try:
            user_repo = repositories["user_repo"]
            media_repo = repositories["media_repo"]
            job_repo = repositories["job_repo"]
            
            # Create user
            user_data = {
                "username": "consistency_test_user",
                "email": "consistency@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "premium"
            }
            
            user_id = await user_repo.create(user_data)
            
            # Create media file
            media_data = {
                "user_id": user_id,
                "file_name": "consistency_test.mp3",
                "original_file_name": "consistency_test.mp3",
                "file_path": "/uploads/consistency_test.mp3",
                "file_size": 512000,
                "mime_type": "audio/mpeg",
                "file_type": "audio",
                "duration_seconds": 120.0
            }
            
            media_id = await media_repo.create(media_data)
            
            # Create job
            job_data = {
                "user_id": user_id,
                "media_file_id": media_id,
                "job_id": f"consistency_job_{uuid.uuid4().hex[:8]}",
                "job_type": "transcription",
                "status": "completed",
                "result": {
                    "transcription": "Test transcription content",
                    "confidence": 0.98
                }
            }
            
            job_id = await job_repo.create(job_data)
            
            # Test consistency: All repositories should show consistent data
            # User through user repository
            user_from_user_repo = await user_repo.get_by_id(user_id)
            
            # User through media repository (indirectly)
            user_media = await media_repo.get_by_user_id(user_id)
            
            # User through job repository (indirectly)
            user_jobs = await job_repo.get_by_user_id(user_id)
            
            # Consistency checks
            assert user_from_user_repo["id"] == user_id
            assert all(media["user_id"] == user_id for media in user_media)
            assert all(job["user_id"] == user_id for job in user_jobs)
            
            # Check that counts are consistent
            user_media_count = await media_repo.count_by_user(user_id)
            user_job_count = await job_repo.count_by_user(user_id)
            
            assert len(user_media) == user_media_count
            assert len(user_jobs) == user_job_count
            
            # Verify UUID consistency
            assert str(uuid.UUID(user_id)) == user_id  # Valid UUID format
            assert str(uuid.UUID(media_id)) == media_id
            assert str(uuid.UUID(job_id)) == job_id
            
            # Verify JSONB data integrity
            assert isinstance(user_from_user_repo["usage_stats"], dict)
            assert isinstance(user_media[0]["metadata"], dict)
            assert isinstance(user_jobs[0]["result"], dict)
            
        except Exception as e:
            pytest.fail(f"Data consistency test failed: {e}")


class TestRepositoryPerformanceAndScalability:
    """Test repository performance and basic scalability"""
    
    @pytest.fixture
    async def repositories(self):
        """Fixture to provide repository instances"""
        try:
            await Database.init_db()
            
            user_repo = UserRepository()
            media_repo = MediaRepository()
            job_repo = ProcessingJobRepository()
            
            yield {
                "user_repo": user_repo,
                "media_repo": media_repo,
                "job_repo": job_repo
            }
            
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup repositories: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repositories: Dict[str, Any]):
        """Test basic concurrent operations"""
        try:
            user_repo = repositories["user_repo"]
            
            # Create multiple users concurrently
            async def create_user(index):
                user_data = {
                    "username": f"concurrent_user_{index}",
                    "email": f"concurrent_{index}@example.com",
                    "password_hash": "hashed_password",
                    "subscription_level": "free"
                }
                return await user_repo.create(user_data)
            
            # Create 10 users concurrently
            tasks = [create_user(i) for i in range(10)]
            user_ids = await asyncio.gather(*tasks)
            
            # Verify all users were created successfully
            assert len(user_ids) == 10
            assert all(user_id is not None for user_id in user_ids)
            
            # Verify no duplicate usernames
            users = await user_repo.list_all(limit=20)
            usernames = [user["username"] for user in users]
            concurrent_usernames = [name for name in usernames if name.startswith("concurrent_user_")]
            assert len(concurrent_usernames) == 10
            assert len(set(concurrent_usernames)) == 10  # All unique
            
        except Exception as e:
            pytest.fail(f"Concurrent operations test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self, repositories: Dict[str, Any]):
        """Test pagination performance with larger datasets"""
        try:
            user_repo = repositories["user_repo"]
            
            # Create 50 users
            user_ids = []
            for i in range(50):
                user_data = {
                    "username": f"pagination_user_{i:03d}",
                    "email": f"pagination_{i}@example.com",
                    "password_hash": "hashed_password",
                    "subscription_level": "free"
                }
                user_id = await user_repo.create(user_data)
                user_ids.append(user_id)
            
            # Test different pagination scenarios
            # First page
            page1 = await user_repo.list_all(limit=10, offset=0)
            assert len(page1) == 10
            
            # Middle page
            page5 = await user_repo.list_all(limit=10, offset=40)
            assert len(page5) == 10
            
            # Last page (partial)
            page6 = await user_repo.list_all(limit=10, offset=50)
            assert len(page6) <= 10  # May be less if exact multiple
            
            # Verify no duplicates across pages
            all_usernames = []
            for offset in range(0, 60, 10):
                page = await user_repo.list_all(limit=10, offset=offset)
                page_usernames = [user["username"] for user in page]
                all_usernames.extend(page_usernames)
            
            # Should have no duplicates
            assert len(all_usernames) == len(set(all_usernames))
            
        except Exception as e:
            pytest.fail(f"Pagination performance test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])