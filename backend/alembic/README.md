# Alembic Database Migrations

This directory contains Alembic migration scripts for the PostgreSQL database schema used in the AI Media Translation API.

## Structure

- `alembic.ini` - Alembic configuration file
- `env.py` - Alembic environment setup
- `script.py.mako` - Template for generating migration scripts
- `versions/` - Directory containing migration scripts

## Migration Files

### 001_initial_schema.py
Initial PostgreSQL schema with:
- UUID primary keys
- JSONB columns for flexible data storage
- Proper foreign key relationships
- Comprehensive indexing strategy
- Custom types for enums

## Usage

### Create new migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Run migrations
```bash
cd backend
alembic upgrade head
```

### Rollback migrations
```bash
cd backend
alembic downgrade -1
```

### Check current version
```bash
cd backend
alembic current
```

## Migration Dependencies

This migration depends on:
- PostgreSQL 13+ (for UUID generation and JSONB support)
- The `uuid-ossp` extension
- Proper database permissions

## Notes

- All tables use UUID primary keys with `gen_random_uuid()`
- JSONB columns provide MongoDB-like flexibility for complex data
- Comprehensive indexing strategy for performance
- Foreign key constraints with CASCADE deletes
- Timestamp columns use TIMESTAMPTZ for timezone-aware storage