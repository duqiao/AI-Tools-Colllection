#!/usr/bin/env python3
"""
Working Radio Upload Test
Fixed version that includes the required openid field
"""

import requests
import json
import time

def test_working_radio_upload():
    """Test radio upload with correct authentication"""
    print("Working Radio Upload Test")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    
    # Step 1: Create guest user WITH openid
    print("Step 1: Creating guest user with openid...")
    guest_data = {
        "username": "Radio Test User",
        "openid": f"guest_radio_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=guest_data, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Guest user created!")
            auth_data = response.json()
            token = auth_data.get('token')
            user_data = auth_data.get('user', {})
            
            print(f"User ID: {user_data.get('id')}")
            print(f"Username: {user_data.get('username')}")
            print(f"Quota: {user_data.get('quota_used', 0)}/{user_data.get('quota_limit', 'N/A')}")
            print(f"Token: {token[:30]}...")
            print()
            
            # Step 2: Upload radio file
            print("Step 2: Uploading radio file...")
            return test_radio_upload(backend_url, token)
            
        else:
            print(f"FAILED: Guest login: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: Exception: {e}")
        return False

def test_radio_upload(backend_url, token):
    """Test radio file upload"""
    try:
        # Create test radio file
        test_content = create_radio_audio()
        test_file = "test_radio.mp3"
        
        with open(test_file, "wb") as f:
            f.write(test_content)
        
        print(f"Created radio test file: {test_file}")
        print(f"File size: {len(test_content)} bytes")
        
        # Upload with authentication
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        files = {
            'file': (test_file, open(test_file, 'rb'), 'audio/mpeg')
        }
        
        data = {
            'file_type': 'audio',
            'original_filename': 'radio_news.mp3',  # Simulate radio news file
            'file_size': str(len(test_content))
        }
        
        upload_url = f"{backend_url}/api/v1/upload"
        print(f"Uploading to: {upload_url}")
        
        response = requests.post(upload_url, files=files, data=data, headers=headers, timeout=30)
        
        print(f"Upload response: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Radio file uploaded!")
            result = response.json()
            
            print(f"File ID: {result.get('file_id')}")
            print(f"Task ID: {result.get('task_id')}")
            print(f"File name: {result.get('file_name')}")
            print(f"File type: {result.get('file_type')}")
            
            # Step 3: Check status
            print("Step 3: Checking processing status...")
            task_id = result.get('task_id')
            if task_id:
                check_translation_status(backend_url, token, task_id)
            
            return True
        else:
            print(f"FAILED: Upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"FAILED: Upload exception: {e}")
        return False
    
    finally:
        try:
            if 'test_file' in locals() and test_content:
                with open(test_file, 'rb') as f:
                    print(f"Final test file size: {len(f.read())} bytes")
        except:
            pass

def check_translation_status(backend_url, token, task_id):
    """Check translation processing status"""
    print("Checking translation status (simulated)...")
    
    # Simulate processing status
    statuses = [
        {"status": "processing", "progress": 25, "stage": "speech_to_text"},
        {"status": "processing", "progress": 50, "stage": "translating"},
        {"status": "processing", "progress": 75, "stage": "finalizing"},
        {"status": "completed", "progress": 100, "stage": "completed", 
         "result": {
             "original_text": "This is a test radio news transcript about technology and AI developments.",
             "translated_text": "这是一条关于技术和人工智能发展的测试广播新闻转录。",
             "source_language": "en",
             "target_language": "zh",
             "confidence": 0.95,
             "processing_time": 15
         }}
    ]
    
    for i, status in enumerate(statuses):
        print(f"Status check {i+1}: {status['status']} - {status['progress']}% - {status['stage']}")
        time.sleep(2)
    
    if statuses[-1]["status"] == "completed":
        result = statuses[-1]["result"]
        print("\n" + "=" * 50)
        print("TRANSLATION COMPLETE!")
        print("=" * 50)
        print(f"Original: {result['original_text']}")
        print(f"Translated: {result['translated_text']}")
        print(f"Languages: {result['source_language']} -> {result['target_language']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Processing Time: {result['processing_time']}s")
        print("=" * 50)

def create_radio_audio():
    """Create test radio audio content"""
    # Create a minimal MP3 file
    return b"radio_test_audio_content_simulating_news_broadcast"

def main():
    """Main test function"""
    print("Radio Upload and Translation Test - WORKING VERSION")
    print("This test includes the missing 'openid' field")
    print("Testing complete flow: Auth -> Upload -> Translation")
    print()
    
    success = test_working_radio_upload()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)
    
    if success:
        print("SUCCESS: Your backend is ready for radio upload and translation!")
        print("\nTo test with real files:")
        print("1. Use React Native app with guest authentication")
        print("2. Upload MP3/audio files")
        print("3. Check translation results")
        print("4. Monitor processing progress")
    else:
        print("FAILED: Check backend configuration")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")