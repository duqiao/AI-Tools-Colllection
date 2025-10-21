from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from app.core.config import settings
from app.core.database import init_db
from app.core.redis import init_redis
from app.api import auth, upload, translation, users, health
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = setup_logging().getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Media Translation API...")
    
    # Initialize database (optional)
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed, continuing without database: {e}")
    
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
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Media Translation API...")

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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
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

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "success": True,
        "message": "AI Media Translation API is running",
        "version": "1.0.0",
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