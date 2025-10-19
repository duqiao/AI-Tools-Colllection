# FastAPI Application Entry Point

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.v1 import auth, translation, users, subscription, quota
from app.api.v1 import auth as auth_router
from app.api.v1 import translation as translation_router
from app.api.v1 import users as users_router
from app.api.v1 import subscription as subscription_router
from app.api.v1 import quota as quota_router
from app.core.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting WeChat Media Translator API")
    yield
    # Shutdown
    logger.info("Shutting down WeChat Media Translator API")

# Create FastAPI app
app = FastAPI(
    title="WeChat Media Translator API",
    description="API for WeChat Mini-Program Media Translation Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware for WeChat mini-program development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth_router.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    translation_router.router,
    prefix="/api/v1/translation", 
    tags=["translation"]
)

app.include_router(
    users_router.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    subscription_router.router,
    prefix="/api/v1/subscription",
    tags=["subscription"]
)

app.include_router(
    quota_router.router,
    prefix="/api/v1/quota",
    tags=["quota"]
)

@app.get("/")
async def root():
    """Root endpoint for API health check"""
    return {
        "message": "WeChat Media Translator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )