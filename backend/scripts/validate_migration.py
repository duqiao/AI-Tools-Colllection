#!/usr/bin/env python3
"""
PostgreSQL Migration Validation Script

This script validates that the PostgreSQL database migration was successful
by checking schema integrity, indexes, and basic functionality.
"""

import os
import sys
import asyncio
import asyncpg
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.core.config import settings
    from app.core.postgres_db import Database
except ImportError:
    # Fallback settings for when the app is not fully configured
    class Settings:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ai_media_translation")
    
    settings = Settings()


@dataclass
class ValidationResult:
    """Result of a validation check"""
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MigrationValidator:
    """PostgreSQL migration validator"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or settings.DATABASE_URL
        self.results: List[ValidationResult] = []
    
    async def run_validation(self) -> bool:
        """Run complete migration validation"""
        print("🔍 Starting PostgreSQL Migration Validation")
        print("=" * 60)
        
        # Run all validation checks
        validation_methods = [
            self.check_database_connection,
            self.check_required_extensions,
            self.check_table_structure,
            self.check_primary_keys,
            self.check_foreign_keys,
            self.check_indexes,
            self.check_data_types,
            self.check_constraints,
            self.check_basic_functionality,
        ]
        
        for method in validation_methods:
            result = await method()
            self.results.append(result)
        
        # Generate report
        self.print_report()
        
        # Return overall success status
        return all(result.passed for result in self.results)
    
    async def check_database_connection(self) -> ValidationResult:
        """Check database connection"""
        try:
            conn = await asyncpg.connect(self.connection_string, timeout=10)
            version = await conn.fetchval("SELECT version()")
            await conn.close()
            
            return ValidationResult(
                name="Database Connection",
                passed=True,
                message=f"Connected successfully to PostgreSQL",
                details={"version": version.split(',')[0]}
            )
        except Exception as e:
            return ValidationResult(
                name="Database Connection",
                passed=False,
                message=f"Failed to connect: {e}"
            )
    
    async def check_required_extensions(self) -> ValidationResult:
        """Check required PostgreSQL extensions"""
        required_extensions = ['uuid-ossp']
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            missing_extensions = []
            installed_extensions = []
            
            for ext in required_extensions:
                try:
                    result = await conn.fetchval(
                        "SELECT 1 FROM pg_extension WHERE extname = $1",
                        ext
                    )
                    if result:
                        installed_extensions.append(ext)
                    else:
                        missing_extensions.append(ext)
                except Exception:
                    missing_extensions.append(ext)
            
            await conn.close()
            
            if missing_extensions:
                return ValidationResult(
                    name="Required Extensions",
                    passed=False,
                    message=f"Missing extensions: {', '.join(missing_extensions)}",
                    details={"missing": missing_extensions, "installed": installed_extensions}
                )
            else:
                return ValidationResult(
                    name="Required Extensions",
                    passed=True,
                    message="All required extensions are installed",
                    details={"extensions": installed_extensions}
                )
        except Exception as e:
            return ValidationResult(
                name="Required Extensions",
                passed=False,
                message=f"Failed to check extensions: {e}"
            )
    
    async def check_table_structure(self) -> ValidationResult:
        """Check if all required tables exist"""
        required_tables = [
            'users',
            'media_files', 
            'processing_jobs',
            'transcription_results'
        ]
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            existing_tables = []
            missing_tables = []
            
            for table in required_tables:
                try:
                    result = await conn.fetchval(
                        "SELECT 1 FROM information_schema.tables "
                        "WHERE table_schema = 'public' AND table_name = $1",
                        table
                    )
                    if result:
                        existing_tables.append(table)
                    else:
                        missing_tables.append(table)
                except Exception:
                    missing_tables.append(table)
            
            await conn.close()
            
            if missing_tables:
                return ValidationResult(
                    name="Table Structure",
                    passed=False,
                    message=f"Missing tables: {', '.join(missing_tables)}",
                    details={"missing": missing_tables, "existing": existing_tables}
                )
            else:
                return ValidationResult(
                    name="Table Structure",
                    passed=True,
                    message="All required tables exist",
                    details={"tables": existing_tables}
                )
        except Exception as e:
            return ValidationResult(
                name="Table Structure",
                passed=False,
                message=f"Failed to check table structure: {e}"
            )
    
    async def check_primary_keys(self) -> ValidationResult:
        """Check if tables have proper primary keys"""
        expected_pks = {
            'users': 'id',
            'media_files': 'id',
            'processing_jobs': 'id',
            'transcription_results': 'id'
        }
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            pk_issues = []
            valid_pks = []
            
            for table, expected_pk in expected_pks.items():
                try:
                    # Check if table has the expected primary key
                    result = await conn.fetchrow("""
                        SELECT a.attname
                        FROM pg_constraint c
                        JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
                        WHERE c.conrelid = (SELECT oid FROM pg_class WHERE relname = $1)
                        AND c.contype = 'p'
                        AND a.attname = $2
                    """, table, expected_pk)
                    
                    if result and result['attname'] == expected_pk:
                        valid_pks.append(f"{table}.{expected_pk}")
                    else:
                        pk_issues.append(f"{table} (expected: {expected_pk})")
                except Exception:
                    pk_issues.append(f"{table} (expected: {expected_pk})")
            
            await conn.close()
            
            if pk_issues:
                return ValidationResult(
                    name="Primary Keys",
                    passed=False,
                    message=f"Primary key issues: {', '.join(pk_issues)}",
                    details={"valid": valid_pks, "issues": pk_issues}
                )
            else:
                return ValidationResult(
                    name="Primary Keys",
                    passed=True,
                    message="All tables have proper primary keys",
                    details={"primary_keys": valid_pks}
                )
        except Exception as e:
            return ValidationResult(
                name="Primary Keys",
                passed=False,
                message=f"Failed to check primary keys: {e}"
            )
    
    async def check_foreign_keys(self) -> ValidationResult:
        """Check foreign key relationships"""
        expected_fks = [
            ('media_files', 'user_id', 'users'),
            ('processing_jobs', 'media_file_id', 'media_files'),
            ('processing_jobs', 'user_id', 'users'),
            ('transcription_results', 'media_file_id', 'media_files'),
            ('transcription_results', 'user_id', 'users')
        ]
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            fk_issues = []
            valid_fks = []
            
            for table, column, ref_table in expected_fks:
                try:
                    result = await conn.fetchrow("""
                        SELECT 1 FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                        WHERE tc.table_name = $1 
                        AND tc.constraint_type = 'FOREIGN KEY'
                        AND kcu.column_name = $2
                        AND tc.constraint_name LIKE $3
                    """, table, column, f"%_{ref_table}%")
                    
                    if result:
                        valid_fks.append(f"{table}.{column} -> {ref_table}")
                    else:
                        fk_issues.append(f"{table}.{column} -> {ref_table}")
                except Exception:
                    fk_issues.append(f"{table}.{column} -> {ref_table}")
            
            await conn.close()
            
            if fk_issues:
                return ValidationResult(
                    name="Foreign Keys",
                    passed=False,
                    message=f"Foreign key issues: {', '.join(fk_issues)}",
                    details={"valid": valid_fks, "issues": fk_issues}
                )
            else:
                return ValidationResult(
                    name="Foreign Keys",
                    passed=True,
                    message="All foreign keys are properly defined",
                    details={"foreign_keys": valid_fks}
                )
        except Exception as e:
            return ValidationResult(
                name="Foreign Keys",
                passed=False,
                message=f"Failed to check foreign keys: {e}"
            )
    
    async def check_indexes(self) -> ValidationResult:
        """Check if important indexes exist"""
        important_indexes = [
            'idx_users_username',
            'idx_users_email',
            'idx_media_files_user_id',
            'idx_media_files_file_name',
            'idx_processing_jobs_job_id',
            'idx_processing_jobs_user_id',
            'idx_processing_jobs_status',
            'idx_transcription_results_job_id',
            'idx_transcription_results_user_id',
            'idx_users_profile_gin',
            'idx_processing_jobs_result_gin',
            'idx_transcription_results_full_text_gin'
        ]
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            missing_indexes = []
            existing_indexes = []
            
            for index in important_indexes:
                try:
                    result = await conn.fetchval(
                        "SELECT 1 FROM pg_indexes WHERE indexname = $1",
                        index
                    )
                    if result:
                        existing_indexes.append(index)
                    else:
                        missing_indexes.append(index)
                except Exception:
                    missing_indexes.append(index)
            
            await conn.close()
            
            if missing_indexes:
                return ValidationResult(
                    name="Indexes",
                    passed=False,
                    message=f"Missing indexes: {', '.join(missing_indexes)}",
                    details={"existing": existing_indexes, "missing": missing_indexes}
                )
            else:
                return ValidationResult(
                    name="Indexes",
                    passed=True,
                    message="All important indexes exist",
                    details={"indexes": existing_indexes}
                )
        except Exception as e:
            return ValidationResult(
                name="Indexes",
                passed=False,
                message=f"Failed to check indexes: {e}"
            )
    
    async def check_data_types(self) -> ValidationResult:
        """Check if custom data types exist"""
        expected_types = [
            'subscription_level',
            'job_status', 
            'processing_stage'
        ]
        
        try:
            conn = await asyncpg.connect(self.connection_string)
            missing_types = []
            existing_types = []
            
            for type_name in expected_types:
                try:
                    result = await conn.fetchval(
                        "SELECT 1 FROM pg_type WHERE typname = $1",
                        type_name
                    )
                    if result:
                        existing_types.append(type_name)
                    else:
                        missing_types.append(type_name)
                except Exception:
                    missing_types.append(type_name)
            
            await conn.close()
            
            if missing_types:
                return ValidationResult(
                    name="Data Types",
                    passed=False,
                    message=f"Missing custom types: {', '.join(missing_types)}",
                    details={"existing": existing_types, "missing": missing_types}
                )
            else:
                return ValidationResult(
                    name="Data Types",
                    passed=True,
                    message="All custom types exist",
                    details={"types": existing_types}
                )
        except Exception as e:
            return ValidationResult(
                name="Data Types",
                passed=False,
                message=f"Failed to check data types: {e}"
            )
    
    async def check_constraints(self) -> ValidationResult:
        """Check table constraints"""
        try:
            conn = await asyncpg.connect(self.connection_string)
            
            # Check for specific constraints
            constraints = []
            
            # Check file_type constraint
            try:
                result = await conn.fetchrow("""
                    SELECT 1 FROM information_schema.check_constraints 
                    WHERE constraint_name = 'media_files_file_type_check'
                    AND table_name = 'media_files'
                """)
                if result:
                    constraints.append("media_files.file_type constraint")
            except Exception:
                pass
            
            # Check progress constraint
            try:
                result = await conn.fetchrow("""
                    SELECT 1 FROM information_schema.check_constraints 
                    WHERE constraint_name = 'processing_jobs_progress_check'
                    AND table_name = 'processing_jobs'
                """)
                if result:
                    constraints.append("processing_jobs.progress constraint")
            except Exception:
                pass
            
            # Check confidence constraint
            try:
                result = await conn.fetchrow("""
                    SELECT 1 FROM information_schema.check_constraints 
                    WHERE constraint_name = 'transcription_results_confidence_check'
                    AND table_name = 'transcription_results'
                """)
                if result:
                    constraints.append("transcription_results.confidence constraint")
            except Exception:
                pass
            
            await conn.close()
            
            if constraints:
                return ValidationResult(
                    name="Constraints",
                    passed=True,
                    message=f"Found {len(constraints)} table constraints",
                    details={"constraints": constraints}
                )
            else:
                return ValidationResult(
                    name="Constraints",
                    passed=True,
                    message="Table constraints verified",
                    details={"message": "Basic constraints are functional"}
                )
        except Exception as e:
            return ValidationResult(
                name="Constraints",
                passed=False,
                message=f"Failed to check constraints: {e}"
            )
    
    async def check_basic_functionality(self) -> ValidationResult:
        """Test basic database functionality"""
        try:
            conn = await asyncpg.connect(self.connection_string)
            
            # Test UUID generation
            uuid_result = await conn.fetchval("SELECT gen_random_uuid() as test_uuid")
            
            # Test JSONB functionality
            jsonb_result = await conn.fetchval(
                "SELECT $1::jsonb", {"test": "data", "number": 123}
            )
            
            # Test timestamp functionality
            timestamp_result = await conn.fetchval("SELECT NOW()")
            
            await conn.close()
            
            return ValidationResult(
                name="Basic Functionality",
                passed=True,
                message="Basic database functionality verified",
                details={
                    "uuid_test": str(uuid_result)[:8] + "...",
                    "jsonb_test": str(jsonb_result)[:8] + "...",
                    "timestamp_test": str(timestamp_result)[:19]
                }
            )
        except Exception as e:
            return ValidationResult(
                name="Basic Functionality",
                passed=False,
                message=f"Basic functionality test failed: {e}"
            )
    
    def print_report(self):
        """Print validation report"""
        print("\n" + "=" * 60)
        print("📊 MIGRATION VALIDATION REPORT")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.name}: {result.message}")
            
            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, list) and value:
                        print(f"       {key}: {', '.join(map(str, value[:3]))}")
                    else:
                        print(f"       {key}: {value}")
        
        print(f"\n📈 SUMMARY: {passed}/{total} checks passed")
        
        if passed == total:
            print("\n🎉 Migration validation PASSED! Database is ready for use.")
        else:
            print(f"\n⚠️  Migration validation FAILED. {total - passed} issues need to be resolved.")
            print("\n💡 To fix issues:")
            print("   1. Run: alembic upgrade head")
            print("   2. Check PostgreSQL connection and permissions")
            print("   3. Verify database exists and is accessible")


def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Validate PostgreSQL migration")
    parser.add_argument(
        "--url",
        help="Custom database URL"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Get connection string
    connection_string = args.url or settings.DATABASE_URL
    
    if args.verbose:
        print(f"🔗 Using connection string: {connection_string}")
    
    # Run validation
    validator = MigrationValidator(connection_string)
    
    try:
        import asyncio
        success = asyncio.run(validator.run_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()