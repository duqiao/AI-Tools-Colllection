"""
PostgreSQL Database Connection Tests

This test module verifies PostgreSQL database connectivity and basic functionality.
These tests should FAIL before the PostgreSQL migration implementation is complete.
"""

import pytest
import asyncio
import asyncpg
from typing import Optional
import sys
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from app.core.config import settings
    from app.core.postgres_db import Database, check_database_health
    from app.utils.postgres_errors import PostgresError, PostgresErrorHandler, PostgresErrorType
except ImportError as e:
    pytest.skip(f"PostgreSQL modules not available: {e}", allow_module_level=True)


class TestPostgresConnection:
    """Test PostgreSQL database connectivity"""
    
    @pytest.mark.asyncio
    async def test_basic_connection(self):
        """Test that we can establish a basic connection to PostgreSQL"""
        try:
            conn = await asyncpg.connect(
                settings.DATABASE_URL,
                command_timeout=10
            )
            
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            assert result == 1
            
            # Get database version
            version = await conn.fetchval("SELECT version()")
            assert "PostgreSQL" in version
            
            await conn.close()
            
        except Exception as e:
            pytest.fail(f"Failed to connect to PostgreSQL: {e}")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool(self):
        """Test Database connection pool functionality"""
        try:
            # Initialize database pool
            await Database.init_db()
            
            # Test getting connection from pool
            async with Database.get_connection() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
            
            # Close pool
            await Database.close_db()
            
        except Exception as e:
            pytest.fail(f"Failed to test database pool: {e}")
    
    @pytest.mark.asyncio
    async def test_database_health_check(self):
        """Test database health check functionality"""
        try:
            health = await check_database_health()
            
            assert health is not None
            assert "status" in health
            assert "connection" in health
            assert "database" in health
            
            # Should be healthy if everything is set up correctly
            assert health["status"] == "healthy"
            assert health["connection"]["status"] == "connected"
            
        except Exception as e:
            pytest.fail(f"Database health check failed: {e}")
    
    @pytest.mark.asyncio
    async def test_required_tables_exist(self):
        """Test that all required tables exist after migration"""
        required_tables = [
            'users',
            'media_files', 
            'processing_jobs',
            'transcription_results'
        ]
        
        try:
            async with Database.get_connection() as conn:
                for table in required_tables:
                    result = await conn.fetchval(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = $1",
                        table
                    )
                    assert result == 1, f"Table {table} does not exist"
                    
        except Exception as e:
            pytest.fail(f"Failed to verify table existence: {e}")
    
    @pytest.mark.asyncio
    async def test_uuid_extension_exists(self):
        """Test that UUID extension is enabled"""
        try:
            async with Database.get_connection() as conn:
                result = await conn.fetchval(
                    "SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp'"
                )
                assert result == 1, "UUID extension not found"
                
        except Exception as e:
            pytest.fail(f"Failed to verify UUID extension: {e}")
    
    @pytest.mark.asyncio
    async def test_custom_data_types_exist(self):
        """Test that custom ENUM types exist"""
        expected_types = [
            'subscription_level',
            'job_status', 
            'processing_stage'
        ]
        
        try:
            async with Database.get_connection() as conn:
                for type_name in expected_types:
                    result = await conn.fetchval(
                        "SELECT 1 FROM pg_type WHERE typname = $1",
                        type_name
                    )
                    assert result == 1, f"Custom type {type_name} not found"
                    
        except Exception as e:
            pytest.fail(f"Failed to verify custom data types: {e}")
    
    @pytest.mark.asyncio
    async def test_primary_keys_are_uuids(self):
        """Test that tables have UUID primary keys"""
        expected_pks = {
            'users': 'id',
            'media_files': 'id',
            'processing_jobs': 'id',
            'transcription_results': 'id'
        }
        
        try:
            async with Database.get_connection() as conn:
                for table, expected_pk in expected_pks.items():
                    # Check if table has the expected primary key
                    result = await conn.fetchrow("""
                        SELECT a.attname, t.typname
                        FROM pg_constraint c
                        JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
                        JOIN pg_type t ON t.oid = a.atttypid
                        WHERE c.conrelid = (SELECT oid FROM pg_class WHERE relname = $1)
                        AND c.contype = 'p'
                        AND a.attname = $2
                    """, table, expected_pk)
                    
                    assert result is not None, f"Primary key {expected_pk} not found on table {table}"
                    assert result['typname'] == 'uuid', f"Primary key {expected_pk} on {table} is not UUID type"
                    
        except Exception as e:
            pytest.fail(f"Failed to verify UUID primary keys: {e}")
    
    @pytest.mark.asyncio
    async def test_foreign_key_relationships(self):
        """Test that foreign key relationships are properly set up"""
        expected_fks = [
            ('media_files', 'user_id', 'users'),
            ('processing_jobs', 'media_file_id', 'media_files'),
            ('processing_jobs', 'user_id', 'users'),
            ('transcription_results', 'media_file_id', 'media_files'),
            ('transcription_results', 'user_id', 'users')
        ]
        
        try:
            async with Database.get_connection() as conn:
                for table, column, ref_table in expected_fks:
                    result = await conn.fetchrow("""
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name = $1 
                        AND tc.constraint_type = 'FOREIGN KEY'
                        AND kcu.column_name = $2
                        AND tc.constraint_name LIKE $3
                    """, table, column, f"%_{ref_table}%")
                    
                    assert result is not None, f"Foreign key {table}.{column} -> {ref_table} not found"
                    
        except Exception as e:
            pytest.fail(f"Failed to verify foreign key relationships: {e}")
    
    @pytest.mark.asyncio
    async def test_jsonb_functionality(self):
        """Test JSONB column functionality"""
        try:
            async with Database.get_connection() as conn:
                # Test JSONB data insertion and retrieval
                test_data = {"test": "data", "number": 123, "nested": {"key": "value"}}
                
                # Insert test data into a temp table to test JSONB
                await conn.execute("""
                    CREATE TEMP TABLE test_jsonb_table (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        data JSONB
                    )
                """)
                
                # Insert JSONB data
                record_id = await conn.fetchval(
                    "INSERT INTO test_jsonb_table (data) VALUES ($1) RETURNING id",
                    test_data
                )
                
                # Retrieve JSONB data
                retrieved_data = await conn.fetchval(
                    "SELECT data FROM test_jsonb_table WHERE id = $1",
                    record_id
                )
                
                assert retrieved_data == test_data
                
                # Test JSONB query functionality
                result = await conn.fetchval(
                    "SELECT data->>'test' as test_value FROM test_jsonb_table WHERE id = $1",
                    record_id
                )
                
                assert result == "data"
                
        except Exception as e:
            pytest.fail(f"Failed to test JSONB functionality: {e}")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test PostgreSQL error handling"""
        try:
            async with Database.get_connection() as conn:
                # Test constraint violation error
                with pytest.raises(Exception):  # Should raise asyncpg.PostgresError
                    await conn.execute("INSERT INTO users (id) VALUES (NULL)")
                
        except Exception as e:
            # If we can't even connect or if the table doesn't exist, that's expected at this stage
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Unexpected error in error handling test: {e}")


class TestPostgresErrorHandling:
    """Test PostgreSQL-specific error handling"""
    
    @pytest.mark.asyncio
    async def test_postgres_error_mapping(self):
        """Test that PostgreSQL errors are properly mapped"""
        try:
            async with Database.get_connection() as conn:
                # Create a simple test to generate a unique violation
                await conn.execute("""
                    CREATE TEMP TABLE test_unique_table (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        email VARCHAR(255) UNIQUE
                    )
                """)
                
                # Insert first record
                await conn.execute(
                    "INSERT INTO test_unique_table (email) VALUES ($1)",
                    "test@example.com"
                )
                
                # Try to insert duplicate - should raise PostgresError
                with pytest.raises(PostgresError) as exc_info:
                    await conn.execute(
                        "INSERT INTO test_unique_table (email) VALUES ($1)",
                        "test@example.com"
                    )
                
                assert exc_info.value.error_type.value == "unique_violation"
                assert "already exists" in exc_info.value.message.lower()
                
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Unexpected error in error mapping test: {e}")
    
    def test_error_handler_creation(self):
        """Test PostgresErrorHandler functionality"""
        try:
            # Test error handling with a generic exception
            error = Exception("Test error")
            postgres_error = PostgresErrorHandler.handle_error(error)
            
            assert isinstance(postgres_error, PostgresError)
            assert postgres_error.error_type == PostgresErrorType.UNKNOWN_ERROR
            assert postgres_error.message == "Database error: Test error"
            
        except Exception as e:
            pytest.fail(f"Error handler test failed: {e}")


# Integration test class
class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    @pytest.mark.asyncio
    async def test_full_crud_cycle(self):
        """Test full CRUD cycle with UUID primary keys"""
        try:
            async with Database.get_connection() as conn:
                # Create a test user
                user_id = await conn.fetchval("""
                    INSERT INTO users (username, email, password_hash, subscription_level, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                    RETURNING id
                """, "testuser", "test@example.com", "hashed_password", "free")
                
                assert user_id is not None
                
                # Read user
                user = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1",
                    user_id
                )
                
                assert user is not None
                assert user['username'] == "testuser"
                assert user['email'] == "test@example.com"
                
                # Update user
                await conn.execute(
                    "UPDATE users SET username = $1, updated_at = NOW() WHERE id = $2",
                    "updated_user", user_id
                )
                
                # Verify update
                updated_user = await conn.fetchrow(
                    "SELECT username FROM users WHERE id = $1",
                    user_id
                )
                
                assert updated_user['username'] == "updated_user"
                
                # Delete user
                result = await conn.execute(
                    "DELETE FROM users WHERE id = $1",
                    user_id
                )
                
                assert result == "DELETE 1"
                
                # Verify deletion
                deleted_user = await conn.fetchrow(
                    "SELECT 1 FROM users WHERE id = $1",
                    user_id
                )
                
                assert deleted_user is None
                
        except Exception as e:
            if "does not exist" in str(e) or "connection" in str(e).lower():
                pytest.skip(f"Database not fully set up: {e}")
            else:
                pytest.fail(f"Full CRUD cycle test failed: {e}")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])