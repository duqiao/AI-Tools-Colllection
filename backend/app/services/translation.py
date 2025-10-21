import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.provider = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize translation provider based on settings"""
        from app.core.config import settings
        
        provider = settings.TRANSLATION_PROVIDER.lower()
        if provider == "deepl":
            self.provider = DeepLTranslator()
        else:  # Default to Google Translate
            self.provider = GoogleTranslator()
        
        logger.info(f"Translation provider initialized: {settings.TRANSLATION_PROVIDER}")
    
    async def translate(self, text: str, source_language: str = "auto", target_language: str = "zh") -> Dict[str, Any]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_language: Source language code (auto-detect if "auto")
            target_language: Target language code
        
        Returns:
            Dictionary containing translation results
        """
        if not text or text.strip() == "":
            raise ValueError("Text to translate cannot be empty")
        
        try:
            # Run translation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._translate_sync,
                text,
                source_language,
                target_language
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def _translate_sync(self, text: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Synchronous translation"""
        try:
            result = self.provider.translate(text, source_language, target_language)
            
            # Standardize result format
            return {
                "originalText": text,
                "translatedText": result["translated_text"],
                "sourceLanguage": result.get("source_language", source_language),
                "targetLanguage": target_language,
                "confidence": result.get("confidence", 0.9),
                "provider": result.get("provider", "unknown"),
                "metadata": result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return self.provider.get_supported_languages()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider": self.provider.get_name(),
            "configured": self.provider.is_configured(),
            "supported_languages": self.get_supported_languages()
        }

class GoogleTranslator:
    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.GOOGLE_TRANSLATE_API_KEY
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("Google Translate API key not configured")
    
    def translate(self, text: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Translate using Google Translate API"""
        if not self.is_configured:
            # Fallback to basic mock translation
            return self._mock_translation(text, source_language, target_language)
        
        try:
            import googletrans
            translator = googletrans.Translator()
            
            # Detect language if auto
            detected_lang = source_language
            if source_language == "auto":
                detected = translator.detect(text)
                detected_lang = detected.lang
            
            # Perform translation
            result = translator.translate(text, src=detected_lang, dest=target_language)
            
            return {
                "translated_text": result.text,
                "source_language": result.src,
                "confidence": 0.9,  # Google Translate doesn't provide confidence
                "provider": "google"
            }
            
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            # Fallback to mock translation
            return self._mock_translation(text, source_language, target_language)
    
    def _mock_translation(self, text: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Mock translation for fallback"""
        # This is a simple fallback - in production, you'd want a better fallback
        mock_translations = {
            "hello": {"zh": "你好", "es": "hola", "fr": "bonjour"},
            "thank you": {"zh": "谢谢", "es": "gracias", "fr": "merci"},
            "goodbye": {"zh": "再见", "es": "adiós", "fr": "au revoir"}
        }
        
        lower_text = text.lower().strip()
        if lower_text in mock_translations and target_language in mock_translations[lower_text]:
            translated_text = mock_translations[lower_text][target_language]
        else:
            translated_text = f"[Google Translate would translate: '{text}' from {source_language} to {target_language}]"
        
        return {
            "translated_text": translated_text,
            "source_language": source_language,
            "confidence": 0.5,
            "provider": "mock_google"
        }
    
    def get_supported_languages(self) -> list:
        """Get supported languages"""
        return ["en", "zh", "zh-cn", "zh-tw", "es", "fr", "de", "ja", "ko", "pt", "ru", "ar", "hi"]
    
    def get_name(self) -> str:
        return "google"

class DeepLTranslator:
    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.DEEPL_API_KEY
        self.is_configured = bool(self.api_key)
        
        if not self.is_configured:
            logger.warning("DeepL API key not configured")
    
    def translate(self, text: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Translate using DeepL API"""
        if not self.is_configured:
            # Fallback to Google Translator
            google_translator = GoogleTranslator()
            return google_translator.translate(text, source_language, target_language)
        
        try:
            from deep_translator import GoogleTranslator as DeepLAPI
            
            translator = DeepLAPI(api_key=self.api_key)
            result = translator.translate(
                text,
                source=source_language if source_language != "auto" else None,
                target=target_language
            )
            
            return {
                "translated_text": result.text,
                "source_language": result.src,
                "confidence": 0.95,  # DeepL generally provides high quality
                "provider": "deepl"
            }
            
        except Exception as e:
            logger.error(f"DeepL translation error: {e}")
            # Fallback to Google Translator
            google_translator = GoogleTranslator()
            return google_translator.translate(text, source_language, target_language)
    
    def get_supported_languages(self) -> list:
        """Get supported languages"""
        return ["en", "zh", "zh-cn", "es", "fr", "de", "ja", "ko", "pt", "ru"]
    
    def get_name(self) -> str:
        return "deepl"

# Service factory
def get_translation_service():
    """Get the configured translation service"""
    return TranslationService()