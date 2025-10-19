"""
Media format detection and analysis utilities.

This module provides tools for detecting media file types,
extracting metadata, and analyzing media characteristics.
"""

import os
import struct
import mimetypes
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)


class MediaDetector:
    """Media file detection and analysis utility."""
    
    # File signatures (magic numbers)
    SIGNATURES = {
        # Audio formats
        'mp3': [b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2', b'\xff\xfa'],
        'wav': [b'RIFF'],
        'aac': [b'\xff\xf1'],
        'flac': [b'fLaC'],
        'ogg': [b'OggS'],
        'm4a': [b'\x00\x00\x00\x1cftypM4A'],
        'opus': [b'OggS'],
        
        # Video formats
        'mp4': [b'\x00\x00\x00\x18ftypmp4', b'\x00\x00\x00\x1cftypisom'],
        'avi': [b'RIFF'],
        'mov': [b'\x00\x00\x00\x14ftypqt'],
        'webm': [b'\x1a\x45\xdf\xa3'],
        'mkv': [b'\x1a\x45\xdf\xa3'],
        'flv': [b'FLV'],
        'wmv': [b'\x30\x26\xb2\x75\x8e\x66\xcf\x11'],
        
        # Image formats
        'jpeg': [b'\xff\xd8\xff'],
        'png': [b'\x89PNG\r\n\x1a\n'],
        'gif': [b'GIF87a', b'GIF89a'],
        'bmp': [b'BM'],
        'webp': [b'RIFF'],
        'tiff': [b'II*\x00', b'MM\x00*']
    }
    
    # MIME type mappings
    MIME_MAPPINGS = {
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'aac': 'audio/aac',
        'flac': 'audio/flac',
        'ogg': 'audio/ogg',
        'm4a': 'audio/mp4',
        'opus': 'audio/opus',
        'mp4': 'video/mp4',
        'avi': 'video/x-msvideo',
        'mov': 'video/quicktime',
        'webm': 'video/webm',
        'mkv': 'video/x-matroska',
        'flv': 'video/x-flv',
        'wmv': 'video/x-ms-wmv',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'tiff': 'image/tiff'
    }
    
    def __init__(self):
        self.supported_formats = list(self.SIGNATURES.keys())
    
    def detect_format(self, file_path: str) -> Dict[str, Any]:
        """
        Detect media format from file signature and extension.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Dictionary with format information
        """
        try:
            if not os.path.exists(file_path):
                return {"error": "File not found"}
            
            # Get file extension
            extension = Path(file_path).suffix.lower()
            
            # Detect from file signature
            signature_format = self._detect_from_signature(file_path)
            
            # Detect from extension
            extension_format = self._detect_from_extension(extension)
            
            # Resolve format conflicts
            detected_format = self._resolve_format_conflict(signature_format, extension_format)
            
            # Get MIME type
            mime_type = self.MIME_MAPPINGS.get(detected_format)
            
            # Get media category
            category = self._get_media_category(detected_format)
            
            return {
                "format": detected_format,
                "extension": extension,
                "mime_type": mime_type,
                "category": category,
                "signature_match": signature_format == detected_format,
                "extension_match": extension_format == detected_format,
                "is_supported": detected_format in self.supported_formats
            }
            
        except Exception as e:
            logger.error(f"Format detection error for {file_path}: {str(e)}")
            return {"error": str(e)}
    
    def get_media_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from media file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dictionary with metadata information
        """
        try:
            format_info = self.detect_format(file_path)
            
            if "error" in format_info:
                return format_info
            
            # Get basic file info
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            metadata = {
                "file_path": file_path,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                **format_info
            }
            
            # Add format-specific metadata
            if format_info["category"] == "audio":
                metadata.update(self._get_audio_metadata(file_path))
            elif format_info["category"] == "video":
                metadata.update(self._get_video_metadata(file_path))
            elif format_info["category"] == "image":
                metadata.update(self._get_image_metadata(file_path))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error for {file_path}: {str(e)}")
            return {"error": str(e)}
    
    def _detect_from_signature(self, file_path: str) -> Optional[str]:
        """Detect format from file signature (magic numbers)."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Read first 32 bytes
            
            for format_name, signatures in self.SIGNATURES.items():
                for signature in signatures:
                    if header.startswith(signature):
                        return format_name
            
            return None
            
        except Exception as e:
            logger.error(f"Signature detection error: {str(e)}")
            return None
    
    def _detect_from_extension(self, extension: str) -> Optional[str]:
        """Detect format from file extension."""
        extension_mapping = {
            '.mp3': 'mp3', '.wav': 'wav', '.aac': 'aac', '.flac': 'flac',
            '.ogg': 'ogg', '.m4a': 'm4a', '.opus': 'opus',
            '.mp4': 'mp4', '.avi': 'avi', '.mov': 'mov', '.webm': 'webm',
            '.mkv': 'mkv', '.flv': 'flv', '.wmv': 'wmv',
            '.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.gif': 'gif',
            '.bmp': 'bmp', '.webp': 'webp', '.tiff': 'tiff'
        }
        
        return extension_mapping.get(extension.lower())
    
    def _resolve_format_conflict(self, signature_format: Optional[str], 
                               extension_format: Optional[str]) -> str:
        """Resolve conflicts between signature and extension detection."""
        
        # If both methods agree, use that format
        if signature_format == extension_format and signature_format:
            return signature_format
        
        # If signature detection succeeded, prefer it
        if signature_format:
            logger.warning(f"Signature/extension mismatch: signature={signature_format}, extension={extension_format}")
            return signature_format
        
        # Fall back to extension detection
        if extension_format:
            return extension_format
        
        # Default to unknown
        return "unknown"
    
    def _get_media_category(self, format_name: str) -> str:
        """Get media category from format name."""
        audio_formats = ['mp3', 'wav', 'aac', 'flac', 'ogg', 'm4a', 'opus']
        video_formats = ['mp4', 'avi', 'mov', 'webm', 'mkv', 'flv', 'wmv']
        image_formats = ['jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']
        
        if format_name in audio_formats:
            return "audio"
        elif format_name in video_formats:
            return "video"
        elif format_name in image_formats:
            return "image"
        else:
            return "unknown"
    
    def _get_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract audio-specific metadata."""
        # This is a simplified implementation
        # In production, you would use libraries like mutagen or pydub
        
        metadata = {
            "duration_seconds": None,
            "bitrate": None,
            "sample_rate": None,
            "channels": None
        }
        
        try:
            # Try to extract basic duration from file size
            file_size = os.path.getsize(file_path)
            
            # Very rough estimation (will be inaccurate)
            if file_size > 0:
                # Assume average 128kbps for audio, 1 second = 16KB
                estimated_duration = file_size / (128 * 1024 / 8)
                metadata["duration_seconds"] = round(estimated_duration, 1)
            
        except Exception as e:
            logger.warning(f"Audio metadata extraction failed: {str(e)}")
        
        return metadata
    
    def _get_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract video-specific metadata."""
        # This is a simplified implementation
        # In production, you would use libraries like ffmpeg-python or OpenCV
        
        metadata = {
            "duration_seconds": None,
            "width": None,
            "height": None,
            "fps": None,
            "bitrate": None
        }
        
        try:
            # Very basic estimation based on file size
            file_size = os.path.getsize(file_path)
            
            # Rough estimation for video (1 second = 1MB for SD video)
            if file_size > 0:
                estimated_duration = file_size / (1024 * 1024)
                metadata["duration_seconds"] = round(estimated_duration, 1)
            
        except Exception as e:
            logger.warning(f"Video metadata extraction failed: {str(e)}")
        
        return metadata
    
    def _get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract image-specific metadata."""
        # This is a simplified implementation
        # In production, you would use libraries like Pillow
        
        metadata = {
            "width": None,
            "height": None,
            "color_mode": None,
            "has_transparency": False
        }
        
        try:
            # Basic detection for common formats
            with open(file_path, 'rb') as f:
                header = f.read(24)
            
            # JPEG detection (very basic)
            if header.startswith(b'\xff\xd8\xff'):
                metadata["format"] = "jpeg"
            
            # PNG detection
            elif header.startswith(b'\x89PNG'):
                metadata["format"] = "png"
                metadata["has_transparency"] = True
            
            # GIF detection
            elif header.startswith(b'GIF'):
                metadata["format"] = "gif"
                metadata["has_transparency"] = True
            
        except Exception as e:
            logger.warning(f"Image metadata extraction failed: {str(e)}")
        
        return metadata
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if file format is supported."""
        format_info = self.detect_format(file_path)
        return format_info.get("is_supported", False)
    
    def get_processing_requirements(self, file_path: str) -> Dict[str, Any]:
        """Get processing requirements for the media file."""
        metadata = self.get_media_metadata(file_path)
        
        if "error" in metadata:
            return {"error": metadata["error"]}
        
        category = metadata["category"]
        file_size_mb = metadata["file_size_mb"]
        
        requirements = {
            "needs_audio_extraction": category == "video",
            "estimated_processing_time": self._estimate_processing_time(metadata),
            "processing_priority": self._get_processing_priority(metadata),
            "memory_requirement_mb": self._estimate_memory_requirement(metadata)
        }
        
        return requirements
    
    def _estimate_processing_time(self, metadata: Dict[str, Any]) -> float:
        """Estimate processing time in seconds."""
        if metadata["category"] == "video":
            # Video requires audio extraction + transcription
            duration = metadata.get("duration_seconds", 60)
            return duration * 0.3  # 30% of duration for processing
        else:
            # Audio only needs transcription
            duration = metadata.get("duration_seconds", 30)
            return duration * 0.2  # 20% of duration for processing
    
    def _get_processing_priority(self, metadata: Dict[str, Any]) -> str:
        """Get processing priority based on file characteristics."""
        file_size_mb = metadata["file_size_mb"]
        
        if file_size_mb < 5:
            return "high"
        elif file_size_mb < 50:
            return "normal"
        else:
            return "low"
    
    def _estimate_memory_requirement(self, metadata: Dict[str, Any]) -> int:
        """Estimate memory requirement in MB."""
        file_size_mb = metadata["file_size_mb"]
        
        if metadata["category"] == "video":
            # Video needs more memory for processing
            return max(file_size_mb * 2, 100)
        else:
            # Audio processing is less memory intensive
            return max(file_size_mb * 1.5, 50)


# Global detector instance
media_detector = MediaDetector()