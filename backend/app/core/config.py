from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Media Translation API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8001",
        "http://localhost:8094",
        "http://localhost:19006", 
        "exp://localhost:19000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:19006",
        "*",  # Allow all origins for development
    ]
    
    # Allow CORS_ORIGINS from environment (will be parsed)
    CORS_ORIGINS: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql://admin:dev123456@localhost:5432/ai_media_translation"
    REDIS_URL: str = "redis://:dev123456@localhost:6379"
    
    # PostgreSQL Connection Settings (for compatibility with existing configs)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_media_translation"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "dev123456"
    
    # PostgreSQL Connection Pool Settings
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MIN_CONNECTIONS: int = 2
    DATABASE_COMMAND_TIMEOUT: int = 60
    
    # JWT
    JWT_SECRET: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_REFRESH_SECRET: str = "your-super-secret-refresh-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours for development (was 15 minutes)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_AUDIO_SIZE: int = 50 * 1024 * 1024   # 50MB
    MAX_VIDEO_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_TYPES: List[str] = [
        "audio/mpeg",      # MP3
        "audio/wav",       # WAV
        "audio/x-wav",     # WAV
        "audio/mp4",       # M4A
        "audio/ogg",       # OGG
        "audio/flac",      # FLAC
        "audio/aac"        # AAC
    ]
    ALLOWED_VIDEO_TYPES: List[str] = [
        "video/mp4",       # MP4
        "video/quicktime", # MOV
        "video/x-msvideo", # AVI
        "video/x-matroska", # MKV
        "video/webm"       # WebM
    ]
    
    # Speech-to-Text
    STT_PROVIDER: str = "openai"  # openai, deepseek_api, google, azure, ollama, mock
    OPENAI_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    FALLBACK_STT_PROVIDER: str = "mock"  # Fallback if provider fails
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Default Ollama server URL
    OLLAMA_MODEL: str = "deepseek-coder:6.7b-instruct"  # Default model for DeepSeek
    OLLAMA_TIMEOUT: int = 300  # seconds
    OLLAMA_MAX_TOKENS: int = 4096  # Maximum tokens to generate
    
    # Translation
    TRANSLATION_PROVIDER: str = "google"  # google, deepl, mock
    GOOGLE_TRANSLATE_API_KEY: Optional[str] = None
    DEEPL_API_KEY: Optional[str] = None
    FALLBACK_TRANSLATION_PROVIDER: str = "mock"
    
    # User Quotas
    GUEST_DAILY_LIMIT: int = 3
    FREE_DAILY_LIMIT: int = 10
    PREMIUM_DAILY_LIMIT: int = 1000
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Processing
    MAX_CONCURRENT_JOBS: int = 3
    JOB_TIMEOUT_MINUTES: int = 30
    
    class Config:
        env_file = ".env.local"  # Prioritize local development config
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables (for migration compatibility)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse CORS_ORIGINS from environment if provided
        if self.CORS_ORIGINS:
            try:
                import json
                parsed_origins = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed_origins, list):
                    self.ALLOWED_ORIGINS = parsed_origins
            except (json.JSONDecodeError, TypeError):
                # Fallback: split by comma if JSON parsing fails
                self.ALLOWED_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        
        # Create directories if they don't exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.TEMP_DIR).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()