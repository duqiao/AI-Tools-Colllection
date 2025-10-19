#!/usr/bin/env python3
"""
Test database connection for WeChat Media Translator
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

def test_database_connection():
    """Test connection to PostgreSQL database"""
    
    # Database connection parameters
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'wechat_translator',
        'user': 'postgres',
        'password': 'password'
    }
    
    try:
        print("🔍 Testing database connection...")
        
        # Connect to PostgreSQL
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version['version']}")
        
        # Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print("📋 Existing tables:")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("📋 No tables found (database is empty)")
        
        # Test creating a simple table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("INSERT INTO test_table DEFAULT VALUES;")
        connection.commit()
        
        cursor.execute("SELECT COUNT(*) as count FROM test_table;")
        count = cursor.fetchone()
        print(f"✅ Test table created and populated: {count['count']} rows")
        
        # Clean up
        cursor.execute("DROP TABLE IF EXISTS test_table;")
        connection.commit()
        
        cursor.close()
        connection.close()
        
        print("🎉 Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)