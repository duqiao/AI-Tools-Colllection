"""
Logging Configuration

This module sets up structured logging for the FastAPI application.
"""

import logging
import structlog
import sys
from pathlib import Path

from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging with console and file output."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format=settings.log_format,
        level=getattr(logging, settings.log_level),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log")
        ]
    )
    
    # Configure loggers for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger for the given name."""
    return structlog.get_logger(name)