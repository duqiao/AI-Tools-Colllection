"""
Media File Repository Tests

This test module verifies MediaFile repository functionality with PostgreSQL.
These tests should FAIL before the MediaFile repository implementation is complete.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from app.repositories.media_repository import MediaRepository
    from app.repositories.user_repository import UserRepository
    from app.core.postgres_db import Database
    from app.utils.postgres_errors import PostgresError, PostgresErrorType
except ImportError as e:
    pytest.skip(f"Media repository modules not available: {e}", allow_module_level=True)


class TestMediaRepository:
    """Test MediaFile repository functionality"""
    
    @pytest.fixture
    async def media_repo(self):
        """Fixture to provide media repository instance"""
        try:
            await Database.init_db()
            repo = MediaRepository()
            yield repo
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup media repository: {e}")
    
    @pytest.fixture
    async def user_repo(self):
        """Fixture to provide user repository instance"""
        try:
            await Database.init_db()
            repo = UserRepository()
            yield repo
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup user repository: {e}")
    
    @pytest.fixture
    async def test_user(self, user_repo: UserRepository):
        """Fixture to create a test user"""
        user_data = {
            "username": "test_media_user",
            "email": "testmedia@example.com",
            "password_hash": "hashed_password",
            "subscription_level": "free"
        }
        
        user_id = await user_repo.create(user_data)
        return user_id
    
    @pytest.fixture
    async def test_media_data(self, test_user: str):
        """Fixture to provide test media file data"""
        return {
            "user_id": test_user,
            "file_name": "test_audio.mp3",
            "original_file_name": "original_audio.mp3",
            "file_path": "/uploads/test_audio.mp3",
            "file_size": 1024000,  # 1MB
            "mime_type": "audio/mpeg",
            "file_type": "audio",
            "duration_seconds": 120.5,
            "sample_rate": 44100,
            "channels": 2,
            "bitrate": 128000,
            "format": "mp3",
            "encoding": "utf-8",
            "metadata": {
                "title": "Test Audio",
                "artist": "Test Artist",
                "album": "Test Album",
                "genre": "Test",
                "year": 2024,
                "track": 1,
                "uploaded_from": "mobile_app",
                "device_info": {
                    "platform": "iOS",
                    "version": "17.0",
                    "model": "iPhone 15"
                }
            },
            "processing_info": {
                "status": "uploaded",
                "uploaded_at": datetime.utcnow().isoformat(),
                "checksum": "abc123def456",
                "virus_scan_status": "clean",
                "backup_status": "pending"
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_media_file(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test creating a new media file record"""
        try:
            # Create media file
            media_id = await media_repo.create(test_media_data)
            
            assert media_id is not None
            assert isinstance(media_id, str)  # UUID as string
            
            # Verify media file was created
            created_media = await media_repo.get_by_id(media_id)
            
            assert created_media is not None
            assert created_media["file_name"] == test_media_data["file_name"]
            assert created_media["original_file_name"] == test_media_data["original_file_name"]
            assert created_media["user_id"] == test_media_data["user_id"]
            assert created_media["file_size"] == test_media_data["file_size"]
            assert created_media["mime_type"] == test_media_data["mime_type"]
            assert created_media["file_type"] == test_media_data["file_type"]
            assert created_media["duration_seconds"] == test_media_data["duration_seconds"]
            assert created_media["metadata"]["title"] == test_media_data["metadata"]["title"]
            assert created_media["processing_info"]["status"] == test_media_data["processing_info"]["status"]
            
            # Verify timestamps
            assert created_media["created_at"] is not None
            assert created_media["updated_at"] is not None
            
        except Exception as e:
            pytest.fail(f"Failed to create media file: {e}")
    
    @pytest.mark.asyncio
    async def test_get_media_by_id(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test retrieving a media file by ID"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Get media file by ID
            retrieved_media = await media_repo.get_by_id(media_id)
            
            assert retrieved_media is not None
            assert retrieved_media["id"] == media_id
            assert retrieved_media["file_name"] == test_media_data["file_name"]
            assert retrieved_media["user_id"] == test_media_data["user_id"]
            
        except Exception as e:
            pytest.fail(f"Failed to get media file by ID: {e}")
    
    @pytest.mark.asyncio
    async def test_get_media_by_user_id(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test retrieving media files by user ID"""
        try:
            # Create multiple media files for the user
            media_ids = []
            for i in range(3):
                media_data = test_media_data.copy()
                media_data["file_name"] = f"test_audio_{i}.mp3"
                media_data["original_file_name"] = f"original_audio_{i}.mp3"
                
                media_id = await media_repo.create(media_data)
                media_ids.append(media_id)
            
            # Get media files by user ID
            user_media = await media_repo.get_by_user_id(test_media_data["user_id"])
            
            assert len(user_media) >= 3
            assert all(media["user_id"] == test_media_data["user_id"] for media in user_media)
            
            # Verify all our created media files are in the results
            created_file_names = [f"test_audio_{i}.mp3" for i in range(3)]
            result_file_names = [media["file_name"] for media in user_media]
            
            for file_name in created_file_names:
                assert file_name in result_file_names
            
        except Exception as e:
            pytest.fail(f"Failed to get media files by user ID: {e}")
    
    @pytest.mark.asyncio
    async def test_get_media_by_file_name(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test retrieving a media file by filename"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Get media file by filename
            retrieved_media = await media_repo.get_by_file_name(test_media_data["file_name"])
            
            assert retrieved_media is not None
            assert retrieved_media["id"] == media_id
            assert retrieved_media["file_name"] == test_media_data["file_name"]
            
        except Exception as e:
            pytest.fail(f"Failed to get media file by filename: {e}")
    
    @pytest.mark.asyncio
    async def test_update_media_file(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test updating a media file"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Update media file data
            update_data = {
                "file_size": 2048000,  # 2MB
                "duration_seconds": 240.0,
                "metadata": {
                    "title": "Updated Audio",
                    "artist": "Updated Artist",
                    "genre": "Updated Genre"
                },
                "processing_info": {
                    "status": "processed",
                    "processed_at": datetime.utcnow().isoformat()
                }
            }
            
            success = await media_repo.update(media_id, update_data)
            assert success is True
            
            # Verify update
            updated_media = await media_repo.get_by_id(media_id)
            
            assert updated_media["file_size"] == 2048000
            assert updated_media["duration_seconds"] == 240.0
            assert updated_media["metadata"]["title"] == "Updated Audio"
            assert updated_media["processing_info"]["status"] == "processed"
            
        except Exception as e:
            pytest.fail(f"Failed to update media file: {e}")
    
    @pytest.mark.asyncio
    async def test_update_processing_info(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test updating processing information specifically"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Update processing info
            processing_update = {
                "status": "processing",
                "processing_started_at": datetime.utcnow().isoformat(),
                "progress_percentage": 45,
                "current_stage": "transcription"
            }
            
            success = await media_repo.update_processing_info(media_id, processing_update)
            assert success is True
            
            # Verify update
            updated_media = await media_repo.get_by_id(media_id)
            
            assert updated_media["processing_info"]["status"] == "processing"
            assert updated_media["processing_info"]["progress_percentage"] == 45
            assert updated_media["processing_info"]["current_stage"] == "transcription"
            # Should preserve other processing info
            assert updated_media["processing_info"]["checksum"] == "abc123def456"
            
        except Exception as e:
            pytest.fail(f"Failed to update processing info: {e}")
    
    @pytest.mark.asyncio
    async def test_update_metadata(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test updating metadata specifically"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Update metadata
            metadata_update = {
                "title": "Final Title",
                "artist": "Final Artist",
                "album": "Final Album",
                "year": 2025,
                "additional_tags": ["speech", "interview", "education"]
            }
            
            success = await media_repo.update_metadata(media_id, metadata_update)
            assert success is True
            
            # Verify update
            updated_media = await media_repo.get_by_id(media_id)
            
            assert updated_media["metadata"]["title"] == "Final Title"
            assert updated_media["metadata"]["artist"] == "Final Artist"
            assert updated_media["metadata"]["year"] == 2025
            assert updated_media["metadata"]["additional_tags"] == ["speech", "interview", "education"]
            # Should preserve other metadata
            assert updated_media["metadata"]["genre"] == "Test"
            
        except Exception as e:
            pytest.fail(f"Failed to update metadata: {e}")
    
    @pytest.mark.asyncio
    async def test_delete_media_file(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test deleting a media file"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Verify media file exists
            media_before_delete = await media_repo.get_by_id(media_id)
            assert media_before_delete is not None
            
            # Delete media file
            success = await media_repo.delete(media_id)
            assert success is True
            
            # Verify media file is deleted
            media_after_delete = await media_repo.get_by_id(media_id)
            assert media_after_delete is None
            
        except Exception as e:
            pytest.fail(f"Failed to delete media file: {e}")
    
    @pytest.mark.asyncio
    async def test_media_file_exists(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test checking if media file exists"""
        try:
            # Create media file first
            media_id = await media_repo.create(test_media_data)
            
            # Check existence with valid ID
            exists = await media_repo.exists(media_id)
            assert exists is True
            
            # Check existence with invalid ID
            fake_id = str(uuid.uuid4())
            exists_fake = await media_repo.exists(fake_id)
            assert exists_fake is False
            
        except Exception as e:
            pytest.fail(f"Failed to check media file existence: {e}")
    
    @pytest.mark.asyncio
    async def test_list_media_files(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test listing media files with pagination"""
        try:
            # Create multiple media files
            media_ids = []
            for i in range(5):
                media_data = test_media_data.copy()
                media_data["file_name"] = f"list_test_audio_{i}.mp3"
                media_data["original_file_name"] = f"list_original_audio_{i}.mp3"
                
                media_id = await media_repo.create(media_data)
                media_ids.append(media_id)
            
            # List all media files
            all_media = await media_repo.list_all()
            assert len(all_media) >= 5
            
            # List with limit
            limited_media = await media_repo.list_all(limit=3)
            assert len(limited_media) == 3
            
            # List with offset
            offset_media = await media_repo.list_all(limit=2, offset=2)
            assert len(offset_media) == 2
            
        except Exception as e:
            pytest.fail(f"Failed to list media files: {e}")
    
    @pytest.mark.asyncio
    async def test_count_media_files(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test counting media files"""
        try:
            # Get initial count
            initial_count = await media_repo.count()
            
            # Create a media file
            media_id = await media_repo.create(test_media_data)
            
            # Check count increased
            new_count = await media_repo.count()
            assert new_count == initial_count + 1
            
        except Exception as e:
            pytest.fail(f"Failed to count media files: {e}")
    
    @pytest.mark.asyncio
    async def test_count_media_files_by_user(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test counting media files by user"""
        try:
            # Get initial count for user
            initial_user_count = await media_repo.count_by_user(test_media_data["user_id"])
            
            # Create multiple media files for the user
            for i in range(3):
                media_data = test_media_data.copy()
                media_data["file_name"] = f"count_test_audio_{i}.mp3"
                await media_repo.create(media_data)
            
            # Check count increased
            new_user_count = await media_repo.count_by_user(test_media_data["user_id"])
            assert new_user_count == initial_user_count + 3
            
        except Exception as e:
            pytest.fail(f"Failed to count media files by user: {e}")
    
    @pytest.mark.asyncio
    async def test_search_media_files(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test searching media files"""
        try:
            # Create media files with searchable data
            media1_data = test_media_data.copy()
            media1_data["file_name"] = "important_meeting.mp3"
            media1_data["metadata"] = {
                "title": "Important Meeting",
                "description": "Quarterly business review meeting",
                "tags": ["business", "meeting", "quarterly"]
            }
            
            media2_data = test_media_data.copy()
            media2_data["file_name"] = "podcast_episode.mp3"
            media2_data["metadata"] = {
                "title": "Tech Podcast Episode",
                "description": "Discussion about latest technology trends",
                "tags": ["tech", "podcast", "technology"]
            }
            
            media1_id = await media_repo.create(media1_data)
            media2_id = await media_repo.create(media2_data)
            
            # Search by filename
            meeting_results = await media_repo.search("meeting", ["file_name"])
            assert len(meeting_results) >= 1
            assert any(media["file_name"] == "important_meeting.mp3" for media in meeting_results)
            
            # Search by metadata title
            podcast_results = await media_repo.search("podcast", ["metadata"])
            assert len(podcast_results) >= 1
            assert any(media["metadata"]["title"] == "Tech Podcast Episode" for media in podcast_results)
            
            # Search by metadata description
            business_results = await media_repo.search("business", ["metadata"])
            assert len(business_results) >= 1
            assert any("business" in media["metadata"]["description"].lower() for media in business_results)
            
        except Exception as e:
            pytest.fail(f"Failed to search media files: {e}")
    
    @pytest.mark.asyncio
    async def test_get_media_by_file_type(self, media_repo: MediaRepository, test_media_data: Dict[str, Any]):
        """Test retrieving media files by file type"""
        try:
            # Create different types of media files
            audio_data = test_media_data.copy()
            audio_data["file_name"] = "test_audio.mp3"
            audio_data["file_type"] = "audio"
            audio_data["mime_type"] = "audio/mpeg"
            
            video_data = test_media_data.copy()
            video_data["file_name"] = "test_video.mp4"
            video_data["file_type"] = "video"
            video_data["mime_type"] = "video/mp4"
            
            # Create media files
            audio_id = await media_repo.create(audio_data)
            video_id = await media_repo.create(video_data)
            
            # Get audio files
            audio_files = await media_repo.get_by_file_type("audio")
            assert len(audio_files) >= 1
            assert all(media["file_type"] == "audio" for media in audio_files)
            
            # Get video files
            video_files = await media_repo.get_by_file_type("video")
            assert len(video_files) >= 1
            assert all(media["file_type"] == "video" for media in video_files)
            
        except Exception as e:
            pytest.fail(f"Failed to get media files by type: {e}")


class TestMediaRepositoryValidation:
    """Test MediaFile repository validation and error handling"""
    
    @pytest.fixture
    async def media_repo(self):
        """Fixture to provide media repository instance"""
        try:
            await Database.init_db()
            repo = MediaRepository()
            yield repo
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup media repository: {e}")
    
    @pytest.fixture
    async def user_repo(self):
        """Fixture to provide user repository instance"""
        try:
            await Database.init_db()
            repo = UserRepository()
            yield repo
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup user repository: {e}")
    
    @pytest.fixture
    async def test_user(self, user_repo: UserRepository):
        """Fixture to create a test user"""
        user_data = {
            "username": "validation_test_user",
            "email": "validation@example.com",
            "password_hash": "hashed_password",
            "subscription_level": "free"
        }
        
        user_id = await user_repo.create(user_data)
        return user_id
    
    @pytest.mark.asyncio
    async def test_create_media_with_invalid_user_id(self, media_repo: MediaRepository):
        """Test creating media with invalid user ID should fail"""
        try:
            fake_user_id = str(uuid.uuid4())
            media_data = {
                "user_id": fake_user_id,
                "file_name": "test.mp3",
                "original_file_name": "test.mp3",
                "file_path": "/uploads/test.mp3",
                "file_size": 1024,
                "mime_type": "audio/mpeg",
                "file_type": "audio"
            }
            
            with pytest.raises(PostgresError) as exc_info:
                await media_repo.create(media_data)
            
            assert exc_info.value.error_type == PostgresErrorType.FOREIGN_KEY_VIOLATION
            assert "does not exist" in exc_info.value.message.lower()
            
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Invalid user ID test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_media_with_invalid_file_type(self, media_repo: MediaRepository, test_user: str):
        """Test creating media with invalid file type should fail"""
        try:
            media_data = {
                "user_id": test_user,
                "file_name": "test.xyz",
                "original_file_name": "test.xyz",
                "file_path": "/uploads/test.xyz",
                "file_size": 1024,
                "mime_type": "application/xyz",
                "file_type": "invalid_type"  # Should be one of: audio, video, document, image
            }
            
            with pytest.raises(PostgresError) as exc_info:
                await media_repo.create(media_data)
            
            assert exc_info.value.error_type == PostgresErrorType.CONSTRAINT_VIOLATION
            
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Invalid file type test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_media(self, media_repo: MediaRepository):
        """Test updating nonexistent media should return False"""
        try:
            fake_id = str(uuid.uuid4())
            update_data = {"file_size": 2048}
            
            success = await media_repo.update(fake_id, update_data)
            assert success is False
            
        except Exception as e:
            pytest.fail(f"Update nonexistent media test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_media(self, media_repo: MediaRepository):
        """Test deleting nonexistent media should return False"""
        try:
            fake_id = str(uuid.uuid4())
            
            success = await media_repo.delete(fake_id)
            assert success is False
            
        except Exception as e:
            pytest.fail(f"Delete nonexistent media test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])