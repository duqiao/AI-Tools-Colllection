import whisper
import torch
import librosa
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
# from app.services.ollama_stt import OllamaSpeechToTextService  # Using OpenAI Whisper instead
from app.core.redis import set_progress

# Fallback services when main providers are not available
class MockSpeechToTextService:
    """Mock speech-to-text service for development/testing"""
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.warning(f"Using mock transcription for: {audio_path}")
        
        # Simple mock transcription
        mock_text = f"[Mock transcription] Audio file processed: {Path(audio_path).name}"
        
        return {
            "full_text": mock_text,
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": mock_text,
                    "confidence": 0.8
                }
            ],
            "language": options.get("language", "unknown"),
            "confidence": 0.8,
            "metadata": {
                "audio_duration": 30.0,
                "provider": "mock",
                "model": "mock_model",
                "processing_method": "mock_transcription"
            }
        }
    
    def get_supported_languages(self) -> list:
        return ["en", "zh", "es", "fr", "de"]
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "model": "mock",
            "configured": True,
            "supported_languages": self.get_supported_languages()
        }

class OpenAIWhisperService:
    """Fallback Whisper service if OpenAI not available"""
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.warning("OpenAI Whisper not configured, using Whisper locally")
        return await WhisperService().transcribe(audio_path, options)

class GoogleSpeechToTextService:
    """Fallback Google service if Google API not available"""
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.warning("Google Translate API not configured, using basic translation")
        return await MockSpeechToTextService().transcribe(audio_path, options)

class SpeechToTextService:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Speech-to-Text using device: {self.device}")
    
    async def load_model(self):
        """Load Whisper model asynchronously"""
        if self.model is None:
            try:
                # Load model in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None, 
                    whisper.load_model, 
                    settings.WHISPER_MODEL,
                    self.device
                )
                logger.info(f"Whisper model '{settings.WHISPER_MODEL}' loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe audio file to text using Whisper
        
        Args:
            audio_path: Path to audio file
            options: Transcription options
                - language: Source language code (auto-detect if None)
                - enable_timestamps: Boolean, include timestamps
                - enable_speaker_diarization: Boolean, identify speakers
        
        Returns:
            Dictionary containing transcription results
        """
        try:
            await self.load_model()
            
            if options is None:
                options = {}
            
            # Prepare transcription options
            whisper_options = {
                "task": "transcribe",
                "language": options.get("language"),
                "fp16": self.device == "cuda",
                "verbose": False
            }
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio_path,
                whisper_options,
                options.get("enable_timestamps", True)
            )
            
            # Format result
            return {
                "full_text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown"),
                "confidence": self._calculate_confidence(result),
                "metadata": {
                    "audio_duration": self._get_audio_duration(audio_path),
                    "word_count": len(result["text"].split()),
                    "provider": "whisper",
                    "model": settings.WHISPER_MODEL
                }
            }
            
        except Exception as e:
            logger.error(f"Speech-to-text transcription failed: {e}")
            raise
    
    def _transcribe_sync(self, audio_path: str, whisper_options: Dict, enable_timestamps: bool):
        """Synchronous transcription using Whisper"""
        try:
            result = self.model.transcribe(audio_path, **whisper_options)
            
            if not enable_timestamps:
                # Remove segments if timestamps disabled
                result["segments"] = []
            
            return result
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise
    
    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate overall confidence from Whisper result"""
        segments = result.get("segments", [])
        if not segments:
            return 0.0
        
        # Whisper doesn't provide per-segment confidence, so estimate based on avg logprob
        avg_logprob = result.get("avg_logprob", -1.0)
        # Convert logprob to approximate confidence (0-1 scale)
        confidence = max(0.0, min(1.0, (avg_logprob + 2.0) / 4.0))
        
        return confidence
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration"""
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            logger.warning(f"Failed to get audio duration: {e}")
            return 0.0
    
    async def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        # Whisper supports these languages
        return [
            "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru",
            "ar", "hi", "th", "vi", "tr", "pl", "nl", "sv", "da", "no",
            "fi", "he", "cs", "hu", "ro", "bg", "hr", "sk", "sl", "et",
            "lv", "lt", "mt", "cy", "ga", "eu", "ca", "gl", "is"
        ]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "openai",
            "model": settings.WHISPER_MODEL,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "supported_languages": self.get_supported_languages()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.model:
            # Clear model from memory
            del self.model
            self.model = None
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Whisper model cleaned up")

# Alternative STT service using Google Speech-to-Text
class GoogleSpeechToTextService:
    def __init__(self):
        self.api_key = settings.GOOGLE_SPEECH_API_KEY
        if not self.api_key:
            logger.warning("Google Speech API key not configured")
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transcribe using Google Speech-to-Text API"""
        if not self.api_key:
            # Fallback to Whisper
            whisper_service = SpeechToTextService()
            return await whisper_service.transcribe(audio_path, options)
        
        # TODO: Implement Google Speech-to-Text API
        # For now, fallback to Whisper
        logger.info("Google Speech-to-Text not implemented, falling back to Whisper")
        whisper_service = SpeechToTextService()
        return await whisper_service.transcribe(audio_path, options)

# Main service factory
def get_speech_to_text_service():
    """Get the configured speech-to-text service"""
    provider = settings.STT_PROVIDER.lower()
    
    if provider == "openai":
        return OpenAIWhisperService()
    elif provider == "google":
        return GoogleSpeechToTextService()
    elif provider == "mock":
        return MockSpeechToTextService()
    else:  # Default to OpenAI Whisper
        return OpenAIWhisperService()