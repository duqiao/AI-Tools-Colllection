#!/usr/bin/env python3
"""
Quick PostgreSQL Connection Test

This script provides a simple way to test PostgreSQL connectivity
without requiring the full application to be configured.
"""

import os
import sys
import argparse
import asyncio
import asyncpg
from urllib.parse import urlparse


def parse_connection_string(url: str) -> dict:
    """Parse PostgreSQL connection string"""
    try:
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/') if parsed.path else 'postgres',
            'ssl': 'require' if parsed.scheme == 'postgresql+ssl' else 'prefer'
        }
    except Exception:
        return {}


async def test_connection(connection_string: str) -> bool:
    """Test PostgreSQL connection"""
    try:
        conn = await asyncpg.connect(
            connection_string,
            command_timeout=10
        )
        
        # Test basic query
        version = await conn.fetchval("SELECT version()")
        print(f"✅ Successfully connected to PostgreSQL")
        print(f"📊 Server version: {version.split(',')[0]}")
        
        # Test basic query
        await conn.fetchval("SELECT 1 as test")
        print("✅ Basic query executed successfully")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False


async def test_database_schema(connection_string: str) -> bool:
    """Test if database schema exists"""
    try:
        conn = await asyncpg.connect(
            connection_string,
            command_timeout=10
        )
        
        # Check if tables exist
        tables = ['users', 'media_files', 'processing_jobs', 'transcription_results']
        existing_tables = []
        
        for table in tables:
            try:
                result = await conn.fetchval(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = $1",
                    table
                )
                if result:
                    existing_tables.append(table)
            except Exception:
                pass
        
        if existing_tables:
            print(f"✅ Found {len(existing_tables)} tables: {', '.join(existing_tables)}")
        else:
            print("ℹ️  No tables found - database is empty, ready for migration")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False


async def run_tests(connection_string: str) -> bool:
    """Run all tests"""
    print("🚀 Starting PostgreSQL Connection Tests")
    print("=" * 50)
    
    print(f"🔗 Testing connection to: {connection_string}")
    
    # Test connection
    print("\n1️⃣ Testing database connection...")
    if not await test_connection(connection_string):
        return False
    
    # Test schema
    print("\n2️⃣ Checking database schema...")
    if not await test_database_schema(connection_string):
        return False
    
    print("\n✅ All tests passed!")
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test PostgreSQL connection")
    parser.add_argument(
        "--url", 
        default="postgresql://localhost:5432/ai_media_translation",
        help="PostgreSQL connection string (default: postgresql://localhost:5432/ai_media_translation)"
    )
    parser.add_argument(
        "--env-var",
        default="DATABASE_URL",
        help="Environment variable containing connection string"
    )
    
    args = parser.parse_args()
    
    # Get connection string
    connection_string = args.url
    
    # Try to get from environment if specified
    if args.env_var:
        env_value = os.getenv(args.env_var)
        if env_value:
            connection_string = env_value
            print(f"📝 Using connection string from environment variable {args.env_var}")
    
    print(f"🔗 Connection string: {connection_string}")
    
    # Run tests
    try:
        success = asyncio.run(run_tests(connection_string))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()