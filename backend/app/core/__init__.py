"""
Application initialization utilities

This module provides initialization functions for the FastAPI application.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)


def create_app_directories():
    """Create necessary directories for the application."""
    import os
    
    directories = [
        "uploads",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def validate_configuration():
    """Validate that required configuration is present."""
    from app.core.config import settings
    
    required_fields = [
        "secret_key",
        "database_url"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field):
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"Missing required configuration: {missing_fields}")
        raise ValueError(f"Missing required configuration: {missing_fields}")
    
    logger.info("Configuration validation passed")