#!/usr/bin/env python3
"""
Simple authentication test to debug the auth flow
"""

import requests
import json
import time

def test_auth():
    """Test authentication flow"""
    backend_url = "http://127.0.0.1:8001"
    
    print("🔐 Testing Authentication Flow")
    print("=" * 40)
    
    # Test 1: Create guest user
    print("1. Creating guest user...")
    guest_data = {
        "username": f"TestUser_{int(time.time())}",
        "openid": f"test_guest_{int(time.time())}"
    }
    
    try:
        response = requests.post(
            f"{backend_url}/api/v1/auth/guest",
            json=guest_data,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   📄 Response: {json.dumps(data, indent=2)}")
            
            # Check for token in different locations
            token = data.get('token') or data.get('user', {}).get('token') or data.get('access_token')
            print(f"   🔑 Token found: {bool(token)}")
            if token:
                print(f"   🔑 Token preview: {token[:30]}...")
            
            return token
        else:
            print(f"   ❌ Failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   🚫 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   🚫 Raw: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def test_upload_with_token(token):
    """Test upload with token"""
    if not token:
        print("❌ No token provided, skipping upload test")
        return
        
    backend_url = "http://127.0.0.1:8001"
    
    print("\n2. Testing upload with token...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    # Create a small test file
    test_content = b"fake mp3 content for testing"
    files = {
        'file': ('test.mp3', test_content, 'audio/mpeg')
    }
    
    data = {
        'language': 'en',
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
        
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   📄 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   🚫 Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   🚫 Raw: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Upload exception: {e}")

if __name__ == "__main__":
    token = test_auth()
    test_upload_with_token(token)
    input("\nPress Enter to continue...")