#!/usr/bin/env python3
"""
AI Media Translation Backend - FastAPI Server
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

if __name__ == "__main__":
    from app.main import app
    from app.core.config import settings
    
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.DEBUG and 'Development' or 'Production'}")
    print(f"Server will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"Health Check: http://{settings.HOST}:{settings.PORT}/health")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug",  # Changed from "info" to "debug"
        access_log=True,
        use_colors=True,
        workers=1
    )