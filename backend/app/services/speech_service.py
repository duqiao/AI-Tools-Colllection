"""
Speech recognition service for processing audio transcriptions.

This module provides integration with speech recognition providers
including Alibaba Cloud and Tencent Cloud services.
"""

import json
import time
from typing import Dict, Any, Optional, List
from enum import Enum
import requests
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SpeechProvider(Enum):
    """Speech recognition provider options."""
    ALIBABA = "alibaba"
    TENCENT = "tencent"


class SpeechService:
    """Service for speech recognition operations."""
    
    def __init__(self):
        self.alibaba_config = {
            "access_key_id": settings.alibaba_cloud_access_key_id,
            "access_key_secret": settings.alibaba_cloud_access_key_secret,
            "endpoint": "nls-meta.cn-shanghai.aliyuncs.com",
            "app_key": settings.alibaba_app_key
        }
        
        self.tencent_config = {
            "secret_id": settings.tencent_cloud_secret_id,
            "secret_key": settings.tencent_cloud_secret_key,
            "endpoint": "asr.tencentcloudapi.com",
            "region": "ap-beijing"
        }
    
    async def transcribe_audio_file(
        self,
        audio_url: str,
        file_type: str = "audio",
        language: str = "zh-CN",
        provider: SpeechProvider = SpeechProvider.ALIBABA
    ) -> Dict[str, Any]:
        """Transcribe audio file using specified provider."""
        
        try:
            if provider == SpeechProvider.ALIBABA:
                return await self._transcribe_with_alibaba(audio_url, file_type, language)
            elif provider == SpeechProvider.TENCENT:
                return await self._transcribe_with_tencent(audio_url, file_type, language)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Speech transcription failed with {provider.value}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider.value
            }
    
    async def _transcribe_with_alibaba(
        self,
        audio_url: str,
        file_type: str,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using Alibaba Cloud Speech Recognition."""
        
        # Mock implementation - in production, integrate with actual Alibaba Cloud API
        logger.info(f"Starting Alibaba Cloud transcription for: {audio_url}")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Mock response
        mock_result = {
            "success": True,
            "provider": "alibaba",
            "text": "这是阿里巴巴云语音识别的模拟转录结果。",
            "confidence": 0.95,
            "word_count": 15,
            "duration": 3.5,
            "processing_time": 2.1,
            "request_id": f"alibaba-{int(time.time())}",
            "cost": 0.05
        }
        
        logger.info(f"Alibaba Cloud transcription completed: {mock_result['request_id']}")
        return mock_result
    
    async def _transcribe_with_tencent(
        self,
        audio_url: str,
        file_type: str,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using Tencent Cloud Speech Recognition."""
        
        # Mock implementation - in production, integrate with actual Tencent Cloud API
        logger.info(f"Starting Tencent Cloud transcription for: {audio_url}")
        
        # Simulate processing time
        await asyncio.sleep(1.8)
        
        # Mock response
        mock_result = {
            "success": True,
            "provider": "tencent",
            "text": "这是腾讯云语音识别的模拟转录结果。",
            "confidence": 0.93,
            "word_count": 14,
            "duration": 3.2,
            "processing_time": 1.8,
            "request_id": f"tencent-{int(time.time())}",
            "cost": 0.045
        }
        
        logger.info(f"Tencent Cloud transcription completed: {mock_result['request_id']}")
        return mock_result
    
    def get_supported_formats(self, provider: SpeechProvider) -> List[str]:
        """Get supported audio formats for provider."""
        
        formats = {
            SpeechProvider.ALIBABA: [
                "wav", "mp3", "aac", "m4a", "flac", "ogg", "opus"
            ],
            SpeechProvider.TENCENT: [
                "wav", "mp3", "m4a", "flac", "ogg", "amr", "speex"
            ]
        }
        
        return formats.get(provider, [])
    
    def get_supported_languages(self, provider: SpeechProvider) -> List[str]:
        """Get supported languages for provider."""
        
        languages = {
            SpeechProvider.ALIBABA: [
                "zh-CN", "zh-TW", "en-US", "ja-JP", "ko-KR", "th-TH", "vi-VN"
            ],
            SpeechProvider.TENCENT: [
                "zh-CN", "zh-TW", "en-US", "ja-JP", "ko-KR", "th-TH", "vi-VN", "id-ID"
            ]
        }
        
        return languages.get(provider, [])
    
    def estimate_cost(
        self,
        duration_seconds: float,
        provider: SpeechProvider
    ) -> float:
        """Estimate transcription cost based on duration."""
        
        # Pricing per minute (mock values)
        pricing = {
            SpeechProvider.ALIBABA: 0.05,  # $0.05 per minute
            SpeechProvider.TENCENT: 0.045  # $0.045 per minute
        }
        
        price_per_minute = pricing.get(provider, 0.05)
        duration_minutes = duration_seconds / 60.0
        
        return round(price_per_minute * duration_minutes, 4)
    
    def validate_audio_file(
        self,
        file_size: int,
        file_type: str,
        duration_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """Validate audio file meets requirements."""
        
        # File size limits (60MB max)
        max_size = 60 * 1024 * 1024  # 60MB in bytes
        min_size = 1024  # 1KB minimum
        
        # Duration limits (5 hours max)
        max_duration = 5 * 60 * 60  # 5 hours in seconds
        min_duration = 0.5  # 0.5 seconds minimum
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check file size
        if file_size < min_size:
            validation_result["valid"] = False
            validation_result["errors"].append("File too small (minimum 1KB)")
        elif file_size > max_size:
            validation_result["valid"] = False
            validation_result["errors"].append("File too large (maximum 60MB)")
        
        # Check duration if available
        if duration_seconds is not None:
            if duration_seconds < min_duration:
                validation_result["valid"] = False
                validation_result["errors"].append("Audio too short (minimum 0.5 seconds)")
            elif duration_seconds > max_duration:
                validation_result["valid"] = False
                validation_result["errors"].append("Audio too long (maximum 5 hours)")
        
        # Check supported file types
        supported_types = ["audio", "video", "wechat_video"]
        if file_type not in supported_types:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Unsupported file type: {file_type}")
        
        return validation_result
    
    def get_optimal_provider(
        self,
        language: str = "zh-CN",
        duration_seconds: Optional[float] = None,
        quality_requirement: str = "standard"
    ) -> SpeechProvider:
        """Select optimal provider based on requirements."""
        
        # For Chinese language, Alibaba Cloud generally has better accuracy
        if language.startswith("zh-"):
            if quality_requirement == "high":
                return SpeechProvider.ALIBABA
            else:
                # For shorter files, Tencent is faster and cheaper
                if duration_seconds and duration_seconds < 60:
                    return SpeechProvider.TENCENT
                else:
                    return SpeechProvider.ALIBABA
        
        # For other languages, use Alibaba Cloud as default
        return SpeechProvider.ALIBABA
    
    async def batch_transcribe(
        self,
        audio_urls: List[str],
        provider: SpeechProvider = SpeechProvider.ALIBABA,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Transcribe multiple audio files concurrently."""
        
        import asyncio
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def transcribe_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.transcribe_audio_file(url, provider=provider)
        
        tasks = [transcribe_with_semaphore(url) for url in audio_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "url": audio_urls[i],
                    "provider": provider.value
                })
            else:
                processed_results.append(result)
        
        return processed_results


# Import asyncio for async operations
import asyncio