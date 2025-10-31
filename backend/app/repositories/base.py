"""
Base Repository Pattern for PostgreSQL Database Operations

This module provides a base repository class that implements common
database operations using asyncpg for PostgreSQL.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from ..core.postgres_db import Database, QueryError

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Base repository class for PostgreSQL operations"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._connection = None
    
    @property
    def connection(self) -> asyncpg.Connection:
        """Get database connection (lazy loading)"""
        if self._connection is None:
            raise RuntimeError("Connection not initialized. Use within context manager.")
        return self._connection
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._connection = await Database.get_pool().acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    # Basic CRUD operations
    
    async def create(self, data: Dict[str, Any]) -> str:
        """Create a new record"""
        try:
            # Ensure created_at is set
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Build the query
            columns = list(data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = list(data.values())
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """
            
            result = await self.connection.fetchval(query, *values)
            logger.debug(f"Created record in {self.table_name} with ID: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create record in {self.table_name}: {e}")
            raise QueryError(f"Create operation failed: {e}")
    
    async def get_by_id(self, record_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Get a record by ID"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE id = $1"
            row = await self.connection.fetchrow(query, str(record_id))
            
            if row:
                result = dict(row)
                logger.debug(f"Retrieved record from {self.table_name} with ID: {record_id}")
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get record from {self.table_name} with ID {record_id}: {e}")
            raise QueryError(f"Get operation failed: {e}")
    
    async def update(self, record_id: Union[str, uuid.UUID], data: Dict[str, Any]) -> bool:
        """Update a record by ID"""
        try:
            # Ensure updated_at is set
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow()
            
            # Build the query
            columns = [f"{key} = ${i+2}" for i, key in enumerate(data.keys(), start=1)]
            values = [str(record_id)] + list(data.values())
            
            query = f"""
                UPDATE {self.table_name}
                SET {', '.join(columns)}
                WHERE id = $1
            """
            
            result = await self.connection.execute(query, *values)
            success = result == "UPDATE 1"
            
            if success:
                logger.debug(f"Updated record in {self.table_name} with ID: {record_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update record in {self.table_name} with ID {record_id}: {e}")
            raise QueryError(f"Update operation failed: {e}")
    
    async def delete(self, record_id: Union[str, uuid.UUID]) -> bool:
        """Delete a record by ID"""
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = $1"
            result = await self.connection.execute(query, str(record_id))
            success = result == "DELETE 1"
            
            if success:
                logger.debug(f"Deleted record from {self.table_name} with ID: {record_id}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete record from {self.table_name} with ID {record_id}: {e}")
            raise QueryError(f"Delete operation failed: {e}")
    
    async def exists(self, record_id: Union[str, uuid.UUID]) -> bool:
        """Check if a record exists by ID"""
        try:
            query = f"SELECT 1 FROM {self.table_name} WHERE id = $1 LIMIT 1"
            result = await self.connection.fetchval(query, str(record_id))
            return result == 1
        except Exception as e:
            logger.error(f"Failed to check existence in {self.table_name} for ID {record_id}: {e}")
            raise QueryError(f"Exists check failed: {e}")
    
    async def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """List all records with pagination"""
        try:
            query = f"SELECT * FROM {self.table_name} ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            elif offset > 0:
                query += f" OFFSET {offset}"
            
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to list records from {self.table_name}: {e}")
            raise QueryError(f"List operation failed: {e}")
    
    async def count(self) -> int:
        """Count total records"""
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name}"
            result = await self.connection.fetchval(query)
            return result
        except Exception as e:
            logger.error(f"Failed to count records in {self.table_name}: {e}")
            raise QueryError(f"Count operation failed: {e}")
    
    # Custom query methods
    
    async def find_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """Find records by a specific field"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {field} = $1 ORDER BY created_at DESC"
            rows = await self.connection.fetch(query, value)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to find records by {field} in {self.table_name}: {e}")
            raise QueryError(f"Find operation failed: {e}")
    
    async def find_one_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Find one record by a specific field"""
        try:
            query = f"SELECT * FROM {self.table_name} WHERE {field} = $1 ORDER BY created_at DESC LIMIT 1"
            row = await self.connection.fetchrow(query, value)
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to find one record by {field} in {self.table_name}: {e}")
            raise QueryError(f"Find one operation failed: {e}")
    
    async def search(self, search_term: str, search_fields: List[str]) -> List[Dict[str, Any]]:
        """Search records in multiple text fields"""
        if not search_fields:
            return []
        
        try:
            # Build search condition
            search_conditions = []
            params = []
            
            for i, field in enumerate(search_fields):
                if i == 0:
                    search_conditions.append(f"CAST({field} AS TEXT) ILIKE ${i+1}")
                else:
                    search_conditions.append(f"OR CAST({field} AS TEXT) ILIKE ${i+1}")
                params.append(f"%{search_term}%")
            
            query = f"""
                SELECT * FROM {self.table_name}
                WHERE {' '.join(search_conditions)}
                ORDER BY created_at DESC
            """
            
            rows = await self.connection.fetch(query, *params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to search records in {self.table_name}: {e}")
            raise QueryError(f"Search operation failed: {e}")
    
    # JSONB-specific methods
    
    async def create_with_jsonb(self, data: Dict[str, Any], jsonb_data: Dict[str, Any]) -> str:
        """Create a record with JSONB data"""
        try:
            # Merge regular data with JSONB data
            combined_data = {**data, **jsonb_data}
            return await self.create(combined_data)
        except Exception as e:
            logger.error(f"Failed to create record with JSONB in {self.table_name}: {e}")
            raise QueryError(f"Create with JSONB failed: {e}")
    
    async def update_jsonb_field(self, record_id: Union[str, uuid.UUID], jsonb_field: str, update_data: Dict[str, Any]) -> bool:
        """Update a specific JSONB field"""
        try:
            # Get current data first
            current = await self.get_by_id(record_id)
            if not current:
                return False
            
            # Merge with new data
            current_data = current.get(jsonb_field, {})
            merged_data = {**current_data, **update_data}
            
            # Update the JSONB field
            data = {jsonb_field: merged_data, 'updated_at': datetime.utcnow()}
            return await self.update(record_id, data)
        except Exception as e:
            logger.error(f"Failed to update JSONB field {jsonb_field} in {self.table_name}: {e}")
            raise QueryError(f"JSONB field update failed: {e}")
    
    async def query_jsonb(self, jsonb_path: str, condition: str = None) -> List[Dict[str, Any]]:
        """Query JSONB fields using PostgreSQL JSONB operators"""
        try:
            if condition:
                where_clause = f"WHERE {jsonb_path} {condition}"
            else:
                where_clause = ""
            
            query = f"""
                SELECT * FROM {self.table_name}
                {where_clause}
                ORDER BY created_at DESC
            """
            
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to query JSONB in {self.table_name}: {e}")
            raise QueryError(f"JSONB query failed: {e}")


# Utility functions for common database operations
async def execute_transaction(operations: List[callable]) -> bool:
    """Execute multiple operations in a transaction"""
    async with Database.get_connection() as conn:
        try:
            async with conn.transaction():
                for operation in operations:
                    await operation(conn)
                return True
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return False