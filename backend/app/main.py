from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path
import time
import logging

# Setup request logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.postgres_db import init_db
from app.core.redis import init_redis
from app.api import auth, upload, translation, users, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Media Translation API...")
    
    # Initialize PostgreSQL database
    try:
        await init_db()
        logger.info("PostgreSQL database initialized with connection pooling")
    except Exception as e:
        logger.error(f"PostgreSQL database initialization failed: {e}")
        # In production, you might want to exit if database initialization fails
        # For now, we'll continue and let individual endpoints handle database errors
    
    # Initialize Redis (optional)
    try:
        await init_redis()
        logger.info("Redis initialized")
    except Exception as e:
        logger.warning(f"Redis initialization failed, continuing without Redis: {e}")
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ready: {upload_dir}")
    
    # Log database connection info (without credentials)
    logger.info(f"Database backend: PostgreSQL")
    logger.info(f"Database host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"Database name: {settings.POSTGRES_DB}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Media Translation API...")
    logger.info("Closing PostgreSQL connection pools...")

# Create FastAPI app
app = FastAPI(
    title="AI Media Translation API",
    description="Backend API for AI-powered media translation with video/audio recognition",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request details
    logger.info(f"📥 {request.method} {request.url}")
    logger.info(f"📋 Headers: {dict(request.headers)}")
    
    # Handle request
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    logger.info(f"📤 Response: {response.status_code} - {process_time:.4f}s")
    
    return response

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Health"]
)

# Also include health endpoints at root level for compatibility
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    upload.router,
    prefix="/api/v1/upload",
    tags=["Upload"]
)

app.include_router(
    translation.router,
    prefix="/api/v1/translation",
    tags=["Translation"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"]
)

# Global OPTIONS handler for CORS preflight requests
@app.options("/{path:path}")
async def global_options_handler(path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        content={"message": "CORS preflight successful"}
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "success": True,
        "message": "AI Media Translation API is running",
        "version": "1.0.0",
        "database": "PostgreSQL",
        "features": [
            "Media file upload and processing",
            "Speech-to-text transcription", 
            "User authentication and management",
            "Usage tracking and analytics"
        ],
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "upload": "/api/v1/upload",
            "translation": "/api/v1/translation",
            "users": "/api/v1/users"
        },
        "documentation": "/docs" if settings.DEBUG else "https://your-api-domain.com/docs"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )