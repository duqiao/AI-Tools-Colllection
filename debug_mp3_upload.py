#!/usr/bin/env python3
"""
MP3 Upload Debug Tool
Tests MP3 file upload from frontend to backend
"""

import requests
import json
import time
from pathlib import Path

def test_mp3_upload():
    """Test MP3 file upload to debug the issue"""
    print("MP3 Upload Debug Tool")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    api_url = f"{backend_url}/api/v1/upload"
    
    print(f"Backend URL: {api_url}")
    print()
    
    # Test 1: Check if backend is running
    print("1. Testing backend connectivity...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False
    
    # Test 2: Check upload endpoint exists
    print("\n2. Testing upload endpoint...")
    try:
        response = requests.options(api_url, timeout=10)
        print(f"✅ Upload endpoint response: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload endpoint not accessible: {e}")
        return False
    
    # Test 3: Try uploading a small test file
    print("\n3. Testing MP3 file upload...")
    
    # Create a small test MP3 file (just for testing)
    test_mp3_content = create_test_mp3()
    test_file_path = "test_upload.mp3"
    
    try:
        with open(test_file_path, "wb") as f:
            f.write(test_mp3_content)
        
        print(f"✅ Created test MP3 file: {test_file_path}")
        
        # Prepare upload data
        files = {
            'file': (test_file_path, open(test_file_path, 'rb'), 'audio/mpeg')
        }
        
        data = {
            'file_type': 'audio',
            'original_filename': 'test_upload.mp3',
            'file_size': str(len(test_mp3_content))
        }
        
        print(f"📤 Uploading file: {test_file_path}")
        print(f"   Size: {len(test_mp3_content)} bytes")
        print(f"   MIME type: audio/mpeg")
        print()
        
        # Upload file
        start_time = time.time()
        response = requests.post(api_url, files=files, data=data, timeout=30)
        upload_time = time.time() - start_time
        
        print(f"⏱️  Upload took: {upload_time:.2f} seconds")
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
            try:
                result = response.json()
                print(f"📄 File ID: {result.get('file_id', 'N/A')}")
                print(f"📝 File name: {result.get('file_name', 'N/A')}")
                print(f"🔗 Task ID: {result.get('task_id', 'N/A')}")
            except:
                print("⚠️  Response was not valid JSON")
        else:
            print(f"❌ Upload failed with status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"🚫 Error message: {error_data.get('detail', 'Unknown error')}")
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
    # This is a minimal MP3 header with silence
    # MP3 file format: ID3v2 header + MPEG frame
    mp3_header = bytes([
        # ID3v2 header
        0x49, 0x44, 0x33, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        
        # Minimal MPEG audio frame (very short silence)
        0xFF, 0xFB, 0x90, 0x00,  # MPEG header
        0x00, 0x00, 0x00, 0x00,  # Minimal frame data
    ])
    return mp3_header

def test_backend_endpoints():
    """Test various backend endpoints"""
    print("\n4. Testing backend endpoints...")
    backend_url = "http://127.0.0.1:8001"
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/docs", "API documentation"),
        ("/api/v1/upload", "Upload endpoint (POST)"),
    ]
    
    for endpoint, description in endpoints:
        try:
            if endpoint == "/api/v1/upload":
                # For upload endpoint, test OPTIONS request
                response = requests.options(f"{backend_url}{endpoint}", timeout=10)
            else:
                # For other endpoints, test GET request
                response = requests.get(f"{backend_url}{endpoint}", timeout=10)
            
            print(f"   {description}: {response.status_code} {'✅' if 200 <= response.status_code < 300 else '❌'}")
            
        except Exception as e:
            print(f"   {description}: ❌ Error - {e}")

def main():
    """Main test function"""
    print("🔍 Starting MP3 Upload Debug Test")
    print("This will help identify why MP3 uploads are failing")
    print()
    
    # Test backend endpoints first
    test_backend_endpoints()
    
    print("\n" + "=" * 50)
    
    # Test MP3 upload
    success = test_mp3_upload()
    
    print("\n" + "=" * 50)
    print("📊 Debug Summary")
    print("=" * 50)
    
    if success:
        print("✅ MP3 upload test completed")
        print("\n💡 If uploads still fail in React Native app:")
        print("   1. Check CORS headers in browser DevTools")
        print("   2. Verify file size limits in frontend")
        print("   3. Check network tab for API call details")
        print("   4. Ensure authentication tokens are valid")
    else:
        print("❌ MP3 upload test failed")
        print("\n🛠️  Common issues:")
        print("   - Backend not running on correct port")
        print("   - File size exceeds limits")
        print("   - Unsupported MIME type")
        print("   - Authentication required")
        print("   - CORS policy blocking request")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")