import asyncio
import aiohttp
import logging
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.max_tokens = settings.OLLAMA_MAX_TOKENS
        self.client = None
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized"""
        if self.client is None:
            self.client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Ollama API"""
        await self._ensure_client()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.client.post(url, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Ollama request failed: {response.status}")
                    return {"error": f"HTTP {response.status}: {response.text}"}
        except asyncio.TimeoutError:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return {"error": f"Request timed out after {self.timeout}s"}
        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return {"error": str(e)}
    
    async def is_model_available(self) -> bool:
        """Check if the configured model is available"""
        try:
            await self._ensure_client()
            url = f"{self.base_url}/api/tags"
            
            async with self.client.get(url) as response:
                if response.status == 200:
                    tags_data = await response.json()
                    models = [tag.get("name", "") for tag in tags_data.get("models", [])]
                    return self.model in models
                else:
                    return False
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transcribe audio using Ollama with DeepSeek/Qwen model
        
        This method handles the complexity of converting audio to text by:
        1. Validating audio file format
        2. Converting audio to optimal format for Ollama
        3. Encoding audio file to base64
        4. Prompting the model with speech-to-text instructions
        5. Handling the response and extracting transcription
        """
        try:
            # Validate audio file
            audio_file_path = Path(audio_path)
            if not audio_file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            logger.info(f"Starting Ollama transcription for: {audio_path}")
            
            # Convert audio to WAV format if needed (Ollama works best with WAV)
            processed_audio_path = await self._prepare_audio_for_ollama(audio_path)
            
            # Read and encode processed audio file
            with open(processed_audio_path, "rb") as audio_file:
                audio_data = audio_file.read()
            
            # Encode to base64
            import base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Create transcription prompt
            prompt = self._create_transcription_prompt(options)
            
            # Prepare request
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "images": [{"data": audio_b64, "type": "audio/wav"}],
                "options": {
                    "temperature": 0.1,
                    "max_tokens": self.max_tokens,
                    "top_p": 0.9,
                    "top_k": 40
                },
                "stream": False
            }
            
            logger.info(f"Sending transcription request to Ollama for model: {self.model}")
            logger.info(f"Audio size: {len(audio_data)} bytes, Base64 size: {len(audio_b64)} chars")
            
            # Make request
            result = await self._make_request("/api/generate", request_data)
            
            if "error" in result:
                raise Exception(f"Ollama error: {result['error']}")
            
            # Extract transcription from response
            response_text = result.get("response", "")
            
            if not response_text:
                logger.warning("Empty response from Ollama")
                return self._create_empty_result(audio_path, options)
            
            logger.info(f"Ollama response received: {len(response_text)} chars")
            
            # Try to parse structured response
            transcription_result = self._parse_transcription_response(response_text, options)
            
            # Clean up temporary audio file if we created one
            if processed_audio_path != audio_path and Path(processed_audio_path).exists():
                try:
                    Path(processed_audio_path).unlink()
                    logger.debug(f"Cleaned up temporary audio file: {processed_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")
            
            # Add metadata
            transcription_result.update({
                "metadata": {
                    "audio_duration": await self._get_audio_duration(audio_path),
                    "provider": "ollama",
                    "model": self.model,
                    "processing_method": "ollama_speech_to_text",
                    "original_file": str(audio_path),
                    "file_size": len(audio_data)
                }
            })
            
            logger.info(f"Ollama transcription completed successfully")
            return transcription_result
            
        except Exception as e:
            logger.error(f"Ollama transcription failed: {e}")
            raise
    
    async def _prepare_audio_for_ollama(self, audio_path: str) -> str:
        """
        Prepare audio file for Ollama processing
        
        Ollama works best with WAV files at 16kHz mono
        """
        try:
            from app.services.audio_processor import AudioProcessor
            audio_processor = AudioProcessor()
            
            audio_file_path = Path(audio_path)
            
            # Check if already in optimal format
            if (audio_file_path.suffix.lower() == '.wav' and 
                await audio_processor._is_optimal_wav_format(audio_path)):
                return audio_path
            
            # Convert to optimal WAV format
            logger.info(f"Converting audio to optimal WAV format: {audio_path}")
            
            # Use AudioProcessor to convert (we'll add a helper method)
            optimal_audio_path = await self._convert_to_optimal_wav(audio_path, audio_processor)
            
            return optimal_audio_path
            
        except Exception as e:
            logger.warning(f"Audio preparation failed, using original: {e}")
            return audio_path
    
    async def _convert_to_optimal_wav(self, audio_path: str, audio_processor) -> str:
        """Convert audio to optimal WAV format for Ollama"""
        try:
            import tempfile
            import os
            
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_filename = f"ollama_audio_{int(time.time())}.wav"
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
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown FFmpeg error"
                raise Exception(f"FFmpeg error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg process timed out")
        except Exception as e:
            raise Exception(f"FFmpeg execution failed: {e}")
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get actual audio duration using AudioProcessor"""
        try:
            from app.services.audio_processor import AudioProcessor
            audio_processor = AudioProcessor()
            
            media_info = await audio_processor.get_media_info(audio_path)
            duration = media_info.get('duration', 0)
            
            return float(duration)
            
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return self._estimate_audio_duration(audio_path)
    
    def _create_empty_result(self, audio_path: str, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create empty transcription result"""
        return {
            "full_text": "",
            "segments": [],
            "language": options.get("language", "unknown") if options else "unknown",
            "confidence": 0.0
        }
    
    def _create_transcription_prompt(self, options: Optional[Dict[str, Any]]) -> str:
        """Create optimized prompt for speech-to-text transcription"""
        
        base_prompt = """You are a highly accurate speech-to-text transcription system. 

Please transcribe the audio provided and return ONLY the transcription text in JSON format:

{
  "text": "exact transcription here",
  "language": "detected language code",
  "confidence": 0.95,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "first segment text"
    }
  ]
}

Requirements:
1. Be extremely accurate with the transcription
2. Detect the spoken language automatically
3. Handle multiple speakers if present
4. Include timestamps for speech segments
5. Provide confidence scores for each segment
6. If speech is unclear, mark as [unclear] with reason

IMPORTANT: 
- Return ONLY the JSON object, no explanations
- If no speech detected, return {"text": "", "language": "unknown", "confidence": 0.0, "segments": []}
- Be precise with timing and speaker identification"""
        
        # Add language specification if provided
        if options and options.get("language"):
            language_prompt = f"\n\nTarget language: {options.get('language')}"
            base_prompt += language_prompt
        
        return base_prompt
    
    def _parse_transcription_response(self, response_text: str, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Ollama response and extract structured data"""
        try:
            # Try to parse JSON response
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                try:
                    parsed = json.loads(response_text)
                    
                    # Validate parsed response
                    if "text" in parsed:
                        return {
                            "full_text": parsed["text"],
                            "segments": parsed.get("segments", []),
                            "language": parsed.get("language", "auto-detected"),
                            "confidence": parsed.get("confidence", 0.8)
                        }
                    else:
                        # Fallback to simple text extraction
                        return {
                            "full_text": response_text.strip(),
                            "segments": [],
                            "language": "auto-detected",
                            "confidence": 0.7
                        }
                except json.JSONDecodeError:
                    # Not valid JSON, treat as plain text
                    pass
            
            # Fallback: treat as plain text
            return {
                "full_text": response_text.strip(),
                "segments": [],
                "language": "auto-detected", 
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Failed to parse transcription response: {e}")
            return {
                "full_text": response_text,
                "segments": [],
                "language": "auto-detected",
                "confidence": 0.5
            }
    
    def _estimate_audio_duration(self, audio_path: str) -> float:
        """Estimate audio duration (simplified calculation)"""
        try:
            # This is a rough estimate - in production you'd use audio analysis
            import os
            file_size = os.path.getsize(audio_path)
            
            # Rough estimation: assume 8kbps audio (adjust as needed)
            estimated_duration = file_size / (8 * 1024)  # seconds
            return max(1.0, estimated_duration)
            
        except Exception:
            return 30.0  # Default 30 seconds
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model"""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "available": await self.is_model_available()
        }
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama server"""
        try:
            await self._ensure_client()
            url = f"{self.base_url}/api/tags"
            
            async with self.client.get(url, timeout=10) as response:
                return response.status == 200
            return False
            
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False

# DeepSeek-specific optimizations
class DeepSeekOllamaService(OllamaService):
    """Optimized service for DeepSeek models via Ollama"""
    
    def _create_transcription_prompt(self, options: Optional[Dict[str, Any]]) -> str:
        """Create DeepSeek-specific transcription prompt"""
        
        prompt = """You are DeepSeek-Coder, a specialized AI model optimized for code and transcription tasks.

TRANSCRIPTION TASK:
Transcribe the provided audio with extreme accuracy. 

DeepSeek Instructions:
- You excel at understanding spoken content including technical jargon
- Provide word-level precision
- Handle multiple speakers gracefully  
- Detect language automatically
- Use your analytical capabilities for the best transcription

Return this JSON format:
{
  "text": "precise transcription",
  "language": "detected language code",
  "confidence": confidence_score,
  "segments": [
    {
      "start": timestamp,
      "end": timestamp, 
      "text": "segment text",
      "speaker": speaker_number,
      "confidence": score
    }
  ]
}

Requirements:
- Maximum accuracy for both technical and general speech
- Auto-detect spoken language
- Handle background noise and speech artifacts
- Provide high-confidence timestamps
- Identify different speakers if multiple voices present"""
        
        # Add language specification if provided
        if options and options.get("language"):
            language_prompt = f"\n\nLanguage focus: {options.get('language')}"
            prompt += language_prompt
        
        return prompt

class OllamaSpeechToTextService:
    """Service that switches between different Ollama models based on availability"""
    
    def __init__(self):
        self.deepseek_service = DeepSeekOllamaService()
        self.generic_service = OllamaService()
        self.current_service = None
    
    async def initialize(self):
        """Initialize and select the best available service"""
        # Try DeepSeek first (preferred)
        if await self.deepseek_service.is_model_available():
            self.current_service = self.deepseek_service
            logger.info("Using DeepSeek model for speech-to-text")
            return True
        
        # Fallback to generic service
        self.current_service = self.generic_service
        logger.info("Using generic Ollama model for speech-to-text")
        return True
    
    async def transcribe(self, audio_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transcribe audio using the best available service"""
        await self.initialize()
        return await self.current_service.transcribe(audio_path, options)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        if self.current_service:
            return await self.current_service.get_model_info()
        return {"provider": "none", "model": "none", "available": False}