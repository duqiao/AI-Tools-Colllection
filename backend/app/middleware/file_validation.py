"""
File validation middleware for media uploads.

This module provides validation logic for uploaded media files
including size, format, and content verification.
"""

import os
import mimetypes
from typing import Dict, Any, List
from fastapi import HTTPException, UploadFile, status
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


class FileValidator:
    """File validation utility class."""
    
    # Allowed file extensions by type
    ALLOWED_EXTENSIONS = {
        "audio": [
            ".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".opus", 
            ".wma", ".mp2", ".amr", ".3gp", ".au"
        ],
        "video": [
            ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv",
            ".m4v", ".3gp", ".mpg", ".mpeg", ".ts", ".vob"
        ],
        "image": [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"
        ]
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        "audio": 50 * 1024 * 1024,      # 50MB
        "video": 200 * 1024 * 1024,     # 200MB
        "image": 10 * 1024 * 1024,      # 10MB
        "default": 100 * 1024 * 1024    # 100MB
    }
    
    # MIME types to validate against
    ALLOWED_MIME_TYPES = {
        "audio": [
            "audio/mpeg", "audio/wav", "audio/aac", "audio/mp4", 
            "audio/flac", "audio/ogg", "audio/opus"
        ],
        "video": [
            "video/mp4", "video/avi", "video/quicktime", "video/x-ms-wmv",
            "video/x-flv", "video/webm", "video/x-matroska"
        ],
        "image": [
            "image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"
        ]
    }
    
    def __init__(self):
        self.supported_types = list(self.ALLOWED_EXTENSIONS.keys())
    
    def validate_file(self, file: UploadFile, max_size: int = None) -> Dict[str, Any]:
        """
        Validate uploaded file.
        
        Args:
            file: The uploaded file object
            max_size: Maximum allowed size override
            
        Returns:
            Validation result with file information
        """
        try:
            # Check if file is provided
            if not file or not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No file provided"
                )
            
            # Get file information
            filename = file.filename
            file_extension = Path(filename).suffix.lower()
            file_size = 0  # FastAPI doesn't provide size until file is read
            
            # Determine file type from extension
            file_type = self._determine_file_type(file_extension)
            
            if file_type == "unknown":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file extension: {file_extension}. "
                           f"Allowed: {self._get_allowed_extensions_string()}"
                )
            
            # Validate file size (we'll check this after reading the file)
            max_allowed_size = max_size or self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES["default"])
            
            # Validate MIME type if provided
            mime_type = getattr(file, 'content_type', None)
            if mime_type and not self._is_mime_type_allowed(mime_type, file_type):
                logger.warning(f"MIME type mismatch: {mime_type} for file {filename}")
                # We'll still allow it but log a warning
            
            return {
                "valid": True,
                "filename": filename,
                "file_type": file_type,
                "file_extension": file_extension,
                "mime_type": mime_type,
                "max_size": max_allowed_size
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File validation failed"
            )
    
    async def validate_file_content(self, file: UploadFile, validation_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate actual file content after reading.
        
        Args:
            file: The uploaded file object
            validation_info: Previous validation results
            
        Returns:
            Complete validation result with content info
        """
        try:
            # Read file content to check actual size
            content = await file.read()
            actual_size = len(content)
            
            # Reset file position for further processing
            await file.seek(0)
            
            # Check file size
            if actual_size > validation_info["max_size"]:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File too large: {actual_size} bytes. "
                           f"Maximum allowed: {validation_info['max_size']} bytes"
                )
            
            # Check minimum size (avoid empty files)
            min_size = 1024  # 1KB minimum
            if actual_size < min_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too small: {actual_size} bytes. "
                           f"Minimum required: {min_size} bytes"
                )
            
            # Additional content validation for specific types
            await self._validate_content_by_type(content, validation_info["file_type"])
            
            return {
                **validation_info,
                "file_size": actual_size,
                "content_valid": True
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"File content validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File content validation failed"
            )
    
    def _determine_file_type(self, extension: str) -> str:
        """Determine file type from extension."""
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if extension in extensions:
                return file_type
        return "unknown"
    
    def _is_mime_type_allowed(self, mime_type: str, file_type: str) -> bool:
        """Check if MIME type is allowed for file type."""
        allowed_types = self.ALLOWED_MIME_TYPES.get(file_type, [])
        return mime_type in allowed_types
    
    def _get_allowed_extensions_string(self) -> str:
        """Get formatted string of allowed extensions."""
        all_extensions = []
        for extensions in self.ALLOWED_EXTENSIONS.values():
            all_extensions.extend(extensions)
        return ", ".join(sorted(all_extensions))
    
    async def _validate_content_by_type(self, content: bytes, file_type: str):
        """Additional content validation based on file type."""
        # Basic file signature validation
        if file_type == "audio":
            self._validate_audio_signature(content)
        elif file_type == "video":
            self._validate_video_signature(content)
        elif file_type == "image":
            self._validate_image_signature(content)
    
    def _validate_audio_signature(self, content: bytes):
        """Validate audio file signature."""
        # Check for common audio file signatures
        audio_signatures = {
            b'ID3': 'mp3',
            b'\xff\xfb': 'mp3',
            b'\xff\xf3': 'mp3',
            b'\xff\xf2': 'mp3',
            b'RIFF': 'wav',
            b'OggS': 'ogg',
            b'fLaC': 'flac'
        }
        
        # Check first 12 bytes for signatures
        header = content[:12]
        for signature, format_name in audio_signatures.items():
            if header.startswith(signature):
                return
        
        # If no signature found, log warning but don't fail
        logger.warning("Could not identify audio file signature")
    
    def _validate_video_signature(self, content: bytes):
        """Validate video file signature."""
        # Check for common video file signatures
        video_signatures = {
            b'\x00\x00\x00\x18ftypmp4': 'mp4',
            b'RIFF': 'avi',
            b'\x1a\x45\xdf\xa3': 'webm',
            b'\x00\x00\x00\x1cftypisom': 'mp4'
        }
        
        # Check first 16 bytes for signatures
        header = content[:16]
        for signature, format_name in video_signatures.items():
            if header.startswith(signature):
                return
        
        # If no signature found, log warning but don't fail
        logger.warning("Could not identify video file signature")
    
    def _validate_image_signature(self, content: bytes):
        """Validate image file signature."""
        # Check for common image file signatures
        image_signatures = {
            b'\xff\xd8\xff': 'jpeg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
            b'RIFF': 'webp',
            b'II*\x00': 'tiff',
            b'MM\x00*': 'tiff'
        }
        
        # Check first 8 bytes for signatures
        header = content[:8]
        for signature, format_name in image_signatures.items():
            if header.startswith(signature):
                return
        
        # If no signature found, log warning but don't fail
        logger.warning("Could not identify image file signature")
    
    def get_file_info(self, file: UploadFile) -> Dict[str, Any]:
        """Get comprehensive file information."""
        if not file.filename:
            return {}
        
        extension = Path(file.filename).suffix.lower()
        file_type = self._determine_file_type(extension)
        
        return {
            "filename": file.filename,
            "extension": extension,
            "file_type": file_type,
            "mime_type": file.content_type,
            "max_size": self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES["default"]),
            "is_supported": file_type in self.supported_types
        }


# Global validator instance
file_validator = FileValidator()