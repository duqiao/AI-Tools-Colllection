import asyncio
import logging
import tempfile
import subprocess
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    async def extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file using FFmpeg
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        try:
            video_file = Path(video_path)
            audio_filename = f"audio_{video_file.stem}.wav"
            audio_path = os.path.join(self.temp_dir, audio_filename)
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-vn',                    # No video
                '-acodec', 'pcm_s16le',   # Audio codec
                '-ar', '16000',            # Sample rate
                '-ac', '1',                # Mono channel
                '-y',                      # Overwrite output
                str(audio_path)
            ]
            
            # Run FFmpeg in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._run_ffmpeg, cmd)
            
            if not os.path.exists(audio_path):
                raise Exception("Audio extraction failed - no output file created")
            
            logger.info(f"Audio extracted successfully: {audio_filename}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            raise
    
    def _run_ffmpeg(self, cmd: list):
        """Run FFmpeg command synchronously"""
        try:
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
    
    async def get_media_info(self, file_path: str) -> dict:
        """
        Get media file information using FFprobe
        
        Args:
            file_path: Path to media file
            
        Returns:
            Dictionary with media information
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            # Run FFprobe in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._run_ffprobe, cmd)
            
            if not result:
                raise Exception("Failed to get media information")
            
            # Extract relevant information
            format_info = result.get('format', {})
            streams = result.get('streams', [])
            
            # Find audio stream
            audio_stream = None
            for stream in streams:
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            duration = float(format_info.get('duration', 0))
            size = int(format_info.get('size', 0))
            
            media_info = {
                'duration': duration,
                'size': size,
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', 'unknown'),
                'audio_codec': audio_stream.get('codec_name') if audio_stream else None,
                'sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else None,
                'channels': audio_stream.get('channels') if audio_stream else None
            }
            
            return media_info
            
        except Exception as e:
            logger.error(f"Failed to get media info: {e}")
            raise
    
    def _run_ffprobe(self, cmd: list):
        """Run FFprobe command synchronously"""
        try:
            import json
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 seconds timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else "Unknown FFprobe error"
                raise Exception(f"FFprobe error: {error_msg}")
            
            return json.loads(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise Exception("FFprobe process timed out")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse FFprobe output: {e}")
        except Exception as e:
            raise Exception(f"FFprobe execution failed: {e}")
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_ffprobe_available(self) -> bool:
        """Check if FFprobe is available"""
        try:
            subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    async def _is_optimal_wav_format(self, audio_path: str) -> bool:
        """Check if WAV file is in optimal format (16kHz mono, 16-bit)"""
        try:
            media_info = await self.get_media_info(audio_path)
            
            # Check format, sample rate, channels
            format_ok = media_info.get('format_name') == 'wav'
            sample_rate_ok = media_info.get('sample_rate') == 16000
            channels_ok = media_info.get('channels') == 1
            
            return format_ok and sample_rate_ok and channels_ok
            
        except Exception as e:
            logger.warning(f"Failed to check WAV format: {e}")
            return False
    
    def get_supported_formats(self) -> dict:
        """Get supported audio/video formats"""
        return {
            'audio': [
                'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac'
            ],
            'video': [
                'mp4', 'mov', 'avi', 'mkv', 'webm'
            ]
        }