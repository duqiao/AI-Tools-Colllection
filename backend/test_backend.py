#!/usr/bin/env python3
"""
Simple test to verify backend functionality
"""

import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    print("🔍 Testing backend imports...")
    
    # Test core imports
    from app.main import app
    print("✅ FastAPI app import: SUCCESS")
    
    from app.core.config import settings
    print(f"✅ Config loaded: {settings.APP_NAME}")
    
    from app.models.schemas import User, MediaFile, ProcessingJob
    print("✅ Pydantic models import: SUCCESS")
    
    from app.services.speech_to_text import get_speech_to_text_service
    stt_service = get_speech_to_text_service()
    print(f"✅ Speech-to-text service: {type(stt_service).__name__}")
    
    from app.core.database import Database
    print("✅ Database service import: SUCCESS")
    
    # Test service functionality
    model_info = stt_service.get_model_info() if hasattr(stt_service, 'get_model_info') else {"provider": "unknown"}
    print(f"✅ STT Model info: {model_info}")
    
    print("\n🎉 Backend system is ready!")
    print("\n📋 Next steps:")
    print("1. Install missing dependencies: pip install fastapi uvicorn aiofiles python-dotenv")
    print("2. Test file upload: curl -X POST http://localhost:8000/api/v1/upload/ -F 'file=@test.mp3'")
    print("3. Start server: python run.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Solution: Install missing dependencies")
    print("pip install fastapi uvicorn pydantic-settings aiofiles python-dotenv")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Check configuration and dependencies")