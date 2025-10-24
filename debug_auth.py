#!/usr/bin/env python3
"""
Debug Authentication Flow
"""

import requests
import json
import time
from datetime import datetime, timedelta

def test_auth_flow():
    """Test authentication flow step by step"""
    base_url = "http://127.0.0.1:8001"
    
    print("🔐 Authentication Debug Tool")
    print("=" * 50)
    
    # Step 1: Test health check
    print("1. Testing backend connectivity...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Step 2: Test guest authentication
    print("\n2. Testing guest authentication...")
    try:
        guest_data = {
            "username": f"DebugUser_{int(time.time())}",
            "openid": f"debug_guest_{int(time.time())}"
        }
        
        print(f"   Request data: {guest_data}")
        
        response = requests.post(
            f"{base_url}/api/v1/auth/guest",
            json=guest_data,
            timeout=10
        )
        
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            auth_data = response.json()
            print(f"   ✅ Auth successful!")
            print(f"   Token: {auth_data.get('token', 'NO_TOKEN')[:50]}...")
            
            token = auth_data.get('token')
            if not token:
                print("   ❌ No token in response!")
                print(f"   Response: {auth_data}")
                return False
            
            # Step 3: Test token validation
            print("\n3. Testing token validation...")
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test user profile endpoint
            response = requests.get(
                f"{base_url}/api/v1/users/profile",
                headers=headers,
                timeout=10
            )
            
            print(f"   Profile response status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Token validation successful!")
                user_data = response.json()
                print(f"   User: {user_data.get('username', 'unknown')}")
                return token
            else:
                print(f"   ❌ Token validation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', 'unknown')}")
                except:
                    print(f"   Raw response: {response.text}")
                return None
        else:
            print(f"   ❌ Auth failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'unknown')}")
            except:
                print(f"   Raw response: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
        return None

def test_upload_with_token(token, base_url="http://127.0.0.1:8001"):
    """Test upload with provided token"""
    print("\n4. Testing upload with authentication...")
    
    if not token:
        print("   ❌ No token provided")
        return False
    
    try:
        # Create test file
        test_content = b"test_audio_content"
        test_filename = "debug_test.mp3"
        
        files = {
            'file': (test_filename, test_content, 'audio/mpeg')
        }
        
        data = {
            'language': 'en',
            'model': 'whisper-1',
            'speaker_diarization': False,
            'auto_delete': 7
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        print(f"   Headers: {headers}")
        print(f"   File: {test_filename} ({len(test_content)} bytes)")
        
        response = requests.post(
            f"{base_url}/api/v1/upload/",
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )
        
        print(f"   Upload response status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            print("   ✅ Upload successful!")
            try:
                result = response.json()
                print(f"   Job ID: {result.get('job_id', 'N/A')}")
                print(f"   Status: {result.get('status', 'N/A')}")
                return True
            except:
                print("   ⚠️  Invalid JSON response")
                return False
        else:
            print(f"   ❌ Upload failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'unknown')}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False

def decode_jwt_token(token):
    """Debug JWT token decoding"""
    print("\n5. Debugging JWT token...")
    
    try:
        import base64
        from jose import jwt
        
        # Split token
        parts = token.split('.')
        print(f"   Token parts: {len(parts)}")
        
        if len(parts) >= 2:
            # Decode header
            header_data = base64.urlsafe_b64decode(parts[0] + '=' * (-len(parts[0]) % 4))
            print(f"   Header: {header_data}")
            
            # Decode payload
            payload_data = base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4))
            print(f"   Payload: {payload_data}")
            
            # Decode with jose
            try:
                decoded = jwt.decode(token, "test", algorithms=["HS256"])
                print(f"   Decoded (no secret): {decoded}")
            except Exception as e:
                print(f"   Decode error: {e}")
        
    except Exception as e:
        print(f"   Token debug error: {e}")

def main():
    """Main test function"""
    token = test_auth_flow()
    
    if token:
        decode_jwt_token(token)
        test_upload_with_token(token)
    else:
        print("\n❌ Authentication failed, cannot test upload")
    
    print("\n" + "=" * 50)
    print("Debug Summary")
    print("=" * 50)
    
    if token:
        print("✅ Authentication flow completed")
        print("💡 If upload still fails, check:")
        print("   1. Backend logs for detailed error messages")
        print("   2. JWT secret consistency between encode/decode")
        print("   3. Token expiration time")
        print("   4. User permissions and active status")
    else:
        print("❌ Authentication failed")
        print("💡 Check:")
        print("   1. Backend is running on correct port")
        print("   2. Guest authentication endpoint is working")
        print("   3. JWT encoding is not failing")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")