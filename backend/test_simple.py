#!/usr/bin/env python3
"""
Simple Backend Test - Tests core API functionality without auth
"""

import asyncio
import httpx
import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

class SimpleBackendTest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        
    async def test_basic_endpoints(self):
        """Test basic endpoints that don't require authentication"""
        print("🏥 Testing Basic Backend Endpoints...")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Root endpoint
        print("📡 Testing Root Endpoint (/)...")
        total_tests += 1
        try:
            response = await self.client.get(self.base_url)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint - Status: {data.get('success')}")
                print(f"   Message: {data.get('message')}")
                print(f"   Version: {data.get('version')}")
                tests_passed += 1
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test 2: Health check
        print("\n🏥 Testing Health Check (/health)...")
        total_tests += 1
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check - Status: {data.get('status')}")
                print(f"   Services: {list(data.get('services', {}).keys())}")
                tests_passed += 1
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test 3: API docs (should be available)
        print("\n📚 Testing API Documentation (/docs)...")
        total_tests += 1
        try:
            response = await self.client.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                print("✅ API documentation available")
                tests_passed += 1
            else:
                print(f"❌ API docs failed: {response.status_code}")
        except Exception as e:
            print(f"❌ API docs error: {e}")
        
        # Test 4: OpenAPI spec
        print("\n📄 Testing OpenAPI Spec (/openapi.json)...")
        total_tests += 1
        try:
            response = await self.client.get(f"{self.base_url}/openapi.json")
            if response.status_code == 200:
                print("✅ OpenAPI spec available")
                tests_passed += 1
            else:
                print(f"❌ OpenAPI spec failed: {response.status_code}")
        except Exception as e:
            print(f"❌ OpenAPI spec error: {e}")
        
        print(f"\n📊 Basic Test Results: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print("🎉 All basic endpoints working!")
            return True
        else:
            print("⚠️ Some basic endpoints failed")
            return False
    
    async def test_server_connectivity(self):
        """Test if server is running"""
        print("🔗 Testing Server Connectivity...")
        try:
            response = await self.client.get(self.base_url, timeout=5.0)
            return response.status_code != 0
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

async def main():
    """Run simple backend tests"""
    print("🧪 Simple Backend Test Suite")
    print("This test checks if your backend API is working properly")
    print("\n📝 Prerequisites:")
    print("1. Backend server running: python run.py")
    print("2. Server accessible at: http://localhost:8000")
    print("3. Required dependencies installed")
    print("\n⏳ Waiting 2 seconds for server startup...")
    
    await asyncio.sleep(2)
    
    tester = SimpleBackendTest()
    
    try:
        # Test server connectivity first
        if not await tester.test_server_connectivity():
            print("\n❌ Server is not running or not accessible")
            print("Please start your server with: python run.py")
            return 1
        
        # Run basic endpoint tests
        success = await tester.test_basic_endpoints()
        
        if success:
            print("\n🎉 Backend API is working correctly!")
            print("\n📋 Next Steps:")
            print("1. Test file upload: curl -X POST http://localhost:8000/api/v1/upload/ -F 'file=@test.mp3'")
            print("2. Test authentication: Run 'python test_e2e.py' for full workflow")
            print("3. Check API docs: Open http://localhost:8000/docs")
            return 0
        else:
            print("\n⚠️ Backend API has issues that need to be resolved")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return 1
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))