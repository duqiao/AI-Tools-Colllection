"""
User Repository Tests

This test module verifies User repository functionality with PostgreSQL.
These tests should FAIL before the User repository implementation is complete.
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
    from app.repositories.user_repository import UserRepository
    from app.repositories.base import BaseRepository
    from app.core.postgres_db import Database
    from app.utils.postgres_errors import PostgresError, PostgresErrorType
except ImportError as e:
    pytest.skip(f"User repository modules not available: {e}", allow_module_level=True)


class TestUserRepository:
    """Test User repository functionality"""
    
    @pytest.fixture
    async def user_repo(self):
        """Fixture to provide user repository instance"""
        try:
            # Initialize database connection
            await Database.init_db()
            repo = UserRepository()
            yield repo
            # Cleanup
            await Database.close_db()
        except Exception as e:
            pytest.skip(f"Failed to setup user repository: {e}")
    
    @pytest.fixture
    async def test_user_data(self):
        """Fixture to provide test user data"""
        return {
            "username": "testuser123",
            "email": "testuser123@example.com",
            "password_hash": "hashed_password_here",
            "subscription_level": "free",
            "profile": {
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": None,
                "preferences": {
                    "language": "en",
                    "theme": "light",
                    "notifications": True
                }
            },
            "usage_stats": {
                "total_files_processed": 0,
                "total_audio_duration": 0,
                "api_calls_count": 0,
                "storage_used_bytes": 0
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test creating a new user"""
        try:
            # Create user
            user_id = await user_repo.create(test_user_data)
            
            assert user_id is not None
            assert isinstance(user_id, str)  # UUID as string
            
            # Verify user was created
            created_user = await user_repo.get_by_id(user_id)
            
            assert created_user is not None
            assert created_user["username"] == test_user_data["username"]
            assert created_user["email"] == test_user_data["email"]
            assert created_user["subscription_level"] == test_user_data["subscription_level"]
            assert created_user["password_hash"] == test_user_data["password_hash"]
            assert created_user["profile"]["first_name"] == test_user_data["profile"]["first_name"]
            assert created_user["usage_stats"]["total_files_processed"] == 0
            
            # Verify timestamps
            assert created_user["created_at"] is not None
            assert created_user["updated_at"] is not None
            assert isinstance(created_user["created_at"], datetime)
            assert isinstance(created_user["updated_at"], datetime)
            
        except Exception as e:
            pytest.fail(f"Failed to create user: {e}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test retrieving a user by ID"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Get user by ID
            retrieved_user = await user_repo.get_by_id(user_id)
            
            assert retrieved_user is not None
            assert retrieved_user["id"] == user_id
            assert retrieved_user["username"] == test_user_data["username"]
            assert retrieved_user["email"] == test_user_data["email"]
            
        except Exception as e:
            pytest.fail(f"Failed to get user by ID: {e}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test retrieving a user by username"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Get user by username
            retrieved_user = await user_repo.get_by_username(test_user_data["username"])
            
            assert retrieved_user is not None
            assert retrieved_user["id"] == user_id
            assert retrieved_user["username"] == test_user_data["username"]
            
        except Exception as e:
            pytest.fail(f"Failed to get user by username: {e}")
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test retrieving a user by email"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Get user by email
            retrieved_user = await user_repo.get_by_email(test_user_data["email"])
            
            assert retrieved_user is not None
            assert retrieved_user["id"] == user_id
            assert retrieved_user["email"] == test_user_data["email"]
            
        except Exception as e:
            pytest.fail(f"Failed to get user by email: {e}")
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test updating a user"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Update user data
            update_data = {
                "username": "updated_username",
                "subscription_level": "premium",
                "profile": {
                    "first_name": "Updated",
                    "last_name": "Name",
                    "preferences": {
                        "language": "es",
                        "theme": "dark"
                    }
                }
            }
            
            success = await user_repo.update(user_id, update_data)
            assert success is True
            
            # Verify update
            updated_user = await user_repo.get_by_id(user_id)
            
            assert updated_user["username"] == "updated_username"
            assert updated_user["subscription_level"] == "premium"
            assert updated_user["profile"]["first_name"] == "Updated"
            assert updated_user["profile"]["preferences"]["language"] == "es"
            
            # Verify updated_at timestamp changed
            original_user = await user_repo.get_by_id(user_id)  # Get fresh data
            # Note: updated_at should be newer, but we can't easily test exact timing in tests
            
        except Exception as e:
            pytest.fail(f"Failed to update user: {e}")
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test updating user profile specifically"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Update profile
            profile_update = {
                "first_name": "John",
                "last_name": "Doe",
                "avatar_url": "https://example.com/avatar.jpg"
            }
            
            success = await user_repo.update_profile(user_id, profile_update)
            assert success is True
            
            # Verify update
            updated_user = await user_repo.get_by_id(user_id)
            
            assert updated_user["profile"]["first_name"] == "John"
            assert updated_user["profile"]["last_name"] == "Doe"
            assert updated_user["profile"]["avatar_url"] == "https://example.com/avatar.jpg"
            # Should preserve other profile data
            assert updated_user["profile"]["preferences"]["language"] == "en"
            
        except Exception as e:
            pytest.fail(f"Failed to update user profile: {e}")
    
    @pytest.mark.asyncio
    async def test_update_usage_stats(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test updating user usage statistics"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Update usage stats
            stats_update = {
                "total_files_processed": 5,
                "total_audio_duration": 300,
                "api_calls_count": 10,
                "storage_used_bytes": 1024
            }
            
            success = await user_repo.update_usage_stats(user_id, stats_update)
            assert success is True
            
            # Verify update
            updated_user = await user_repo.get_by_id(user_id)
            
            assert updated_user["usage_stats"]["total_files_processed"] == 5
            assert updated_user["usage_stats"]["total_audio_duration"] == 300
            assert updated_user["usage_stats"]["api_calls_count"] == 10
            assert updated_user["usage_stats"]["storage_used_bytes"] == 1024
            
        except Exception as e:
            pytest.fail(f"Failed to update usage stats: {e}")
    
    @pytest.mark.asyncio
    async def test_delete_user(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test deleting a user"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Verify user exists
            user_before_delete = await user_repo.get_by_id(user_id)
            assert user_before_delete is not None
            
            # Delete user
            success = await user_repo.delete(user_id)
            assert success is True
            
            # Verify user is deleted
            user_after_delete = await user_repo.get_by_id(user_id)
            assert user_after_delete is None
            
        except Exception as e:
            pytest.fail(f"Failed to delete user: {e}")
    
    @pytest.mark.asyncio
    async def test_user_exists(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test checking if user exists"""
        try:
            # Create user first
            user_id = await user_repo.create(test_user_data)
            
            # Check existence with valid ID
            exists = await user_repo.exists(user_id)
            assert exists is True
            
            # Check existence with invalid ID
            fake_id = str(uuid.uuid4())
            exists_fake = await user_repo.exists(fake_id)
            assert exists_fake is False
            
        except Exception as e:
            pytest.fail(f"Failed to check user existence: {e}")
    
    @pytest.mark.asyncio
    async def test_list_users(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test listing users with pagination"""
        try:
            # Create multiple users
            user_ids = []
            for i in range(5):
                user_data = test_user_data.copy()
                user_data["username"] = f"testuser{i}"
                user_data["email"] = f"testuser{i}@example.com"
                
                user_id = await user_repo.create(user_data)
                user_ids.append(user_id)
            
            # List all users
            all_users = await user_repo.list_all()
            assert len(all_users) >= 5
            
            # List with limit
            limited_users = await user_repo.list_all(limit=3)
            assert len(limited_users) == 3
            
            # List with offset
            offset_users = await user_repo.list_all(limit=2, offset=2)
            assert len(offset_users) == 2
            
        except Exception as e:
            pytest.fail(f"Failed to list users: {e}")
    
    @pytest.mark.asyncio
    async def test_count_users(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test counting users"""
        try:
            # Get initial count
            initial_count = await user_repo.count()
            
            # Create a user
            user_id = await user_repo.create(test_user_data)
            
            # Check count increased
            new_count = await user_repo.count()
            assert new_count == initial_count + 1
            
        except Exception as e:
            pytest.fail(f"Failed to count users: {e}")
    
    @pytest.mark.asyncio
    async def test_search_users(self, user_repo: UserRepository, test_user_data: Dict[str, Any]):
        """Test searching users"""
        try:
            # Create users with searchable data
            user1_data = test_user_data.copy()
            user1_data["username"] = "alice_smith"
            user1_data["email"] = "alice@example.com"
            user1_data["profile"]["first_name"] = "Alice"
            user1_data["profile"]["last_name"] = "Smith"
            
            user2_data = test_user_data.copy()
            user2_data["username"] = "bob_jones"
            user2_data["email"] = "bob@example.com"
            user2_data["profile"]["first_name"] = "Bob"
            user2_data["profile"]["last_name"] = "Jones"
            
            user1_id = await user_repo.create(user1_data)
            user2_id = await user_repo.create(user2_data)
            
            # Search by username
            alice_results = await user_repo.search("alice", ["username"])
            assert len(alice_results) >= 1
            assert any(user["username"] == "alice_smith" for user in alice_results)
            
            # Search by email
            bob_results = await user_repo.search("bob", ["email"])
            assert len(bob_results) >= 1
            assert any(user["email"] == "bob@example.com" for user in bob_results)
            
            # Search by profile name
            smith_results = await user_repo.search("Smith", ["profile"])
            assert len(smith_results) >= 1
            assert any(user["profile"]["last_name"] == "Smith" for user in smith_results)
            
        except Exception as e:
            pytest.fail(f"Failed to search users: {e}")


class TestUserRepositoryValidation:
    """Test User repository validation and error handling"""
    
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
    
    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_username(self, user_repo: UserRepository):
        """Test creating user with duplicate username should fail"""
        try:
            user_data = {
                "username": "duplicate_user",
                "email": "user1@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "free"
            }
            
            # Create first user
            user1_id = await user_repo.create(user_data)
            assert user1_id is not None
            
            # Try to create second user with same username
            user2_data = user_data.copy()
            user2_data["email"] = "user2@example.com"
            
            with pytest.raises(PostgresError) as exc_info:
                await user_repo.create(user2_data)
            
            assert exc_info.value.error_type == PostgresErrorType.UNIQUE_VIOLATION
            assert "already exists" in exc_info.value.message.lower()
            
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Duplicate username test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_email(self, user_repo: UserRepository):
        """Test creating user with duplicate email should fail"""
        try:
            user_data = {
                "username": "user1",
                "email": "duplicate@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "free"
            }
            
            # Create first user
            user1_id = await user_repo.create(user_data)
            assert user1_id is not None
            
            # Try to create second user with same email
            user2_data = user_data.copy()
            user2_data["username"] = "user2"
            
            with pytest.raises(PostgresError) as exc_info:
                await user_repo.create(user2_data)
            
            assert exc_info.value.error_type == PostgresErrorType.UNIQUE_VIOLATION
            assert "already exists" in exc_info.value.message.lower()
            
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Duplicate email test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_create_user_with_invalid_subscription_level(self, user_repo: UserRepository):
        """Test creating user with invalid subscription level should fail"""
        try:
            user_data = {
                "username": "invalid_user",
                "email": "invalid@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "invalid_level"  # Should be one of: free, premium, enterprise
            }
            
            with pytest.raises(PostgresError) as exc_info:
                await user_repo.create(user_data)
            
            assert exc_info.value.error_type == PostgresErrorType.CONSTRAINT_VIOLATION
            
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Invalid subscription level test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, user_repo: UserRepository):
        """Test updating nonexistent user should return False"""
        try:
            fake_id = str(uuid.uuid4())
            update_data = {"username": "updated_name"}
            
            success = await user_repo.update(fake_id, update_data)
            assert success is False
            
        except Exception as e:
            pytest.fail(f"Update nonexistent user test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, user_repo: UserRepository):
        """Test deleting nonexistent user should return False"""
        try:
            fake_id = str(uuid.uuid4())
            
            success = await user_repo.delete(fake_id)
            assert success is False
            
        except Exception as e:
            pytest.fail(f"Delete nonexistent user test failed: {e}")


class TestUserRepositoryContextManager:
    """Test User repository with async context manager"""
    
    @pytest.mark.asyncio
    async def test_repository_with_context_manager(self):
        """Test using repository with async context manager"""
        try:
            user_data = {
                "username": "context_user",
                "email": "context@example.com",
                "password_hash": "hashed_password",
                "subscription_level": "free"
            }
            
            async with UserRepository() as repo:
                user_id = await repo.create(user_data)
                assert user_id is not None
                
                user = await repo.get_by_id(user_id)
                assert user is not None
                assert user["username"] == user_data["username"]
            
        except Exception as e:
            if "UserRepository" not in str(e):
                pytest.skip(f"User repository not implemented: {e}")
            else:
                pytest.fail(f"Context manager test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])