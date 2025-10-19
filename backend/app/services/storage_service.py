"""
Storage service for handling file uploads and media processing.

This module provides file storage operations including upload,
download, and processing of various media formats.
"""

import os
import uuid
import tempfile
import shutil
from typing import Dict, Any, Optional, List, BinaryIO
from pathlib import Path
import aiofiles
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for file storage and media processing operations."""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types and extensions
        self.allowed_extensions = {
            "audio": [".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".opus"],
            "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            "audio": 50 * 1024 * 1024,  # 50MB
            "video": 100 * 1024 * 1024,  # 100MB
            "image": 10 * 1024 * 1024    # 10MB
        }
    
    async def save_uploaded_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Save uploaded file to storage."""
        
        try:
            # Validate file
            validation_result = self._validate_file(file_content, filename, file_type)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"]
                }
            
            # Generate unique filename
            file_extension = Path(filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            # Create user directory
            user_dir = self.upload_dir / str(user_id)
            user_dir.mkdir(exist_ok=True)
            
            # Create date-based subdirectory
            date_dir = user_dir / datetime.now().strftime("%Y-%m-%d")
            date_dir.mkdir(exist_ok=True)
            
            # Save file
            file_path = date_dir / unique_filename
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Generate file URL
            file_url = f"{settings.base_url}/uploads/{user_id}/{datetime.now().strftime('%Y-%m-%d')}/{unique_filename}"
            
            logger.info(f"Saved file: {file_path}")
            
            return {
                "success": True,
                "filename": unique_filename,
                "file_path": str(file_path),
                "file_url": file_url,
                "file_size": len(file_content),
                "file_type": file_type,
                "mime_type": validation_result["mime_type"]
            }
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to save file: {str(e)}"
            }
    
    async def extract_audio_from_video(
        self,
        video_path: str,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """Extract audio from video file."""
        
        try:
            # Generate output filename
            video_filename = Path(video_path).stem
            output_filename = f"{video_filename}_extracted.{output_format}"
            output_path = Path(video_path).parent / output_filename
            
            # Mock implementation - in production, use ffmpeg
            logger.info(f"Extracting audio from: {video_path}")
            
            # Simulate processing time
            await asyncio.sleep(1)
            
            # For mock, just copy the video file as "extracted audio"
            # In production, you would use ffmpeg or similar
            shutil.copy2(video_path, output_path)
            
            logger.info(f"Audio extracted to: {output_path}")
            
            return {
                "success": True,
                "audio_path": str(output_path),
                "audio_filename": output_filename,
                "duration": 120.5  # Mock duration
            }
            
        except Exception as e:
            logger.error(f"Failed to extract audio: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to extract audio: {str(e)}"
            }
    
    async def download_media_from_url(
        self,
        url: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Download media file from URL."""
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Get filename from URL or generate one
                filename = self._extract_filename_from_url(url)
                if not filename:
                    filename = f"download_{uuid.uuid4()}.mp3"
                
                # Determine file type from content type or extension
                content_type = response.headers.get("content-type", "")
                file_type = self._determine_file_type_from_mime(content_type) or \
                           self._determine_file_type_from_extension(filename)
                
                if not file_type:
                    file_type = "audio"  # Default to audio
                
                # Save downloaded file
                result = await self.save_uploaded_file(
                    response.content,
                    filename,
                    file_type,
                    user_id
                )
                
                if result["success"]:
                    result["original_url"] = url
                    result["content_type"] = content_type
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to download media from URL {url}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to download media: {str(e)}"
            }
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage."""
        
        try:
            path = Path(file_path)
            if path.exists():
                await asyncio.to_thread(path.unlink)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information."""
        
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "exists": False,
                    "error": "File not found"
                }
            
            stat = path.stat()
            
            return {
                "exists": True,
                "filename": path.name,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "file_extension": path.suffix.lower(),
                "file_type": self._determine_file_type_from_extension(path.name)
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {str(e)}")
            return {
                "exists": False,
                "error": str(e)
            }
    
    async def cleanup_old_files(self, days: int = 7) -> int:
        """Clean up files older than specified days."""
        
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    await asyncio.to_thread(file_path.unlink)
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0
    
    def _validate_file(
        self,
        file_content: bytes,
        filename: str,
        file_type: str
    ) -> Dict[str, Any]:
        """Validate uploaded file."""
        
        # Check file size
        max_size = self.max_file_sizes.get(file_type, 50 * 1024 * 1024)
        if len(file_content) > max_size:
            return {
                "valid": False,
                "error": f"File too large. Maximum size: {max_size // (1024*1024)}MB"
            }
        
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        allowed_extensions = self.allowed_extensions.get(file_type, [])
        
        if allowed_extensions and file_extension not in allowed_extensions:
            return {
                "valid": False,
                "error": f"File type not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
            }
        
        # Determine MIME type (mock implementation)
        mime_type = self._get_mime_type(file_extension)
        
        return {
            "valid": True,
            "mime_type": mime_type
        }
    
    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """Extract filename from URL."""
        try:
            from urllib.parse import urlparse, unquote
            
            parsed = urlparse(url)
            filename = unquote(Path(parsed.path).name)
            
            if filename and "." in filename:
                return filename
            
            return None
            
        except Exception:
            return None
    
    def _determine_file_type_from_mime(self, mime_type: str) -> Optional[str]:
        """Determine file type from MIME type."""
        
        mime_mapping = {
            "audio/": "audio",
            "video/": "video",
            "image/": "image"
        }
        
        for prefix, file_type in mime_mapping.items():
            if mime_type.startswith(prefix):
                return file_type
        
        return None
    
    def _determine_file_type_from_extension(self, filename: str) -> str:
        """Determine file type from file extension."""
        
        extension = Path(filename).suffix.lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        return "unknown"
    
    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type for file extension."""
        
        mime_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".aac": "audio/aac",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".opus": "audio/opus",
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".flv": "video/x-flv",
            ".webm": "video/webm",
            ".mkv": "video/x-matroska",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp"
        }
        
        return mime_types.get(extension, "application/octet-stream")