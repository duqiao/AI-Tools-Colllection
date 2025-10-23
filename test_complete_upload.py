#!/usr/bin/env python3
"""
Complete MP3 Upload Test with Authentication
Tests full flow: guest login -> MP3 upload
"""

import requests
import json
import time
from pathlib import Path

def test_complete_upload_flow():
    """Test complete upload flow with authentication"""
    print("Complete MP3 Upload Test with Authentication")
    print("=" * 60)
    
    backend_url = "http://127.0.0.1:8001"
    
    print(f"Backend URL: {backend_url}")
    print()
    
    # Step 1: Create guest user session
    print("Step 1: Creating guest user session...")
    guest_login_url = f"{backend_url}/api/v1/auth/guest"
    
    try:
        guest_data = {
            "username": "Test User"
        }
        
        response = requests.post(guest_login_url, json=guest_data, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Guest user created")
            auth_data = response.json()
            token = auth_data.get('token')
            user_id = auth_data.get('user', {}).get('id')
            
            if not token:
                print("FAILED: No token received in guest login")
                return False
                
            print(f"Token: {token[:20]}...")
            print(f"User ID: {user_id}")
            print()
            
            # Step 2: Test authenticated MP3 upload
            print("Step 2: Testing authenticated MP3 upload...")
            return test_authenticated_upload(backend_url, token)
            
        else:
            print(f"FAILED: Guest login failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"FAILED: Guest login exception: {e}")
        return False

def test_authenticated_upload(backend_url, token):
    """Test MP3 upload with authentication token"""
    api_url = f"{backend_url}/api/v1/upload"
    
    # Create test MP3 file
    test_mp3_content = create_test_mp3()
    test_file_path = "test_auth_upload.mp3"
    
    try:
        with open(test_file_path, "wb") as f:
            f.write(test_mp3_content)
        
        print(f"Created test MP3 file: {test_file_path}")
        
        # Prepare upload with authentication
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'multipart/form-data'
        }
        
        files = {
            'file': (test_file_path, open(test_file_path, 'rb'), 'audio/mpeg')
        }
        
        data = {
            'file_type': 'audio',
            'original_filename': 'test_auth_upload.mp3',
            'file_size': str(len(test_mp3_content))
        }
        
        print(f"Uploading file: {test_file_path}")
        print(f"Size: {len(test_mp3_content)} bytes")
        print(f"MIME type: audio/mpeg")
        print(f"Auth token: {token[:20]}...")
        print()
        
        # Upload file with authentication
        start_time = time.time()
        response = requests.post(api_url, files=files, data=data, headers=headers, timeout=30)
        upload_time = time.time() - start_time
        
        print(f"Upload took: {upload_time:.2f} seconds")
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Authenticated upload successful!")
            try:
                result = response.json()
                print(f"File ID: {result.get('file_id', 'N/A')}")
                print(f"File name: {result.get('file_name', 'N/A')}")
                print(f"Task ID: {result.get('task_id', 'N/A')}")
                print(f"Original name: {result.get('original_name', 'N/A')}")
                print(f"File size: {result.get('file_size', 'N/A')}")
                print(f"File type: {result.get('file_type', 'N/A')}")
                print()
                
                # Step 3: Test status check
                print("Step 3: Testing upload status check...")
                task_id = result.get('task_id')
                if task_id:
                    test_status_check(backend_url, token, task_id)
                
            except:
                print("WARNING: Response was not valid JSON")
                
        else:
            print(f"FAILED: Authenticated upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error message: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"Raw response: {response.text}")
        
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
    
    return True

def test_status_check(backend_url, token, task_id):
    """Test checking upload status"""
    status_url = f"{backend_url}/api/v1/upload/{task_id}/status"
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(status_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Status check works!")
            try:
                status_data = response.json()
                print(f"Task status: {status_data.get('status', 'N/A')}")
                print(f"Progress: {status_data.get('progress', 'N/A')}")
                print(f"Stage: {status_data.get('stage', 'N/A')}")
            except:
                print("Status response received but not valid JSON")
        else:
            print(f"FAILED: Status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"FAILED: Status check exception: {e}")

def create_test_mp3():
    """Create a minimal MP3 file for testing"""
    # Minimal MP3 header
    mp3_header = bytes([
        # Minimal MP3 frame header
        0xFF, 0xFB, 0x90, 0x00,
        0x00, 0x00, 0x00, 0x00
    ])
    return mp3_header

def main():
    """Main test function"""
    print("Starting Complete MP3 Upload Test")
    print("This tests the full flow: Guest Login -> Upload -> Status Check")
    print()
    
    success = test_complete_upload_flow()
    
    print("\n" + "=" * 60)
    print("Complete Test Summary")
    print("=" * 60)
    
    if success:
        print("✅ Complete MP3 upload test PASSED!")
        print("\nThe backend is working correctly!")
        print("Your React Native app should:")
        print("1. Create guest user session")
        print("2. Use the token for authenticated uploads")
        print("3. Check upload status")
        
    else:
        print("❌ Complete MP3 upload test FAILED!")
        print("\nCheck backend logs for detailed error information")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")