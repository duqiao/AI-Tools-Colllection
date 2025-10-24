from fastapi import UploadFile
from pathlib import Path
import os
import uuid
import time
from typing import Tuple

from app.core.config import settings

def validate_file_type(mime_type: str) -> bool:
    """Check if file type is supported"""
    return mime_type in settings.ALLOWED_AUDIO_TYPES + settings.ALLOWED_VIDEO_TYPES

def get_file_type(mime_type: str) -> str:
    """Determine file type from MIME type"""
    if mime_type in settings.ALLOWED_AUDIO_TYPES:
        return "audio"
    elif mime_type in settings.ALLOWED_VIDEO_TYPES:
        return "video"
    else:
        return "unknown"

def generate_unique_filename(original_name: str) -> str:
    """Generate unique filename with timestamp and UUID"""
    timestamp = int(time.time())
    unique_id = uuid.uuid4().hex[:16]
    
    # Extract extension
    path = Path(original_name)
    extension = path.suffix
    
    # Generate new filename
    return f"{timestamp}_{unique_id}{extension}"

async def get_file_size(file: UploadFile) -> int:
    """Get actual file size from UploadFile"""
    # Reset file position to start
    await file.seek(0)
    
    # Read file content to get size
    content = await file.read()
    size = len(content)
    
    # Reset file position to start for future reads
    await file.seek(0)
    
    return size

def get_file_size_formatted(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 Bytes"
    
    size_names = ["Bytes", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{round(size, 2)} {size_names[i]}"

def is_file_size_valid(size_bytes: int, file_type: str) -> bool:
    """Check if file size is within limits"""
    max_size = settings.MAX_AUDIO_SIZE if file_type == "audio" else settings.MAX_VIDEO_SIZE
    return size_bytes <= max_size

def get_file_extension(mime_type: str) -> str:
    """Get file extension from MIME type"""
    extension_map = {
        # Audio
        'audio/mpeg': '.mp3',
        'audio/wav': '.wav',
        'audio/x-wav': '.wav',
        'audio/mp4': '.m4a',
        'audio/ogg': '.ogg',
        'audio/flac': '.flac',
        'audio/aac': '.aac',
        
        # Video
        'video/mp4': '.mp4',
        'video/quicktime': '.mov',
        'video/x-msvideo': '.avi',
        'video/x-matroska': '.mkv',
        'video/webm': '.webm'
    }
    
    return extension_map.get(mime_type, '')

def cleanup_temp_file(file_path: str):
    """Safely remove temporary file"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

def validate_media_file(file: UploadFile) -> Tuple[bool, str]:
    """Validate uploaded file and return (is_valid, error_message)"""
    if not file.content_type:
        return False, "File content type is required"
    
    if not validate_file_type(file.content_type):
        return False, f"Unsupported file type: {file.content_type}"
    
    return True, ""