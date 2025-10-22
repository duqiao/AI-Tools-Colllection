#!/usr/bin/env python3
"""
Configuration Test Script
Tests if the backend configuration is working correctly
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    print("🔍 Testing Configuration...")
    print("=" * 40)
    
    # Import settings
    from app.core.config import settings
    
    print(f"✅ Configuration loaded successfully!")
    print(f"   App: {settings.APP_NAME} v{settings.VERSION}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Host: {settings.HOST}:{settings.PORT}")
    print(f"   MongoDB URI: {settings.MONGODB_URI}")
    print(f"   Redis URL: {settings.REDIS_URL}")
    print(f"   CORS Origins: {settings.ALLOWED_ORIGINS}")
    print(f"   Upload Dir: {settings.UPLOAD_DIR}")
    print(f"   Ollama Model: {settings.OLLAMA_MODEL}")
    
    print("\n🎉 Configuration test passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the project root directory")
    sys.exit(1)
except Exception as e:
    print(f"❌ Configuration error: {e}")
    sys.exit(1)