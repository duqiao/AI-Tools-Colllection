import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Optional imports that might cause issues on some systems
try:
    import whisper
    import torch
    import librosa
    WHISPER_AVAILABLE = True
except (ImportError, TypeError, OSError) as e:
    logging.warning(f"Whisper not available: {e}")
    WHISPER_AVAILABLE = False

from app.core.config import settings
from app.services.ollama_stt import OllamaSpeechToTextService
from app.services.deepseek_api_stt import DeepSeekAPISpeechToTextService
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
    """OpenAI Whisper service"""
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper not available, using mock service")
            return await MockSpeechToTextService().transcribe(audio_path, options)
        
        try:
            logger.info("Using local Whisper service")
            return await WhisperService().transcribe(audio_path, options)
        except Exception as e:
            logger.error(f"Whisper service failed: {e}")
            return await MockSpeechToTextService().transcribe(audio_path, options)

class GoogleSpeechToTextService:
    """Fallback Google service if Google API not available"""
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        logger.warning("Google Translate API not configured, using basic translation")
        return await MockSpeechToTextService().transcribe(audio_path, options)

class DeepSeekSpeechToTextService:
    """DeepSeek-based speech-to-text service using Ollama"""
    
    def __init__(self):
        self.ollama_service = OllamaSpeechToTextService()
        self.audio_processor = None
        # Import AudioProcessor only when needed
        from app.services.audio_processor import AudioProcessor
        self.audio_processor = AudioProcessor()
        
        logger.info("DeepSeek Speech-to-Text service initialized")
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe audio/video file using DeepSeek via Ollama
        
        Process:
        1. Handle video files by extracting audio first
        2. Convert audio to optimal format for Ollama
        3. Send to DeepSeek model for transcription
        4. Parse and format results
        """
        try:
            logger.info(f"Starting DeepSeek transcription for: {audio_path}")
            
            # Initialize Ollama service
            await self.ollama_service.initialize()
            
            # Handle video files - extract audio first
            file_path = Path(audio_path)
            processed_audio_path = audio_path
            
            if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                logger.info("Video file detected, extracting audio...")
                processed_audio_path = await self.audio_processor.extract_audio(audio_path)
                logger.info(f"Audio extracted to: {processed_audio_path}")
            
            # Prepare transcription options
            transcription_options = {
                "language": options.get("language") if options else None,
                "enable_timestamps": options.get("enable_timestamps", True) if options else True,
                "enable_speaker_diarization": options.get("enable_speaker_diarization", True) if options else True
            }
            
            # Get file information for metadata
            try:
                media_info = await self.audio_processor.get_media_info(processed_audio_path)
                logger.info(f"Media info: duration={media_info.get('duration', 0):.2f}s, size={media_info.get('size', 0)} bytes")
            except Exception as e:
                logger.warning(f"Could not get media info: {e}")
                media_info = {}
            
            # Transcribe using DeepSeek via Ollama
            transcription_result = await self.ollama_service.transcribe(
                processed_audio_path, 
                transcription_options
            )
            
            # Enhance metadata with DeepSeek-specific information
            transcription_result["metadata"].update({
                "provider": "deepseek_ollama",
                "model": settings.OLLAMA_MODEL,
                "processing_method": "deepseek_speech_to_text",
                "file_info": {
                    "original_path": audio_path,
                    "processed_path": processed_audio_path,
                    "file_type": "video" if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm'] else "audio",
                    "media_duration": media_info.get('duration', 0),
                    "file_size": media_info.get('size', 0)
                }
            })
            
            logger.info(f"DeepSeek transcription completed successfully")
            return transcription_result
            
        except Exception as e:
            logger.error(f"DeepSeek transcription failed: {e}")
            raise
    
    def get_supported_languages(self) -> list:
        """Get languages supported by DeepSeek models"""
        return [
            "en", "zh", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
            "ar", "hi", "th", "vi", "id", "ms", "tl", "sw", "nl", "sv",
            "no", "da", "fi", "pl", "cs", "sk", "hu", "ro", "bg", "hr",
            "sr", "sl", "et", "lv", "lt", "uk", "be", "el", "tr", "he",
            "fa", "ur", "bn", "ta", "te", "ml", "kn", "gu", "pa", "mr"
        ]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get DeepSeek model information"""
        return {
            "provider": "deepseek_ollama",
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
            "configured": True,
            "supported_languages": self.get_supported_languages(),
            "features": [
                "speech_to_text",
                "multi_language",
                "speaker_diarization",
                "timestamp_generation",
                "video_audio_extraction",
                "technical_content_transcription"
            ]
        }
    
    async def test_connection(self) -> bool:
        """Test DeepSeek service connection"""
        try:
            # Test Ollama connection
            if not await self.ollama_service.test_connection():
                return False
            
            # Check if DeepSeek model is available
            model_info = await self.ollama_service.get_model_info()
            return model_info.get("available", False)
            
        except Exception as e:
            logger.error(f"DeepSeek service test failed: {e}")
            return False

class SpeechToTextService:
    def __init__(self):
        if not WHISPER_AVAILABLE:
            logger.error("Whisper is not available on this system")
            raise ImportError("Whisper is not available")
        
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Speech-to-Text using device: {self.device}")
    
    async def load_model(self):
        """Load Whisper model asynchronously"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper is not available")
            
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

class DeepSeekAPIService:
    """DeepSeek API service wrapper for compatibility"""
    
    def __init__(self):
        self.api_service = DeepSeekAPISpeechToTextService()
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self.api_service.transcribe(audio_path, options)
    
    def get_supported_languages(self) -> list:
        return self.api_service.get_supported_languages()
    
    async def get_model_info(self) -> Dict[str, Any]:
        return await self.api_service.get_model_info()
    
    async def test_connection(self) -> bool:
        return await self.api_service.test_connection()

# Main service factory
def get_speech_to_text_service():
    """Get the configured speech-to-text service"""
    provider = settings.STT_PROVIDER.lower()
    
    if provider == "openai":
        return OpenAIWhisperService()
    elif provider == "deepseek_api":
        return DeepSeekAPIService()
    elif provider == "ollama":
        return DeepSeekSpeechToTextService()
    elif provider == "google":
        return GoogleSpeechToTextService()
    elif provider == "mock":
        return MockSpeechToTextService()
    else:  # Default to OpenAI Whisper
        return OpenAIWhisperService()