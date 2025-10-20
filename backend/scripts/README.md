# Data Migration & Validation Scripts

This directory contains scripts for migrating data from the Node.js (MongoDB) backend to the FastAPI (PostgreSQL) backend.

## Scripts Overview

### 1. Migration Script (`migrate_data.py`)

**Purpose**: Migrates all data from MongoDB (Node.js) to PostgreSQL (FastAPI)

**Features**:
- ✅ Complete data migration (users, subscriptions, translations, payments)
- ✅ Batch processing for large datasets
- ✅ Data validation and type conversion
- ✅ Progress tracking and logging
- ✅ Dry-run mode for testing
- ✅ Error handling and rollback capability
- ✅ Detailed statistics and reporting

**Usage**:
```bash
# Dry run (simulates migration without making changes)
python migrate_data.py --dry-run

# Live migration with custom batch size
python migrate_data.py --batch-size=50

# Migration with custom database connections
python migrate_data.py --source-uri="mongodb://localhost:27017" --target-uri="postgresql://user:pass@localhost/db"
```

**Migration Flow**:
1. **Users** → Migrates user accounts with subscription info
2. **Subscriptions** → Migrates subscription plans and status
3. **Translations** → Migrates translation tasks and results
4. **Payments** → Migrates payment orders and transactions
5. **Usage Records** → Derived from translation data

### 2. Validation Script (`validate_migration.py`)

**Purpose**: Validates the completeness and integrity of migrated data

**Features**:
- ✅ Record count verification between source and target
- ✅ Data integrity constraint checking
- ✅ Foreign key relationship validation
- ✅ Data consistency verification
- ✅ Detailed issue reporting with severity levels
- ✅ Recommendations for fixing issues
- ✅ JSON report generation

**Usage**:
```bash
# Basic validation
python validate_migration.py

# Detailed validation with specific field checking
python validate_migration.py --detailed

# Generate JSON report
python validate_migration.py --output-report=migration_report.json
```

**Validation Checks**:
- **Record Matching**: Compares MongoDB vs PostgreSQL record counts
- **Data Integrity**: Checks for duplicates, null constraints, data types
- **Foreign Keys**: Validates relationships between tables
- **Data Consistency**: Ensures logical data relationships
- **Business Rules**: Validates quota limits, subscription status, etc.

## Prerequisites

### Database Setup
```bash
# MongoDB (source) should be running
# PostgreSQL (target) should be running with schema created via Alembic
```

### Python Dependencies
```bash
# Install required packages
pip install pymongo sqlalchemy pydantic fastapi
```

### Environment Configuration
Ensure your FastAPI backend configuration includes:
- MongoDB connection URI (`MONGODB_URI`)
- PostgreSQL connection URI (`DATABASE_URL`)

## Before Migration

### 1. Backup Data
```bash
# Backup MongoDB
mongodump --db media_translator --out /path/to/backup

# Backup PostgreSQL (if exists)
pg_dump -h localhost -U username dbname > postgres_backup.sql
```

### 2. Verify Schema
```bash
# Run Alembic migrations to create PostgreSQL schema
alembic upgrade head
```

### 3. Test Connections
```bash
# Test the scripts with --dry-run first
python migrate_data.py --dry-run
python validate_migration.py --detailed
```

## Migration Process

### Step 1: Dry Run Test
```bash
python migrate_data.py --dry-run --batch-size=10
```
**Expected**: See statistics without actual data changes

### Step 2: Execute Migration
```bash
python migrate_data.py --batch-size=100
```
**Expected**: Progress tracking as data migrates

### Step 3: Validate Results
```bash
python validate_migration.py --detailed --output-report=migration_report.json
```
**Expected**: Detailed validation report

### Step 4: Review Issues
Check the validation report for any issues:
- **Critical**: Must fix before production
- **High**: Should fix before production  
- **Medium**: Review and fix if needed
- **Low**: Can address later

## Troubleshooting

### Common Issues

#### 1. Connection Errors
```
❌ Database connection failed
```
**Solution**: Verify database URIs and network connectivity

#### 2. Missing Records
```
❌ Found X users missing in PostgreSQL
```
**Solution**: Re-run migration for specific missing records

#### 3. Data Type Mismatches
```
❌ Data type mismatch for field X
```
**Solution**: Review data conversion logic in migration script

#### 4. Foreign Key Violations
```
❌ Found orphaned translations with no user
```
**Solution**: Fix relationships or remove orphaned records

### Recovery Procedures

#### Partial Migration Recovery
If migration fails partway:
1. Migration script maintains transaction integrity
2. Re-run the same script - it will skip already migrated records
3. Use validation script to identify missing data

#### Rollback Plan
If migration needs to be reverted:
1. Restore PostgreSQL from backup
2. Restore MongoDB from backup
3. Re-run migration after fixing issues

## Post-Migration Tasks

### 1. Update Application Configuration
- Point frontend to new FastAPI backend
- Update database connection strings
- Verify API endpoints are accessible

### 2. Data Verification
```bash
# Run comprehensive validation
python validate_migration.py --detailed

# Run backend tests
pytest tests/contract/test_fastapi_api.py
pytest tests/integration/test_backend_migration.py
```

### 3. Performance Monitoring
- Monitor query performance
- Check database connection pools
- Verify response times meet requirements

### 4. User Acceptance Testing
- Test complete user workflows
- Verify all API endpoints work correctly
- Test error handling and edge cases

## Migration Statistics Example

After successful migration, you should see output like:

```
📊 MIGRATION SUMMARY
══════════════════════════════════════════════════════════════════════
Duration: 45.23 seconds
Mode: LIVE

👥 Users:
  Total: 1,247
  Migrated: 1,247
  Failed: 0

💳 Subscriptions:
  Total: 156
  Migrated: 156
  Failed: 0

🔤 Translations:
  Total: 3,842
  Migrated: 3,842
  Failed: 0

💰 Payments:
  Total: 89
  Migrated: 89
  Failed: 0

📈 Overall:
  Total Records: 5,334
  Migrated: 5,334
  Failed: 0
  Success Rate: 100.0%
══════════════════════════════════════════════════════════════════════
🎉 Migration completed successfully!
```

## Support

For issues or questions:
1. Check log files (`migration.log`, `validation.log`)
2. Review validation reports
3. Check the troubleshooting section above
4. Consult the development team

## Notes

- Migration scripts are idempotent and can be re-run safely
- Always perform a dry-run before live migration
- Keep backups of both source and target databases
- Monitor system resources during migration
- Test thoroughly before production deployment