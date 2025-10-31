"""
PostgreSQL-Specific Error Handling Utilities

This module provides specialized error handling for PostgreSQL operations,
including error mapping, retry logic, and user-friendly error messages.
"""

import asyncpg
import logging
from typing import Optional, Dict, Any, Type
from enum import Enum
import asyncio
import time

logger = logging.getLogger(__name__)


class PostgresErrorType(Enum):
    """PostgreSQL error types for better error handling"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    CONSTRAINT_VIOLATION = "constraint_violation"
    UNIQUE_VIOLATION = "unique_violation"
    FOREIGN_KEY_VIOLATION = "foreign_key_violation"
    NOT_FOUND = "not_found"
    PERMISSION_DENIED = "permission_denied"
    SYNTAX_ERROR = "syntax_error"
    DATA_TYPE_MISMATCH = "data_type_mismatch"
    DEADLOCK = "deadlock"
    DISK_FULL = "disk_full"
    OUT_OF_MEMORY = "out_of_memory"
    TOO_MANY_CONNECTIONS = "too_many_connections"
    UNKNOWN_ERROR = "unknown_error"


class PostgresError(Exception):
    """Custom PostgreSQL error with additional context"""
    
    def __init__(
        self,
        message: str,
        error_type: PostgresErrorType = PostgresErrorType.UNKNOWN_ERROR,
        original_error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_type.value}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error": self.error_type.value,
            "message": self.message,
            "context": self.context,
            "timestamp": time.time()
        }


class PostgresErrorHandler:
    """Handler for PostgreSQL errors with intelligent error mapping"""
    
    # PostgreSQL error code to error type mapping
    ERROR_CODE_MAP = {
        # Connection errors
        "08001": PostgresErrorType.CONNECTION_ERROR,
        "08003": PostgresErrorType.CONNECTION_ERROR,
        "08004": PostgresErrorType.CONNECTION_ERROR,
        "08006": PostgresErrorType.CONNECTION_ERROR,
        "08007": PostgresErrorType.CONNECTION_ERROR,
        "08P01": PostgresErrorType.CONNECTION_ERROR,
        
        # Timeout errors
        "57014": PostgresErrorType.TIMEOUT_ERROR,
        
        # Constraint violations
        "23000": PostgresErrorType.CONSTRAINT_VIOLATION,
        "23514": PostgresErrorType.CONSTRAINT_VIOLATION,
        
        # Unique violations
        "23501": PostgresErrorType.UNIQUE_VIOLATION,
        "23505": PostgresErrorType.UNIQUE_VIOLATION,
        
        # Foreign key violations
        "23502": PostgresErrorType.FOREIGN_KEY_VIOLATION,
        "23503": PostgresErrorType.FOREIGN_KEY_VIOLATION,
        "23504": PostgresErrorType.FOREIGN_KEY_VIOLATION,
        "23506": PostgresErrorType.FOREIGN_KEY_VIOLATION,
        
        # Not found
        "02000": PostgresErrorType.NOT_FOUND,
        "P0002": PostgresErrorType.NOT_FOUND,
        
        # Permission denied
        "02501": PostgresErrorType.PERMISSION_DENIED,
        "02502": PostgresErrorType.PERMISSION_DENIED,
        "02503": PostgresErrorType.PERMISSION_DENIED,
        "02504": PostgresErrorType.PERMISSION_DENIED,
        "28000": PostgresErrorType.PERMISSION_DENIED,
        "28P01": PostgresErrorType.PERMISSION_DENIED,
        
        # Syntax errors
        "42601": PostgresErrorType.SYNTAX_ERROR,
        "42602": PostgresErrorType.SYNTAX_ERROR,
        "42611": PostgresErrorType.SYNTAX_ERROR,
        "42622": PostgresErrorType.SYNTAX_ERROR,
        
        # Data type mismatches
        "22018": PostgresErrorType.DATA_TYPE_MISMATCH,
        "22021": PostgresErrorType.DATA_TYPE_MISMATCH,
        "22023": PostgresErrorType.DATA_TYPE_MISMATCH,
        "22007": PostgresErrorType.DATA_TYPE_MISMATCH,
        "22008": PostgresErrorType.DATA_TYPE_MISMATCH,
        
        # Deadlock
        "40P01": PostgresErrorType.DEADLOCK,
        
        # Disk full
        "53100": PostgresErrorType.DISK_FULL,
        "53200": PostgresErrorType.OUT_OF_MEMORY,
        "53300": PostgresErrorType.TOO_MANY_CONNECTIONS,
        "53400": PostgresErrorType.TOO_MANY_CONNECTIONS,
    }
    
    # Retry configuration for different error types
    RETRY_CONFIG = {
        PostgresErrorType.CONNECTION_ERROR: {"max_retries": 3, "delay": 1.0, "backoff": 2.0},
        PostgresErrorType.TIMEOUT_ERROR: {"max_retries": 2, "delay": 0.5, "backoff": 1.5},
        PostgresErrorType.DEADLOCK: {"max_retries": 3, "delay": 0.1, "backoff": 2.0},
        PostgresErrorType.TOO_MANY_CONNECTIONS: {"max_retries": 5, "delay": 2.0, "backoff": 1.5},
    }
    
    @classmethod
    def handle_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None) -> PostgresError:
        """Convert a database error to a PostgresError with appropriate type"""
        
        if isinstance(error, PostgresError):
            return error
        
        if isinstance(error, asyncpg.PostgresError):
            error_code = getattr(error, 'sqlstate', None)
            error_type = cls.ERROR_CODE_MAP.get(error_code, PostgresErrorType.UNKNOWN_ERROR)
            
            # Create user-friendly messages based on error type
            message = cls._create_user_message(error, error_type)
            
            return PostgresError(
                message=message,
                error_type=error_type,
                original_error=error,
                context={
                    "sqlstate": error_code,
                    "detail": getattr(error, 'detail', None),
                    "hint": getattr(error, 'hint', None),
                    **(context or {})
                }
            )
        
        elif isinstance(error, asyncpg.InterfaceError):
            return PostgresError(
                message="Database connection failed",
                error_type=PostgresErrorType.CONNECTION_ERROR,
                original_error=error,
                context=context
            )
        
        elif isinstance(error, asyncio.TimeoutError):
            return PostgresError(
                message="Database operation timed out",
                error_type=PostgresErrorType.TIMEOUT_ERROR,
                original_error=error,
                context=context
            )
        
        else:
            return PostgresError(
                message=f"Database error: {str(error)}",
                error_type=PostgresErrorType.UNKNOWN_ERROR,
                original_error=error,
                context=context
            )
    
    @staticmethod
    def _create_user_message(error: asyncpg.PostgresError, error_type: PostgresErrorType) -> str:
        """Create user-friendly error messages"""
        
        if error_type == PostgresErrorType.UNIQUE_VIOLATION:
            return "A record with this value already exists"
        
        elif error_type == PostgresErrorType.FOREIGN_KEY_VIOLATION:
            return "Referenced record does not exist"
        
        elif error_type == PostgresErrorType.CONSTRAINT_VIOLATION:
            detail = getattr(error, 'detail', '')
            if 'not null' in detail.lower():
                return "Required field is missing"
            elif 'check constraint' in detail.lower():
                return "Invalid value provided"
            return "Data constraint violation"
        
        elif error_type == PostgresErrorType.CONNECTION_ERROR:
            return "Unable to connect to database"
        
        elif error_type == PostgresErrorType.TIMEOUT_ERROR:
            return "Operation took too long to complete"
        
        elif error_type == PostgresErrorType.PERMISSION_DENIED:
            return "Permission denied for this operation"
        
        elif error_type == PostgresErrorType.DATA_TYPE_MISMATCH:
            return "Invalid data type provided"
        
        elif error_type == PostgresErrorType.DEADLOCK:
            return "Concurrent operation conflict, please try again"
        
        elif error_type == PostgresErrorType.TOO_MANY_CONNECTIONS:
            return "Database is busy, please try again later"
        
        else:
            return f"Database error: {str(error)}"
    
    @classmethod
    async def execute_with_retry(
        cls,
        operation,
        *args,
        max_retries: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Execute a database operation with automatic retry logic"""
        
        last_error = None
        
        try:
            return await operation(*args, **kwargs)
        
        except Exception as e:
            postgres_error = cls.handle_error(e, context)
            
            # Check if this error type is retryable
            retry_config = cls.RETRY_CONFIG.get(postgres_error.error_type)
            if not retry_config:
                raise postgres_error
            
            # Use provided max_retries or default from config
            max_retry_attempts = max_retries or retry_config["max_retries"]
            
            for attempt in range(max_retry_attempts):
                delay = retry_config["delay"] * (retry_config["backoff"] ** attempt)
                
                logger.warning(
                    f"Retry attempt {attempt + 1}/{max_retry_attempts} for "
                    f"{postgres_error.error_type.value} after {delay:.2f}s delay"
                )
                
                await asyncio.sleep(delay)
                
                try:
                    return await operation(*args, **kwargs)
                
                except Exception as retry_error:
                    last_error = cls.handle_error(retry_error, context)
                    
                    # If it's a different error type, don't retry
                    if last_error.error_type != postgres_error.error_type:
                        raise last_error
            
            # All retries failed
            raise last_error


# Utility functions for common error handling scenarios

async def safe_execute(
    operation,
    *args,
    reraise: bool = True,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[bool, Any]:
    """
    Safely execute a database operation with error handling
    
    Returns:
        tuple: (success: bool, result: Any or error: PostgresError)
    """
    try:
        result = await operation(*args, **kwargs)
        return True, result
    
    except Exception as e:
        error = PostgresErrorHandler.handle_error(e, context)
        logger.error(f"Database operation failed: {error}")
        
        if reraise:
            raise error
        
        return False, error


async def safe_execute_with_retry(
    operation,
    *args,
    reraise: bool = True,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> tuple[bool, Any]:
    """
    Safely execute a database operation with error handling and retry logic
    
    Returns:
        tuple: (success: bool, result: Any or error: PostgresError)
    """
    try:
        result = await PostgresErrorHandler.execute_with_retry(
            operation, *args, context=context, **kwargs
        )
        return True, result
    
    except Exception as e:
        error = PostgresErrorHandler.handle_error(e, context)
        logger.error(f"Database operation failed after retries: {error}")
        
        if reraise:
            raise error
        
        return False, error


def log_error(error: PostgresError, additional_context: Optional[Dict[str, Any]] = None):
    """Log PostgreSQL errors with detailed context"""
    
    log_data = {
        "error_type": error.error_type.value,
        "message": error.message,
        "context": error.context,
        "original_error": str(error.original_error) if error.original_error else None,
        **(additional_context or {})
    }
    
    if error.error_type in [
        PostgresErrorType.CONNECTION_ERROR,
        PostgresErrorType.PERMISSION_DENIED,
        PostgresErrorType.DISK_FULL,
        PostgresErrorType.OUT_OF_MEMORY
    ]:
        logger.critical(f"Critical database error: {error}", extra=log_data)
    
    elif error.error_type in [
        PostgresErrorType.TIMEOUT_ERROR,
        PostgresErrorType.DEADLOCK,
        PostgresErrorType.TOO_MANY_CONNECTIONS
    ]:
        logger.warning(f"Database operation issue: {error}", extra=log_data)
    
    else:
        logger.error(f"Database error: {error}", extra=log_data)


# Exception decorators for easy error handling

def postgres_error_handler(context: Optional[Dict[str, Any]] = None):
    """Decorator for automatic PostgreSQL error handling"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                error = PostgresErrorHandler.handle_error(e, context)
                log_error(error)
                raise error
        
        return wrapper
    return decorator


def postgres_retry_handler(
    max_retries: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Decorator for automatic PostgreSQL error handling with retry"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await PostgresErrorHandler.execute_with_retry(
                func, *args, max_retries=max_retries, context=context, **kwargs
            )
        
        return wrapper
    return decorator


# Common error responses for API endpoints

def create_error_response(error: PostgresError, status_code: int = 500) -> Dict[str, Any]:
    """Create standardized error response for API endpoints"""
    
    return {
        "error": {
            "type": error.error_type.value,
            "message": error.message,
            "details": error.context
        },
        "status": "error",
        "status_code": status_code,
        "timestamp": time.time()
    }


def create_not_found_response(resource: str, identifier: Any) -> Dict[str, Any]:
    """Create standardized not found response"""
    
    return create_error_response(
        PostgresError(
            message=f"{resource.title()} not found",
            error_type=PostgresErrorType.NOT_FOUND,
            context={"resource": resource, "identifier": str(identifier)}
        ),
        status_code=404
    )


def create_unique_violation_response(field: str, value: Any) -> Dict[str, Any]:
    """Create standardized unique violation response"""
    
    return create_error_response(
        PostgresError(
            message=f"A record with {field} '{value}' already exists",
            error_type=PostgresErrorType.UNIQUE_VIOLATION,
            context={"field": field, "value": str(value)}
        ),
        status_code=409  # Conflict
    )