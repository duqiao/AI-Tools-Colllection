import asyncio
import aiohttp
import logging
import json
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.services.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)

class DeepSeekAPIService:
    """DeepSeek API speech-to-text service"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-audio"  # 根据实际模型名称调整
        self.audio_processor = AudioProcessor()
        self.client = None
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured")
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized"""
        if self.client is None:
            self.client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=300)
            )
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to DeepSeek API"""
        await self._ensure_client()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.client.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except asyncio.TimeoutError:
            logger.error("DeepSeek API request timed out")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"DeepSeek API request error: {e}")
            return {"error": str(e)}
    
    async def _prepare_audio_file(self, audio_path: str) -> str:
        """
        Prepare audio file for DeepSeek API
        Convert to optimal format if needed
        """
        try:
            audio_file_path = Path(audio_path)
            
            # DeepSeek API typically supports WAV, MP3, M4A, FLAC
            supported_formats = ['.wav', '.mp3', '.m4a', '.flac']
            
            if audio_file_path.suffix.lower() in supported_formats:
                # Check if audio is in optimal format (16kHz mono)
                if (audio_file_path.suffix.lower() == '.wav' and 
                    await self.audio_processor._is_optimal_wav_format(audio_path)):
                    return audio_path
            
            # Convert to optimal WAV format
            logger.info(f"Converting audio to optimal format: {audio_path}")
            converted_path = await self._convert_to_optimal_format(audio_path)
            return converted_path
            
        except Exception as e:
            logger.warning(f"Audio preparation failed, using original: {e}")
            return audio_path
    
    async def _convert_to_optimal_format(self, audio_path: str) -> str:
        """Convert audio to optimal format for DeepSeek API"""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_filename = f"deepseek_audio_{int(asyncio.get_event_loop().time())}.wav"
            temp_audio_path = os.path.join(temp_dir, temp_filename)
            
            # Use FFmpeg to convert to optimal format
            cmd = [
                'ffmpeg',
                '-i', audio_path,
                '-ar', '16000',  # Sample rate
                '-ac', '1',      # Mono
                '-c:a', 'pcm_s16le',  # 16-bit PCM
                '-y',            # Overwrite
                temp_audio_path
            ]
            
            # Run FFmpeg in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._run_ffmpeg, cmd)
            
            if not os.path.exists(temp_audio_path):
                raise Exception("Audio conversion failed - no output file created")
            
            return temp_audio_path
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            raise
    
    def _run_ffmpeg(self, cmd: list):
        """Run FFmpeg command synchronously"""
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown FFmpeg error"
                raise Exception(f"FFmpeg error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg process timed out")
        except Exception as e:
            raise Exception(f"FFmpeg execution failed: {e}")
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe audio using DeepSeek API
        
        Args:
            audio_path: Path to audio file
            options: Transcription options
                - language: Language code (auto-detect if None)
                - enable_timestamps: Include timestamps
                - enable_speaker_diarization: Identify speakers
        
        Returns:
            Dictionary containing transcription results
        """
        try:
            if not self.api_key:
                raise Exception("DeepSeek API key not configured")
            
            logger.info(f"Starting DeepSeek API transcription for: {audio_path}")
            
            # Prepare audio file
            prepared_audio_path = await self._prepare_audio_file(audio_path)
            
            # Prepare transcription parameters
            language = options.get("language", "auto") if options else "auto"
            
            # Use multipart form data for file upload
            data = aiohttp.FormData()
            data.add_field('model', self.model)
            data.add_field('language', language)
            data.add_field('response_format', 'json')
            
            if options and options.get("enable_timestamps"):
                data.add_field('timestamp_granularities[]', 'word')
            
            # Add audio file
            with open(prepared_audio_path, 'rb') as audio_file:
                data.add_field('file', audio_file, 
                             filename=Path(prepared_audio_path).name,
                             content_type='audio/wav')
                
                # Make API request
                result = await self._make_request_with_form('/audio/transcriptions', data)
            
            # Clean up temporary file if we created one
            if prepared_audio_path != audio_path and Path(prepared_audio_path).exists():
                try:
                    Path(prepared_audio_path).unlink()
                    logger.debug(f"Cleaned up temporary file: {prepared_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
            
            if "error" in result:
                raise Exception(f"DeepSeek API error: {result['error']}")
            
            # Format response
            transcription_result = self._format_transcription_result(result, audio_path, options)
            
            logger.info(f"DeepSeek API transcription completed successfully")
            return transcription_result
            
        except Exception as e:
            logger.error(f"DeepSeek API transcription failed: {e}")
            raise
    
    async def _make_request_with_form(self, endpoint: str, data: aiohttp.FormData) -> Dict[str, Any]:
        """Make multipart form request to DeepSeek API"""
        await self._ensure_client()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with self.client.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API error: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"DeepSeek API request error: {e}")
            return {"error": str(e)}
    
    def _format_transcription_result(self, api_result: Dict[str, Any], audio_path: str, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Format DeepSeek API response to standard format"""
        try:
            # Extract text from API response
            text = api_result.get("text", "")
            
            # Extract segments if available
            segments = api_result.get("segments", [])
            if not segments and text:
                # Create simple segment if no segments provided
                segments = [{
                    "start": 0.0,
                    "end": 30.0,  # Default duration
                    "text": text,
                    "confidence": 0.8
                }]
            
            # Extract language
            language = api_result.get("language", "auto-detected")
            
            # Calculate confidence
            confidence = api_result.get("confidence", 0.8)
            
            return {
                "full_text": text,
                "segments": segments,
                "language": language,
                "confidence": confidence,
                "metadata": {
                    "provider": "deepseek_api",
                    "model": self.model,
                    "processing_method": "deepseek_api_transcription",
                    "original_file": str(audio_path),
                    "api_response": api_result
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to format transcription result: {e}")
            return {
                "full_text": str(api_result),
                "segments": [],
                "language": "unknown",
                "confidence": 0.5,
                "metadata": {
                    "provider": "deepseek_api",
                    "model": self.model,
                    "processing_method": "deepseek_api_transcription",
                    "original_file": str(audio_path),
                    "error": str(e)
                }
            }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about DeepSeek API model"""
        return {
            "provider": "deepseek_api",
            "model": self.model,
            "base_url": self.base_url,
            "configured": bool(self.api_key),
            "supported_languages": [
                "en", "zh", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
                "ar", "hi", "th", "vi", "id", "ms", "tl", "sw", "nl", "sv",
                "no", "da", "fi", "pl", "cs", "sk", "hu", "ro", "bg", "hr"
            ],
            "features": [
                "speech_to_text",
                "multi_language",
                "timestamp_generation",
                "word_level_timestamps",
                "audio_format_conversion"
            ]
        }
    
    async def test_connection(self) -> bool:
        """Test DeepSeek API connection"""
        try:
            if not self.api_key:
                return False
            
            # Test with a simple API call
            result = await self._make_request("GET", "/models")
            
            return "error" not in result
            
        except Exception as e:
            logger.error(f"DeepSeek API connection test failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.close()
            self.client = None

class DeepSeekAPISpeechToTextService:
    """High-level DeepSeek API speech-to-text service with video support"""
    
    def __init__(self):
        self.deepseek_service = DeepSeekAPIService()
        self.audio_processor = AudioProcessor()
        
        logger.info("DeepSeek API Speech-to-Text service initialized")
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe audio/video file using DeepSeek API
        
        Process:
        1. Handle video files by extracting audio first
        2. Convert audio to optimal format for DeepSeek API
        3. Send to DeepSeek API for transcription
        4. Parse and format results
        """
        try:
            logger.info(f"Starting DeepSeek API transcription for: {audio_path}")
            
            # Handle video files - extract audio first
            file_path = Path(audio_path)
            processed_audio_path = audio_path
            
            if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                logger.info("Video file detected, extracting audio...")
                processed_audio_path = await self.audio_processor.extract_audio(audio_path)
                logger.info(f"Audio extracted to: {processed_audio_path}")
            
            # Get file information for metadata
            try:
                media_info = await self.audio_processor.get_media_info(processed_audio_path)
                logger.info(f"Media info: duration={media_info.get('duration', 0):.2f}s, size={media_info.get('size', 0)} bytes")
            except Exception as e:
                logger.warning(f"Could not get media info: {e}")
                media_info = {}
            
            # Transcribe using DeepSeek API
            transcription_result = await self.deepseek_service.transcribe(
                processed_audio_path, 
                options
            )
            
            # Enhance metadata
            transcription_result["metadata"].update({
                "file_info": {
                    "original_path": audio_path,
                    "processed_path": processed_audio_path,
                    "file_type": "video" if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm'] else "audio",
                    "media_duration": media_info.get('duration', 0),
                    "file_size": media_info.get('size', 0)
                }
            })
            
            # Clean up extracted audio if it's a video
            if processed_audio_path != audio_path and Path(processed_audio_path).exists():
                try:
                    Path(processed_audio_path).unlink()
                    logger.info(f"Cleaned up extracted audio: {processed_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up extracted audio: {e}")
            
            logger.info(f"DeepSeek API transcription completed successfully")
            return transcription_result
            
        except Exception as e:
            logger.error(f"DeepSeek API transcription failed: {e}")
            raise
    
    def get_supported_languages(self) -> list:
        """Get languages supported by DeepSeek API"""
        return [
            "en", "zh", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
            "ar", "hi", "th", "vi", "id", "ms", "tl", "sw", "nl", "sv",
            "no", "da", "fi", "pl", "cs", "sk", "hu", "ro", "bg", "hr"
        ]
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get DeepSeek API model information"""
        model_info = await self.deepseek_service.get_model_info()
        model_info.update({
            "features": [
                "speech_to_text",
                "multi_language",
                "timestamp_generation",
                "word_level_timestamps",
                "video_audio_extraction",
                "audio_format_conversion"
            ]
        })
        return model_info
    
    async def test_connection(self) -> bool:
        """Test DeepSeek API service connection"""
        return await self.deepseek_service.test_connection()
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.deepseek_service.cleanup()