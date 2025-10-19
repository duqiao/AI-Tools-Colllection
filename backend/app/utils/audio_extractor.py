"""
Audio extraction utilities for video processing.

This module provides functionality to extract audio tracks
from video files for speech transcription processing.
"""

import os
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)


class AudioExtractor:
    """Audio extraction utility for video files."""
    
    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.supported_formats = [
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', 
            '.mkv', '.m4v', '.3gp', '.mpg', '.mpeg'
        ]
        self.output_formats = ['mp3', 'wav', 'aac']
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable in system."""
        try:
            # Try to find ffmpeg in common locations
            common_paths = [
                'ffmpeg',
                '/usr/bin/ffmpeg',
                '/usr/local/bin/ffmpeg',
                'C:\\ffmpeg\\bin\\ffmpeg.exe',
                'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe'
            ]
            
            for path in common_paths:
                try:
                    result = subprocess.run(
                        [path, '-version'], 
                        capture_output=True, 
                        timeout=5,
                        check=True
                    )
                    if result.returncode == 0:
                        logger.info(f"Found ffmpeg at: {path}")
                        return path
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            logger.warning("ffmpeg not found, audio extraction will be mocked")
            return None
            
        except Exception as e:
            logger.error(f"Error finding ffmpeg: {str(e)}")
            return None
    
    async def extract_audio_from_video(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        output_format: str = "mp3",
        quality: str = "medium"
    ) -> Dict[str, Any]:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to the input video file
            output_path: Path for the output audio file (optional)
            output_format: Output audio format (mp3, wav, aac)
            quality: Audio quality setting (low, medium, high)
            
        Returns:
            Dictionary with extraction results
        """
        try:
            # Validate input file
            if not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": "Input video file not found"
                }
            
            # Validate file format
            file_extension = Path(video_path).suffix.lower()
            if file_extension not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported video format: {file_extension}"
                }
            
            # Generate output path if not provided
            if not output_path:
                output_path = self._generate_output_path(video_path, output_format)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Extract audio
            if self.ffmpeg_path:
                return await self._extract_with_ffmpeg(
                    video_path, output_path, output_format, quality
                )
            else:
                # Mock extraction for development
                return await self._mock_extraction(
                    video_path, output_path, output_format
                )
                
        except Exception as e:
            logger.error(f"Audio extraction error: {str(e)}")
            return {
                "success": False,
                "error": f"Audio extraction failed: {str(e)}"
            }
    
    async def _extract_with_ffmpeg(
        self,
        video_path: str,
        output_path: str,
        output_format: str,
        quality: str
    ) -> Dict[str, Any]:
        """Extract audio using ffmpeg."""
        try:
            # Configure quality settings
            quality_settings = self._get_quality_settings(output_format, quality)
            
            # Build ffmpeg command
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vn',  # No video
                '-acodec', quality_settings['codec'],
                '-ab', quality_settings['bitrate'],
                '-ar', quality_settings['sample_rate'],
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                output_path
            ]
            
            # Run ffmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Get file info
                file_stats = os.stat(output_path)
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "file_size": file_stats.st_size,
                    "format": output_format,
                    "quality": quality,
                    "processing_time": 0,  # TODO: measure actual time
                    "ffmpeg_output": stderr.decode() if stderr else ""
                }
            else:
                return {
                    "success": False,
                    "error": f"ffmpeg failed with code {process.returncode}",
                    "ffmpeg_output": stderr.decode() if stderr else ""
                }
                
        except Exception as e:
            logger.error(f"ffmpeg extraction error: {str(e)}")
            return {
                "success": False,
                "error": f"ffmpeg extraction failed: {str(e)}"
            }
    
    async def _mock_extraction(
        self,
        video_path: str,
        output_path: str,
        output_format: str
    ) -> Dict[str, Any]:
        """Mock audio extraction for development without ffmpeg."""
        try:
            logger.info(f"Mocking audio extraction from {video_path} to {output_path}")
            
            # Simulate processing time
            await asyncio.sleep(2)
            
            # Create a mock audio file (just copy the video with different extension)
            # In production, this would be actual audio extraction
            import shutil
            shutil.copy2(video_path, output_path)
            
            # Get file info
            file_stats = os.stat(output_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "file_size": file_stats.st_size,
                "format": output_format,
                "quality": "medium",
                "processing_time": 2.0,
                "note": "Mock extraction - ffmpeg not available"
            }
            
        except Exception as e:
            logger.error(f"Mock extraction error: {str(e)}")
            return {
                "success": False,
                "error": f"Mock extraction failed: {str(e)}"
            }
    
    def _generate_output_path(self, video_path: str, output_format: str) -> str:
        """Generate output file path based on input video path."""
        video_file = Path(video_path)
        output_filename = f"{video_file.stem}_extracted.{output_format}"
        output_path = video_file.parent / output_filename
        return str(output_path)
    
    def _get_quality_settings(self, output_format: str, quality: str) -> Dict[str, str]:
        """Get quality settings for audio extraction."""
        settings = {
            'mp3': {
                'low': {'codec': 'mp3', 'bitrate': '64k', 'sample_rate': '22050'},
                'medium': {'codec': 'mp3', 'bitrate': '128k', 'sample_rate': '44100'},
                'high': {'codec': 'mp3', 'bitrate': '192k', 'sample_rate': '44100'}
            },
            'wav': {
                'low': {'codec': 'pcm_s16le', 'bitrate': '64k', 'sample_rate': '22050'},
                'medium': {'codec': 'pcm_s16le', 'bitrate': '1411k', 'sample_rate': '44100'},
                'high': {'codec': 'pcm_s24le', 'bitrate': '2116k', 'sample_rate': '48000'}
            },
            'aac': {
                'low': {'codec': 'aac', 'bitrate': '64k', 'sample_rate': '22050'},
                'medium': {'codec': 'aac', 'bitrate': '128k', 'sample_rate': '44100'},
                'high': {'codec': 'aac', 'bitrate': '256k', 'sample_rate': '48000'}
            }
        }
        
        return settings.get(output_format, settings['mp3']).get(quality, settings['mp3']['medium'])
    
    async def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video file information including audio track details.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        try:
            if not os.path.exists(video_path):
                return {"error": "Video file not found"}
            
            if not self.ffmpeg_path:
                # Mock video info
                file_stats = os.stat(video_path)
                return {
                    "duration_seconds": 120.5,
                    "file_size": file_stats.st_size,
                    "has_audio": True,
                    "audio_codec": "aac",
                    "audio_bitrate": "128k",
                    "sample_rate": "44100",
                    "channels": 2,
                    "note": "Mock info - ffmpeg not available"
                }
            
            # Use ffprobe to get video information
            cmd = [
                'ffprobe',  # Assume ffprobe is in the same location as ffmpeg
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-show_format',
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                probe_data = json.loads(stdout.decode())
                
                # Find audio stream
                audio_stream = None
                for stream in probe_data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    return {
                        "duration_seconds": float(probe_data['format'].get('duration', 0)),
                        "file_size": int(probe_data['format'].get('size', 0)),
                        "has_audio": True,
                        "audio_codec": audio_stream.get('codec_name'),
                        "audio_bitrate": audio_stream.get('bit_rate'),
                        "sample_rate": audio_stream.get('sample_rate'),
                        "channels": audio_stream.get('channels'),
                        "duration": audio_stream.get('duration')
                    }
                else:
                    return {
                        "duration_seconds": float(probe_data['format'].get('duration', 0)),
                        "file_size": int(probe_data['format'].get('size', 0)),
                        "has_audio": False,
                        "error": "No audio stream found in video"
                    }
            else:
                return {
                    "error": f"ffprobe failed: {stderr.decode()}"
                }
                
        except Exception as e:
            logger.error(f"Video info extraction error: {str(e)}")
            return {
                "error": f"Failed to get video info: {str(e)}"
            }
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a supported video format."""
        extension = Path(file_path).suffix.lower()
        return extension in self.supported_formats
    
    def cleanup_temp_files(self, directory: Optional[str] = None):
        """Clean up temporary files created during extraction."""
        try:
            if directory:
                temp_dir = Path(directory)
            else:
                temp_dir = Path(tempfile.gettempdir())
            
            # Remove files matching our pattern
            for file_path in temp_dir.glob("*_extracted.*"):
                try:
                    file_path.unlink()
                    logger.info(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")
    
    async def batch_extract_audio(
        self,
        video_paths: list,
        output_directory: str,
        output_format: str = "mp3",
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        Extract audio from multiple video files concurrently.
        
        Args:
            video_paths: List of video file paths
            output_directory: Directory for output audio files
            output_format: Output audio format
            max_concurrent: Maximum concurrent extractions
            
        Returns:
            Dictionary with batch extraction results
        """
        try:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def extract_with_semaphore(video_path: str) -> Dict[str, Any]:
                async with semaphore:
                    filename = Path(video_path).stem
                    output_path = Path(output_directory) / f"{filename}_extracted.{output_format}"
                    
                    return await self.extract_audio_from_video(
                        video_path, str(output_path), output_format
                    )
            
            # Create output directory
            os.makedirs(output_directory, exist_ok=True)
            
            # Run extractions concurrently
            tasks = [extract_with_semaphore(video_path) for video_path in video_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = []
            failed = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed.append({
                        "video_path": video_paths[i],
                        "error": str(result)
                    })
                elif result.get("success"):
                    successful.append({
                        "video_path": video_paths[i],
                        "output_path": result.get("output_path"),
                        "file_size": result.get("file_size")
                    })
                else:
                    failed.append({
                        "video_path": video_paths[i],
                        "error": result.get("error", "Unknown error")
                    })
            
            return {
                "success": True,
                "total": len(video_paths),
                "successful": len(successful),
                "failed": len(failed),
                "successful_files": successful,
                "failed_files": failed
            }
            
        except Exception as e:
            logger.error(f"Batch extraction error: {str(e)}")
            return {
                "success": False,
                "error": f"Batch extraction failed: {str(e)}"
            }


# Global extractor instance
audio_extractor = AudioExtractor()