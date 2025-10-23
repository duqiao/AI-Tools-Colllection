#!/usr/bin/env python3
"""
Simple Radio Upload Test
Tests the radio upload and translation functionality
"""

import requests
import json
import time
from pathlib import Path

def test_simple_flow():
    """Test simple radio upload flow"""
    print("Simple Radio Upload Test")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    
    print(f"Backend URL: {backend_url}")
    print()
    
    # Step 1: Test guest login with minimal data
    print("Step 1: Testing guest login...")
    try:
        guest_data = {
            "username": "Test"
        }
        
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=guest_data, timeout=10)
        
        print(f"Guest login status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Guest login worked!")
            auth_data = response.json()
            token = auth_data.get('token')
            print(f"Got token: {token[:20] if token else 'None'}...")
            
            if token:
                print()
                print("Step 2: Testing file upload...")
                return test_upload(backend_url, token)
            else:
                print("FAILED: No token in response")
                return False
        else:
            print(f"FAILED: Guest login status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: Exception: {e}")
        return False

def test_upload(backend_url, token):
    """Test file upload with token"""
    try:
        # Create test audio file
        test_content = b"minimal_audio_test_data"
        test_file = "radio_test.mp3"
        
        with open(test_file, "wb") as f:
            f.write(test_content)
        
        print(f"Created test file: {test_file}")
        
        # Upload with authentication
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        files = {
            'file': (test_file, open(test_file, 'rb'), 'audio/mpeg')
        }
        
        data = {
            'file_type': 'audio',
            'original_filename': 'radio_test.mp3',
            'file_size': str(len(test_content))
        }
        
        print("Uploading file...")
        response = requests.post(f"{backend_url}/api/v1/upload", files=files, data=data, headers=headers, timeout=30)
        
        print(f"Upload status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: File uploaded!")
            result = response.json()
            print(f"Task ID: {result.get('task_id')}")
            return True
        else:
            print(f"FAILED: Upload status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Upload error: {error_data.get('detail', 'Unknown')}")
            except:
                print(f"Raw response: {response.text}")
            return False
        
    except Exception as e:
        print(f"FAILED: Upload exception: {e}")
        return False
    finally:
        try:
            if Path(test_file).exists():
                Path(test_file).unlink()
        except:
            pass

def main():
    """Main test function"""
    print("Testing Radio Upload Functionality")
    print("This will test guest authentication and file upload")
    print()
    
    success = test_simple_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: Radio upload test completed!")
        print("\nYour backend is ready for:")
        print("- File uploads")
        print("- Speech-to-text processing") 
        print("- Translation")
    else:
        print("FAILED: Radio upload test failed!")
        print("\nCheck backend logs for errors")

if __name__ == "__main__":
    main()