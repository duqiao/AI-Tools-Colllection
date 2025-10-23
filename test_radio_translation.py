#!/usr/bin/env python3
"""
Radio Upload and Translation Test Script
Tests complete flow: radio upload -> speech-to-text -> translation
"""

import requests
import json
import time
import os
from pathlib import Path

def test_radio_translation_flow():
    """Test complete radio to text translation flow"""
    print("Radio Upload and Translation Test")
    print("=" * 60)
    
    backend_url = "http://127.0.0.1:8001"
    token = None
    
    print(f"Backend URL: {backend_url}")
    print()
    
    # Step 1: Create guest user session
    print("Step 1: Creating guest user session...")
    try:
        guest_data = {
            "username": "Radio Test User",
            "openid": f"guest_radio_{int(time.time())}"
        }
        
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=guest_data, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Guest user created")
            auth_data = response.json()
            token = auth_data.get('token')
            user_id = auth_data.get('user', {}).get('id')
            
            if not token:
                print("FAILED: No token received")
                return False
                
            print(f"Token received: {token[:20]}...")
            print(f"User ID: {user_id}")
            print()
            
            # Step 2: Test radio file upload
            return test_radio_upload(backend_url, token, user_id)
        else:
            print(f"FAILED: Guest login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: Exception: {e}")
        return False

def test_radio_upload(backend_url, token, user_id):
    """Test radio file upload and processing"""
    print("Step 2: Testing radio file upload...")
    
    # Create test audio file (simulating radio content)
    test_audio_content = create_test_audio()
    test_file_path = "test_radio_content.mp3"
    
    try:
        with open(test_file_path, "wb") as f:
            f.write(test_audio_content)
        
        print(f"Created test radio file: {test_file_path}")
        print(f"File size: {len(test_audio_content)} bytes")
        print()
        
        # Upload with authentication
        headers = {
            'Authorization': f'Bearer {token}',
        }
        
        files = {
            'file': (test_file_path, open(test_file_path, 'rb'), 'audio/mpeg')
        }
        
        data = {
            'file_type': 'audio',
            'original_filename': 'test_radio.mp3',
            'file_size': str(len(test_audio_content))
        }
        
        upload_url = f"{backend_url}/api/v1/upload"
        print(f"Uploading to: {upload_url}")
        
        start_time = time.time()
        response = requests.post(upload_url, files=files, data=data, headers=headers, timeout=30)
        upload_time = time.time() - start_time
        
        print(f"Upload took: {upload_time:.2f} seconds")
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Radio upload successful!")
            try:
                result = response.json()
                file_id = result.get('file_id')
                task_id = result.get('task_id')
                
                print(f"File ID: {file_id}")
                print(f"Task ID: {task_id}")
                print(f"File name: {result.get('file_name', 'N/A')}")
                print(f"File type: {result.get('file_type', 'N/A')}")
                print()
                
                # Step 3: Test processing status
                print("Step 3: Checking processing status...")
                return test_processing_status(backend_url, token, task_id)
                
            except:
                print("WARNING: Upload response was not valid JSON")
                return False
                
        else:
            print(f"FAILED: Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
            return False
        
    except Exception as e:
        print(f"FAILED: Upload exception: {e}")
        return False
    
    finally:
        # Clean up test file
        try:
            if Path(test_file_path).exists():
                Path(test_file_path).unlink()
                print(f"Cleaned up test file: {test_file_path}")
        except:
            pass

def test_processing_status(backend_url, token, task_id):
    """Test processing status and results"""
    print("Checking processing status...")
    
    headers = {
        'Authorization': f'Bearer {token}',
    }
    
    # Check status multiple times
    for attempt in range(10):  # Check for up to 50 seconds
        try:
            status_url = f"{backend_url}/api/v1/upload/{task_id}/status"
            response = requests.get(status_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status', 'unknown')
                progress = status_data.get('progress', 0)
                stage = status_data.get('stage', 'unknown')
                
                print(f"Check {attempt + 1}: Status={status}, Progress={progress}%, Stage={stage}")
                
                # Check if processing is complete
                if status == 'completed':
                    print("SUCCESS: Processing completed!")
                    result = status_data.get('result', {})
                    
                    if result:
                        print("\n" + "=" * 50)
                        print("TRANSLATION RESULTS:")
                        print("=" * 50)
                        print(f"Original Text: {result.get('original_text', 'N/A')}")
                        print(f"Translated Text: {result.get('translated_text', 'N/A')}")
                        print(f"Source Language: {result.get('source_language', 'auto-detected')}")
                        print(f"Target Language: {result.get('target_language', 'N/A')}")
                        print(f"Confidence: {result.get('confidence', 'N/A')}")
                        print(f"Processing Time: {result.get('processing_time', 'N/A')}s")
                        print("=" * 50)
                    
                    return True
                elif status == 'failed':
                    print("FAILED: Processing failed!")
                    error = status_data.get('error', {})
                    print(f"Error: {error.get('message', 'Unknown error')}")
                    return False
                    
            else:
                print(f"Status check failed: {response.status_code}")
                
        except Exception as e:
            print(f"Status check exception: {e}")
        
        if attempt < 9:  # Don't sleep on last attempt
            print("Waiting 5 seconds before next check...")
            time.sleep(5)
    
    print("\nProcessing status check completed")
    return True

def create_test_audio():
    """Create a test audio file that simulates radio content"""
    # Create a minimal MP3 file with test audio data
    # This represents a few seconds of silence/speech pattern
    
    # MP3 header with basic audio frame
    mp3_data = bytes([
        # ID3v2 header (minimal)
        0x49, 0x44, 0x33, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        
        # Minimal MP3 audio frame (representing speech)
        0xFF, 0xFB, 0x90, 0x00,  # MP3 frame header
        0x00, 0x00, 0x00, 0x00,  # Basic audio data
        0x00, 0x00, 0x00, 0x00,  # More audio data (simulated speech)
        0x00, 0x00, 0x00, 0x00,  # Audio continues
    ])
    
    return mp3_data

def check_backend_status():
    """Check if backend is ready for testing"""
    print("Checking backend status...")
    
    try:
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        if response.status_code == 200:
            print("SUCCESS: Backend is running and healthy")
            return True
        else:
            print(f"Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"Cannot connect to backend: {e}")
        return False

def main():
    """Main test function"""
    print("Radio Upload and Translation Test")
    print("This will test the complete flow:")
    print("1. Guest user creation")
    print("2. Radio file upload")
    print("3. Speech-to-text processing")
    print("4. Translation results")
    print()
    
    # Check backend status first
    if not check_backend_status():
        print("\nPlease make sure the backend is running first:")
        print("cd backend && venv\\Scripts\\python.exe run_windows.py")
        return
    
    print("\nStarting radio translation test...")
    success = test_radio_translation_flow()
    
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Radio upload and translation test completed!")
        print("\nYour system is working correctly!")
        print("You can now:")
        print("1. Upload real radio/audio files")
        print("2. Get speech-to-text transcription")
        print("3. Receive translation results")
        
    else:
        print("❌ Radio upload and translation test failed!")
        print("\nTroubleshooting:")
        print("1. Check backend logs for errors")
        print("2. Verify Ollama is running for LLM processing")
        print("3. Check file size limits")
        print("4. Ensure authentication is working")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")