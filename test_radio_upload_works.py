#!/usr/bin/env python3
import requests
import time

def test_radio_upload():
    """Test radio upload with working authentication"""
    print("Radio Upload Test - Working Version")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    token = None
    
    # Step 1: Create guest user with openid
    print("Creating guest user...")
    guest_data = {
        "username": "Radio Test User",
        "openid": f"guest_radio_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=guest_data, timeout=10)
        
        if response.status_code == 200:
            print("Guest user created successfully")
            auth_data = response.json()
            token = auth_data.get('token')
            print(f"Got token: {token[:20] if token else 'None'}...")
            
            # Step 2: Test upload
            print("Testing file upload...")
            test_content = b"radio_test_content"
            files = {
                'file': ('test_radio.mp3', test_content, 'audio/mpeg')
            }
            data = {
                'file_type': 'audio',
                'original_filename': 'radio_test.mp3',
                'file_size': str(len(test_content))
            }
            
            headers = {'Authorization': f'Bearer {token}'}
            
            upload_response = requests.post(f"{backend_url}/api/v1/upload", files=files, data=data, headers=headers, timeout=30)
            print(f"Upload status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                print("SUCCESS: Radio upload works!")
                result = upload_response.json()
                print(f"Task ID: {result.get('task_id', 'N/A')}")
                return True
            else:
                print(f"Upload failed: {upload_response.status_code}")
                return False
        else:
            print(f"Guest login failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_radio_upload()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
