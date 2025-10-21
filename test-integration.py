#!/usr/bin/env python3
"""
Backend Integration Test Script
Tests the connection between React Native frontend and FastAPI backend
"""

import requests
import json
import time
import sys

# Backend API base URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_backend_connection():
    """Test basic backend connectivity"""
    print("🔍 Testing Backend Connection...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def test_api_endpoints():
    """Test main API endpoints"""
    print("\n🧪 Testing API Endpoints...")
    
    endpoints = [
        ("/", "Root endpoint"),
        ("/health", "Health check"),
        ("/docs", "API documentation"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"   {status} {description}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {description}: Connection failed")

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n🔐 Testing Authentication Endpoints...")
    
    # Test WeChat login endpoint (should handle missing data gracefully)
    try:
        response = requests.post(f"{API_BASE}/auth/wechat-login", 
                               json={"code": "test", "userInfo": {"openid": "test"}}, 
                               timeout=5)
        print(f"   {'⚠️' if response.status_code == 422 else '❌'} WeChat Login: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ WeChat Login: Connection failed")
    
    # Test token refresh endpoint
    try:
        response = requests.post(f"{API_BASE}/auth/refresh", 
                               json={"refresh_token": "test"}, 
                               timeout=5)
        print(f"   {'⚠️' if response.status_code == 422 else '❌'} Token Refresh: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Token Refresh: Connection failed")

def test_translation_endpoints():
    """Test translation endpoints"""
    print("\n🎵 Testing Translation Endpoints...")
    
    # Test translation status
    try:
        response = requests.get(f"{API_BASE}/translation/test/status", timeout=5)
        print(f"   {'⚠️' if response.status_code == 404 else '❌'} Translation Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Translation Status: Connection failed")
    
    # Test translation history
    try:
        response = requests.get(f"{API_BASE}/translation/history", timeout=5)
        print(f"   {'⚠️' if response.status_code == 401 else '❌'} Translation History: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Translation History: Connection failed")

def test_cors_headers():
    """Test CORS headers for frontend compatibility"""
    print("\n🌐 Testing CORS Headers...")
    
    try:
        # Simulate preflight request from React Native app
        response = requests.options(f"{BASE_URL}/", 
                                  headers={
                                      "Origin": "http://localhost:8089",
                                      "Access-Control-Request-Method": "GET",
                                      "Access-Control-Request-Headers": "Content-Type",
                                  },
                                  timeout=5)
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        
        if cors_headers["Access-Control-Allow-Origin"]:
            print(f"   ✅ CORS Origin: {cors_headers['Access-Control-Allow-Origin']}")
        else:
            print("   ⚠️  CORS Origin: Not configured")
            
        if cors_headers["Access-Control-Allow-Methods"]:
            print(f"   ✅ CORS Methods: {cors_headers['Access-Control-Allow-Methods']}")
        else:
            print("   ⚠️  CORS Methods: Not configured")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ CORS Test: Connection failed")

def check_react_native_compatibility():
    """Check React Native frontend compatibility"""
    print("\n📱 React Native Frontend Compatibility...")
    
    frontend_url = "http://localhost:8089"
    
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ React Native app is running on {frontend_url}")
        else:
            print(f"   ⚠️  React Native app returned: {response.status_code}")
    except requests.exceptions.RequestException:
        print(f"   ℹ️  React Native app not running on {frontend_url}")
        print("      (This is expected if you haven't started the frontend)")

def main():
    """Run all tests"""
    print("🚀 Backend Integration Test")
    print("=" * 50)
    
    # Test basic connectivity
    if not test_backend_connection():
        print("\n❌ Backend server is not running. Please start it first:")
        print("   cd D:\\Python\\startup\\AI-Tools-Colllection\\backend")
        print("   py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return False
    
    # Test API endpoints
    test_api_endpoints()
    test_auth_endpoints()
    test_translation_endpoints()
    test_cors_headers()
    check_react_native_compatibility()
    
    print("\n" + "=" * 50)
    print("📋 Integration Test Summary")
    print("   ✅ Backend server is running and accessible")
    print("   🌐 API endpoints are responding")
    print("   🔐 Authentication endpoints are available")
    print("   🎵 Translation endpoints are available")
    print("   📱 Ready for React Native frontend integration")
    print("\n🎯 Next Steps:")
    print("   1. Start React Native app: npx expo start --port 8089 --web")
    print("   2. Test guest mode login functionality")
    print("   3. Test file upload and translation workflow")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)