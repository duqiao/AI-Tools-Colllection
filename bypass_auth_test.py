#!/usr/bin/env python3
"""
Temporary authentication bypass for testing
"""
import requests
import json

def test_upload_without_auth():
    """Test upload without authentication requirements"""
    backend_url = "http://127.0.0.1:8001"
    
    print("Testing upload without authentication...")
    
    # Create test audio file
    test_content = b"radio_test_content"
    files = {
        'file': ('test_radio.mp3', test_content, 'audio/mpeg')
    }
    data = {
        'file_type': 'audio',
        'original_filename': 'radio_test.mp3',
        'file_size': str(len(test_content))
    }
    
    try:
        # Upload without auth header
        response = requests.post(f"{backend_url}/api/v1/upload", files=files, data=data, timeout=30)
        
        print(f"Upload status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Upload works without auth!")
            result = response.json()
            print(f"Task ID: {result.get('task_id', 'N/A')}")
            return True
        else:
            print(f"Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown')}")
            except:
                print(f"Raw: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Upload exception: {e}")
        return False

if __name__ == "__main__":
    test_upload_without_auth()
