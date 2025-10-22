#!/usr/bin/env python3
"""
Backend Accessibility Test
Tests if the backend API is accessible for React Native frontend
"""

import requests
import json
import socket

def get_local_ip():
    """Get the local IP address for device testing"""
    try:
        # Create a socket to connect to an external address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def test_backend_accessibility():
    """Test backend API accessibility"""
    print("🔍 Testing Backend API Accessibility")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    local_ip = get_local_ip()
    
    print(f"🌐 Local IP: {local_ip}")
    print(f"🔗 Backend URL: {backend_url}")
    
    tests = [
        ("Health Check", f"{backend_url}/health"),
        ("API Root", f"{backend_url}/"),
        ("API Documentation", f"{backend_url}/docs"),
        ("OpenAPI Schema", f"{backend_url}/openapi.json"),
    ]
    
    results = []
    
    for test_name, url in tests:
        try:
            response = requests.get(url, timeout=10)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            results.append((test_name, response.status_code == 200))
            print(f"{status} {test_name}: {url}")
            
            if response.status_code == 200:
                content_length = len(response.content)
                content_type = response.headers.get('content-type', 'unknown')
                print(f"      Content-Type: {content_type}")
                print(f"      Content-Length: {content_length} bytes")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ FAIL {test_name}: Connection refused")
            results.append((test_name, False))
        except requests.exceptions.Timeout:
            print(f"❌ FAIL {test_name}: Timeout")
            results.append((test_name, False))
        except Exception as e:
            print(f"❌ FAIL {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ Backend is fully accessible!")
        
        print(f"\n📱 For React Native device testing, use:")
        print(f"   API_BASE_URL: http://{local_ip}:8001/api/v1")
        print(f"   Health Check: http://{local_ip}:8001/health")
        
        print(f"\n🔧 Update React Native configuration:")
        print(f"   In react-native-app/src/services/api.ts:")
        print(f"   const API_BASE_URL = 'http://{local_ip}:8001/api/v1';")
        
    else:
        print("❌ Backend has accessibility issues!")
        print("\n🛠️  Troubleshooting:")
        print("   1. Ensure backend is running: python backend/run.py")
        print("   2. Check port 8001 is not blocked by firewall")
        print("   3. Verify Docker services are running")
        print("   4. Check backend logs for errors")
    
    return passed == total

if __name__ == "__main__":
    success = test_backend_accessibility()
    exit(0 if success else 1)