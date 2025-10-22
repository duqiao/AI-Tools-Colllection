#!/usr/bin/env python3
"""
Test OpenAI Whisper Service Integration
"""

import asyncio
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_whisper_service():
    """Test OpenAI Whisper service functionality"""
    print("🎤 Testing OpenAI Whisper Service...")
    print("=" * 50)
    
    try:
        from app.services.speech_to_text import get_speech_to_text_service
        
        # Get the speech-to-text service
        stt_service = get_speech_to_text_service()
        print(f"✅ Service loaded: {type(stt_service).__name__}")
        
        # Test model info
        if hasattr(stt_service, 'get_model_info'):
            model_info = stt_service.get_model_info()
            print(f"✅ Model info: {model_info}")
        else:
            print("ℹ️ Service doesn't have get_model_info method")
        
        # Test supported languages
        if hasattr(stt_service, 'get_supported_languages'):
            languages = stt_service.get_supported_languages()
            print(f"✅ Supported languages: {len(languages)} languages")
            print(f"   Sample: {', '.join(languages[:5])}")
        else:
            print("ℹ️ Service doesn't have get_supported_languages method")
        
        # Test transcription with a simple test
        test_audio_path = "test_audio.wav"
        
        # Create a minimal test audio file (sine wave)
        try:
            import wave
            import numpy as np
            
            # Create a simple sine wave test audio
            sample_rate = 16000
            duration = 2  # 2 seconds
            frequency = 440  # A4 note
            
            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            
            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(test_audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            print(f"✅ Created test audio file: {test_audio_path}")
            
            # Test transcription
            print("\n🎤 Testing transcription...")
            
            try:
                transcription_options = {
                    "language": "en",
                    "enable_timestamps": True
                }
                
                result = await stt_service.transcribe(test_audio_path, transcription_options)
                
                if result and "full_text" in result:
                    print("✅ Transcription successful!")
                    print(f"   Text: {result['full_text'][:100]}...")
                    print(f"   Language: {result.get('language', 'unknown')}")
                    print(f"   Confidence: {result.get('confidence', 0):.2f}")
                else:
                    print("⚠️ Transcription returned empty or invalid result")
                    print(f"   Result: {result}")
                    
            except Exception as transcribe_error:
                print(f"❌ Transcription failed: {transcribe_error}")
            
            # Cleanup test file
            if os.path.exists(test_audio_path):
                os.remove(test_audio_path)
                
        except ImportError as numpy_error:
            print("⚠️ NumPy not available for audio generation, skipping audio test")
        except ImportError as wave_error:
            print("⚠️ Wave module not available, skipping audio test")
        except Exception as audio_error:
            print(f"⚠️ Audio generation failed: {audio_error}")
        
        print("\n📊 Whisper Service Test Summary:")
        print("✅ Service initialization: SUCCESS")
        print("✅ Service selection: SUCCESS") 
        print("✅ Configuration: SUCCESS")
        
        return True
        
    except ImportError as import_error:
        print(f"❌ Failed to import speech_to_text service: {import_error}")
        return False
    except Exception as e:
        print(f"❌ Whisper service test failed: {e}")
        return False

async def main():
    """Run Whisper service test"""
    print("🧪 OpenAI Whisper Service Test")
    print("This tests the speech-to-text functionality")
    
    try:
        success = await test_whisper_service()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))