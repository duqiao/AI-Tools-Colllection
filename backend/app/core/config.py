"""
Core Configuration Settings

This module contains all configuration settings for the FastAPI application.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "WeChat Media Translator"
    debug: bool = False
    version: str = "1.0.0"
    
    # CORS
    cors_origins: List[str] = [
        "https://servicewechat.com",  # WeChat mini-program
        "http://localhost:3000",     # Development
        "http://127.0.0.1:3000"
    ]
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost/wechat_translator"
    database_echo: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # WeChat Configuration
    wechat_appid: str = ""
    wechat_secret: str = ""
    
    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_file_types: List[str] = ["mp3", "wav", "mp4", "mov", "avi", "webm"]
    
    # External APIs
    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    alibaba_cloud_region: str = "cn-beijing"
    
    tencent_cloud_secret_id: str = ""
    tencent_cloud_secret_key: str = ""
    tencent_cloud_region: str = "ap-beijing"
    
    # Performance
    max_concurrent_translations: int = 1000
    translation_timeout: int = 300  # 5 minutes
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()