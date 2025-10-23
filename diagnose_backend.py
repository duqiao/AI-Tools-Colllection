#!/usr/bin/env python3
"""
Backend Diagnostic Tool
Checks backend configuration and potential issues
"""

import requests
import subprocess
import time

def diagnose_backend():
    """Diagnose backend issues"""
    print("Backend Diagnostic Tool")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    
    print(f"Testing backend at: {backend_url}")
    print()
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("SUCCESS: Backend is accessible")
        else:
            print(f"ISSUE: Health check failed: {response.status_code}")
    except Exception as e:
        print(f"ISSUE: Cannot connect: {e}")
        return
    
    # Test 2: Guest login endpoint
    print("\n2. Testing guest login endpoint...")
    try:
        test_data = {
            "username": "Test User",
            "openid": "test_openid_diagnostic"
        }
        
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=test_data, timeout=10)
        
        print(f"Guest login status: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS: Guest login works")
            print("Your authentication is functioning correctly")
        elif response.status_code == 422:
            print("ISSUE: Validation error - missing required fields")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Raw response: {response.text}")
        elif response.status_code == 500:
            print("ISSUE: Server error - backend problem")
            print("This indicates a backend configuration or database issue")
            
            # Check if backend logs show anything
            print("\nBackend diagnostic suggestions:")
            print("1. Check if MongoDB is running: docker exec ai-mongodb-dev mongosh --eval 'db.runCommand(\"ping\")'")
            print("2. Check if Redis is running: docker exec ai-redis-dev redis-cli -a dev123456 ping")
            print("3. Check backend logs in terminal")
            print("4. Check if Ollama is running for LLM processing")
        else:
            print(f"ISSUE: Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ISSUE: Exception during guest login: {e}")
    
    # Test 3: Upload endpoint structure
    print("\n3. Testing upload endpoint structure...")
    try:
        response = requests.options(f"{backend_url}/api/v1/upload", timeout=10)
        print(f"Upload endpoint status: {response.status_code}")
        
        if response.status_code in [200, 204, 405]:
            print("SUCCESS: Upload endpoint exists")
        else:
            print(f"ISSUE: Upload endpoint problem: {response.status_code}")
            
    except Exception as e:
        print(f"ISSUE: Upload endpoint test failed: {e}")
    
    # Test 4: Configuration check
    print("\n4. Testing backend configuration...")
    try:
        response = requests.get(f"{backend_url}/", timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Backend name: {data.get('message', 'N/A')}")
                print(f"Backend version: {data.get('version', 'N/A')}")
            except:
                print("SUCCESS: Root endpoint accessible")
    except Exception as e:
        print(f"ISSUE: Configuration check failed: {e}")
    
    print("\n" + "=" * 50)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 50)
    
    print("\nWhat to do next:")
    print("1. If guest login works (status 200):")
    print("   - Your backend is ready")
    print("   - Start React Native app: cd react-native-app && npm start")
    print("   - Test file upload in the app")
    
    print("\n2. If guest login fails (status 422/500):")
    print("   - Check Docker services are running")
    print("   - Check backend logs for errors")
    print("   - Verify backend configuration")
    
    print("\n3. For immediate testing:")
    print("   - Use Swagger UI: http://127.0.0.1:8001/docs")
    print("   - Test endpoints manually in browser")

if __name__ == "__main__":
    diagnose_backend()
    input("\nPress Enter to continue...")