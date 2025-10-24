#!/usr/bin/env python3
"""
Enhanced MP3 Upload Debug Tool (Windows Compatible)
Tests MP3 file upload from frontend to backend with comprehensive debugging
"""

import requests
import json
import time
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

def get_auth_token(backend_url="http://127.0.0.1:8001", user_data=None):
    """Get authentication token with optional custom user data"""
    try:
        print("🔐 Getting authentication token...")
        
        if not user_data:
            user_data = {
                "username": f"DebugUser_{int(time.time())}",
                "openid": f"debug_guest_{int(time.time())}"
            }
        
        print(f"   Request data: {user_data}")
        
        response = requests.post(
            f"{backend_url}/api/v1/auth/guest",
            json=user_data,
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data.get('token')
            user_info = auth_data.get('user', {})
            
            print(f"   ✅ Authentication successful!")
            print(f"   User ID: {user_info.get('id', 'N/A')}")
            print(f"   Username: {user_info.get('username', 'N/A')}")
            print(f"   Token: {token[:30]}..." if token else "No token!")
            
            return token, user_info
        else:
            print(f"   ❌ Auth failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"   Raw response: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return None, None

def test_mp3_upload(backend_url="http://127.0.0.1:8001", file_path=None, upload_data=None):
    """Test MP3 file upload to debug the issue"""
    print("🚀 Enhanced MP3 Upload Debug Tool")
    print("=" * 60)
    
    api_url = f"{backend_url}/api/v1/upload/"
    
    print(f"Backend URL: {backend_url}")
    print(f"Upload URL: {api_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Check if backend is running
    print("1. Testing backend connectivity...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Backend is healthy (status: {health_data.get('status')})")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print(f"💡 Make sure the backend is running: cd backend && python run_windows.py")
        return False
    
    # Test 2: Get authentication token
    print("\n2. Getting authentication token...")
    token, user_info = get_auth_token(backend_url)
    if not token:
        print("❌ Cannot proceed without authentication token")
        return False
    
    # Test 3: Check upload endpoint exists
    print("\n3. Testing upload endpoint...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    try:
        response = requests.options(api_url, headers=headers, timeout=10)
        print(f"✅ Upload endpoint accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload endpoint not accessible: {e}")
        return False
    
    # Test 4: Test job status endpoint
    print("\n4. Testing job status endpoint...")
    try:
        response = requests.get(f"{backend_url}/api/v1/upload/", headers=headers, timeout=10)
        print(f"✅ Job status endpoint accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Job status endpoint test: {e}")
    
    # Test 5: File upload
    print("\n5. Testing file upload...")
    
    # Determine file to upload
    if file_path and os.path.exists(file_path):
        print(f"📁 Using existing file: {file_path}")
        upload_file_path = file_path
        with open(upload_file_path, 'rb') as f:
            test_mp3_content = f.read()
        file_name = os.path.basename(file_path)
        mime_type = 'audio/mpeg' if file_path.endswith('.mp3') else 'audio/wav'
    else:
        # Create a small test MP3 file
        print("📝 Creating test MP3 file...")
        test_mp3_content = create_test_mp3()
        upload_file_path = "test_upload.mp3"
        file_name = "test_upload.mp3"
        mime_type = 'audio/mpeg'
        
        with open(upload_file_path, "wb") as f:
            f.write(test_mp3_content)
        print(f"✅ Created test file: {upload_file_path}")
    
    try:
        # Prepare upload data with authentication
        files = {
            'file': (file_name, test_mp3_content, mime_type)
        }
        
        # Use custom upload data if provided, otherwise use defaults
        if upload_data:
            data = upload_data
        else:
            data = {
                'language': 'en',
                'model': 'whisper-1',
                'speaker_diarization': False,
                'auto_delete': 7
            }
        
        print(f"📤 Uploading file: {file_name}")
        print(f"   Size: {len(test_mp3_content)} bytes")
        print(f"   MIME type: {mime_type}")
        print(f"   Upload data: {data}")
        print(f"   Token: {token[:30]}...")
        print()
        
        # Upload file with authentication
        start_time = time.time()
        response = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
        upload_time = time.time() - start_time
        
        print(f"⏱️  Upload took: {upload_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ Upload successful!")
            try:
                result = response.json()
                job_id = result.get('job_id')
                print(f"📄 Job ID: {job_id}")
                print(f"📁 Status: {result.get('status', 'N/A')}")
                print(f"📝 File info: {result.get('file_info', {}).get('original_name', 'N/A')}")
                print(f"📊 File size: {result.get('file_info', {}).get('file_size', 'N/A')} bytes")
                
                # Test 6: Check job status
                if job_id:
                    print(f"\n6. Testing job status for job: {job_id}")
                    status_response = requests.get(
                        f"{backend_url}/api/v1/upload/{job_id}",
                        headers=headers,
                        timeout=10
                    )
                    print(f"📊 Status response: {status_response.status_code}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"📊 Current status: {status_data.get('status')}")
                        print(f"📊 Progress: {status_data.get('progress')}%")
                    
            except json.JSONDecodeError:
                print("⚠️  Response was not valid JSON")
                print(f"📄 Raw response: {response.text}")
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚫 Error message: {error_data.get('detail', 'Unknown error')}")
                print(f"🚫 Error code: {error_data.get('code', 'N/A')}")
            except:
                print(f"🚫 Raw response: {response.text}")
        
    except Exception as e:
        print(f"❌ Upload failed with exception: {e}")
        return False
    
    finally:
        # Clean up test file
        try:
            if Path(test_file_path).exists():
                Path(test_file_path).unlink()
                print(f"🧹 Cleaned up test file: {test_file_path}")
        except:
            pass
    
    return True

def create_test_mp3():
    """Create a minimal MP3 file for testing"""
    # Minimal MP3 header with proper structure
    mp3_header = bytes([
        # ID3v2 header (minimal)
        0x49, 0x44, 0x33, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        
        # Minimal MP3 audio frame (very short silence)
        0xFF, 0xFB, 0x90, 0x00,  # MP3 frame header
        0x00, 0x00, 0x00, 0x00,  # Basic frame data
    ])
    return mp3_header

def create_test_wav():
    """Create a minimal WAV file for testing"""
    # WAV file header + minimal PCM data
    wav_header = bytes([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x08, 0x00, 0x00,  # File size - 8 (little endian)
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        
        # fmt subchunk
        0x66, 0x6d, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Subchunk1Size (16 for PCM)
        0x01, 0x00, 0x01, 0x00,  # AudioFormat (1 for PCM), NumChannels (1)
        0x44, 0xAC, 0x00, 0x00,  # SampleRate (44100)
        0x88, 0x58, 0x01, 0x00,  # ByteRate (44100 * 1 * 16 / 8)
        0x02, 0x00, 0x10, 0x00,  # BlockAlign, BitsPerSample (16)
        
        # data subchunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x10, 0x00, 0x00, 0x00,  # Subchunk2Size (16 bytes of audio)
        
        # Minimal audio data (silence)
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    return wav_header

def test_different_models(backend_url, token):
    """Test different transcription models"""
    print("\n🧪 Testing different transcription models...")
    
    models = ["whisper-1", "whisper-base", "whisper-small"]
    headers = {'Authorization': f'Bearer {token}'}
    
    for model in models:
        print(f"  Testing model: {model}")
        
        # Create small test file
        test_content = create_test_mp3()
        
        files = {
            'file': ('test.mp3', test_content, 'audio/mpeg')
        }
        
        data = {
            'language': 'en',
            'model': model,
            'speaker_diarization': False,
            'auto_delete': 1  # Short-lived for testing
        }
        
        try:
            response = requests.post(
                f"{backend_url}/api/v1/upload/",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"    ✅ {model}: Upload successful")
            else:
                print(f"    ❌ {model}: Upload failed ({response.status_code})")
                
        except Exception as e:
            print(f"    ❌ {model}: Exception - {e}")

def test_different_languages(backend_url, token):
    """Test different language settings"""
    print("\n🌍 Testing different language settings...")
    
    languages = ["en", "es", "fr", "de", "auto"]
    headers = {'Authorization': f'Bearer {token}'}
    
    for lang in languages:
        print(f"  Testing language: {lang}")
        
        # Create small test file
        test_content = create_test_mp3()
        
        files = {
            'file': ('test.mp3', test_content, 'audio/mpeg')
        }
        
        data = {
            'language': lang,
            'model': 'whisper-1',
            'speaker_diarization': False,
            'auto_delete': 1
        }
        
        try:
            response = requests.post(
                f"{backend_url}/api/v1/upload/",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"    ✅ {lang}: Upload successful")
            else:
                print(f"    ❌ {lang}: Upload failed ({response.status_code})")
                
        except Exception as e:
            print(f"    ❌ {lang}: Exception - {e}")

def main():
    """Main test function with command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced MP3 Upload Debug Tool')
    parser.add_argument('--url', default='http://127.0.0.1:8001', 
                       help='Backend URL (default: http://127.0.0.1:8001)')
    parser.add_argument('--file', help='Specific audio file to upload')
    parser.add_argument('--language', default='en',
                       help='Language code (default: en)')
    parser.add_argument('--model', default='whisper-1',
                       help='Model name (default: whisper-1)')
    parser.add_argument('--speaker-diarization', action='store_true',
                       help='Enable speaker diarization')
    parser.add_argument('--test-models', action='store_true',
                       help='Test different models')
    parser.add_argument('--test-languages', action='store_true',
                       help='Test different languages')
    parser.add_argument('--auto-delete', type=int, default=7,
                       help='Auto-delete days (default: 7)')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced MP3 Upload Debug Tool")
    print("=" * 60)
    print(f"Backend URL: {args.url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Prepare upload data
    upload_data = {
        'language': args.language,
        'model': args.model,
        'speaker_diarization': args.speaker_diarization,
        'auto_delete': args.auto_delete
    }
    
    print(f"📋 Upload settings: {upload_data}")
    print()
    
    # Main upload test
    success = test_mp3_upload(args.url, args.file, upload_data)
    
    if success:
        # Additional tests
        token, _ = get_auth_token(args.url)
        
        if token:
            if args.test_models:
                test_different_models(args.url, token)
            
            if args.test_languages:
                test_different_languages(args.url, token)
    
    print("\n" + "=" * 60)
    print("📊 Debug Summary")
    print("=" * 60)
    
    if success:
        print("✅ Upload test completed successfully!")
        print("\n💡 If uploads still fail in React Native app:")
        print("   1. Check CORS headers in browser DevTools")
        print("   2. Verify file size limits in frontend")
        print("   3. Check network tab for API call details")
        print("   4. Ensure authentication tokens are valid")
        print("   5. Check file MIME type matching")
    else:
        print("❌ Upload test failed!")
        print("\n🔧 Common issues:")
        print("   - Backend not running on correct port")
        print("   - File size exceeds limits")
        print("   - Unsupported MIME type")
        print("   - Authentication required")
        print("   - CORS policy blocking request")
        print("   - Database connection issues")
        print("   - Invalid file format")
    
    print(f"\n📋 Command examples:")
    print(f"  python {os.path.basename(__file__)} --file my_audio.mp3")
    print(f"  python {os.path.basename(__file__)} --language es --model whisper-base")
    print(f"  python {os.path.basename(__file__)} --test-models")
    print(f"  python {os.path.basename(__file__)} --test-languages")
    print(f"  python {os.path.basename(__file__)} --speaker-diarization")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
    
    input("\nPress Enter to continue...")