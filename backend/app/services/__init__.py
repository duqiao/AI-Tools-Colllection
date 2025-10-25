# Services package initialization
# Lazy imports to avoid initialization issues

def _import_safely(module_name, item_name):
    """Safely import module items with error handling"""
    try:
        module = __import__(module_name, fromlist=[item_name])
        return getattr(module, item_name)
    except Exception as e:
        # Create a fallback function that logs the error
        def fallback(*args, **kwargs):
            import logging
            logging.error(f"Failed to import {item_name} from {module_name}: {e}")
            raise ImportError(f"Service {item_name} not available: {e}")
        return fallback

# Lazy imports
get_speech_to_text_service = _import_safely("app.services.speech_to_text", "get_speech_to_text_service")
get_translation_service = _import_safely("app.services.translation", "get_translation_service")
MediaProcessor = _import_safely("app.services.media_processor", "MediaProcessor")
AudioProcessor = _import_safely("app.services.audio_processor", "AudioProcessor")

__all__ = [
    "get_speech_to_text_service",
    "get_translation_service", 
    "MediaProcessor",
    "AudioProcessor"
]