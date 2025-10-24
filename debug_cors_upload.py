#!/usr/bin/env python3
"""
Debug script to test CORS and upload endpoint issues
"""

import requests
import json
from datetime import datetime

def test_cors_and_upload():
    """Test CORS preflight and upload functionality"""
    print("🔍 CORS and Upload Debug Test")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    
    # Test both with and without trailing slash
    upload_url = f"{backend_url}/api/v1/upload"
    upload_url_with_slash = f"{backend_url}/api/v1/upload/"
    
    print(f"Backend URL: {backend_url}")
    print(f"Upload URL: {upload_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: CORS preflight request (without slash)
    print("1. Testing CORS preflight request (without trailing slash)...")
    try:
        cors_headers = {
            'Origin': 'http://localhost:19006',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Authorization, Content-Type',
        }
        
        response = requests.options(upload_url, headers=cors_headers, timeout=10)
        print(f"   ✅ CORS OPTIONS Status: {response.status_code}")
        print(f"   📋 URL: {upload_url}")
        print(f"   📋 CORS Headers:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"      {header}: {value}")
        print()
        
    except Exception as e:
        print(f"   ❌ CORS OPTIONS failed: {e}")
        print()

    # Test 1b: CORS preflight request (with slash)
    print("1b. Testing CORS preflight request (with trailing slash)...")
    try:
        cors_headers = {
            'Origin': 'http://localhost:19006',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Authorization, Content-Type',
        }
        
        response = requests.options(upload_url_with_slash, headers=cors_headers, timeout=10)
        print(f"   ✅ CORS OPTIONS Status: {response.status_code}")
        print(f"   📋 URL: {upload_url_with_slash}")
        print(f"   📋 CORS Headers:")
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                print(f"      {header}: {value}")
        print()
        
    except Exception as e:
        print(f"   ❌ CORS OPTIONS failed: {e}")
        print()
    
    # Test 2: Health check
    print("2. Testing backend health...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"   ✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   📄 Health data: {response.json()}")
        print()
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        print()
    
    # Test 3: Get authentication token
    print("3. Getting auth token...")
    try:
        auth_response = requests.post(
            f"{backend_url}/api/v1/auth/guest",
            json={
                "username": f"DebugUser_{int(datetime.now().timestamp())}",
                "openid": f"debug_guest_{int(datetime.now().timestamp())}"
            },
            timeout=10
        )
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            token = auth_data.get('token') or auth_data.get('user', {}).get('token')
            print(f"   ✅ Auth successful: {auth_response.status_code}")
            print(f"   🔑 Token: {token[:30]}..." if token else "No token found")
            print()
            
            if token:
                # Test 4: Actual upload with small test file
                print("4. Testing actual upload...")
                
                # Create a small test file content
                test_content = b"fake audio content for testing"
                
                files = {
                    'file': ('test.mp3', test_content, 'audio/mpeg')
                }
                
                data = {
                    'language': 'en',
                    'model': 'whisper-1',
                    'speaker_diarization': False,
                    'auto_delete': 1
                }
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Origin': 'http://localhost:19006'
                }
                
                print(f"   📤 Upload URL: {upload_url}")
                print(f"   📤 Headers: {headers}")
                print(f"   📤 Data: {data}")
                print()
                
                upload_response = requests.post(
                    upload_url, 
                    files=files, 
                    data=data, 
                    headers=headers, 
                    timeout=30
                )
                
                print(f"   📊 Upload Status: {upload_response.status_code}")
                print(f"   📊 Upload Headers:")
                for header, value in upload_response.headers.items():
                    print(f"      {header}: {value}")
                print()
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    print(f"   ✅ Upload successful!")
                    print(f"   📄 Job ID: {result.get('job_id')}")
                    print(f"   📊 Response: {json.dumps(result, indent=2)}")
                else:
                    print(f"   ❌ Upload failed: {upload_response.status_code}")
                    try:
                        error_data = upload_response.json()
                        print(f"   🚫 Error: {json.dumps(error_data, indent=2)}")
                    except:
                        print(f"   🚫 Raw response: {upload_response.text}")
            else:
                print("   ❌ No token received, skipping upload test")
                
        else:
            print(f"   ❌ Auth failed: {auth_response.status_code}")
            try:
                error_data = auth_response.json()
                print(f"   🚫 Auth error: {error_data}")
            except:
                print(f"   🚫 Auth response: {auth_response.text}")
                
    except Exception as e:
        print(f"   ❌ Auth error: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Debug Summary")
    print("=" * 50)
    print("If CORS preflight fails:")
    print("  - Check backend CORS configuration")
    print("  - Verify allowed origins include your frontend URL")
    print("  - Ensure OPTIONS method is allowed")
    print()
    print("If upload fails:")
    print("  - Verify authentication token is valid")
    print("  - Check file size and type limits")
    print("  - Ensure upload directory exists")
    print("  - Check backend logs for errors")

if __name__ == "__main__":
    test_cors_and_upload()
    input("\nPress Enter to continue...")