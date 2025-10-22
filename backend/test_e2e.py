#!/usr/bin/env python3
"""
End-to-End Test Suite for Backend API Integration
Tests the complete workflow: upload → transcription → results
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

class BackendE2ETest:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user = None
        self.auth_token = None
        
    async def setup_test_user(self):
        """Setup or get test user credentials"""
        print("🔧 Setting up test user...")
        
        # Try to register a test user
        user_data = {
            "email": "test@example.com",
            "username": "testuser123",
            "password": "testpassword123",
            "firstName": "Test",
            "lastName": "User"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            if response.status_code in [200, 201]:
                print("✅ Test user registered successfully")
            elif response.status_code == 409:
                print("ℹ️ Test user already exists, proceeding with login")
            else:
                print(f"⚠️ User registration status: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"⚠️ User registration failed: {e}")
        
        # Login to get auth token
        login_data = {
            "email": "test@example.com", 
            "password": "testpassword123"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            )
            if response.status_code == 200:
                auth_result = response.json()
                self.auth_token = auth_result.get("access_token")
                self.test_user = auth_result.get("user", {})
                print("✅ User login successful")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def test_health_check(self):
        """Test health check endpoint"""
        print("\n🏥 Testing Health Check...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed")
                print(f"   Status: {health_data.get('status')}")
                print(f"   Version: {health_data.get('version')}")
                
                # Check service status
                services = health_data.get("services", {})
                for service, status in services.items():
                    if status.get("status") == "connected" or status.get("status") == "available":
                        print(f"   ✅ {service}: {status.get('status')}")
                    else:
                        print(f"   ⚠️ {service}: {status.get('status')}")
                
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_file_upload(self):
        """Test file upload with a simulated audio file"""
        print("\n📁 Testing File Upload...")
        
        # Create a test audio file (simulated MP3 content)
        test_audio_path = "test_audio.mp3"
        test_content = b"fake audio content for testing"  # Minimal test content
        
        try:
            # Create test file
            with open(test_audio_path, "wb") as f:
                f.write(test_content)
            
            # Test upload
            with open(test_audio_path, "rb") as f:
                files = {
                    "file": (test_audio_path, f, "audio/mpeg")
                }
                data = {
                    "language": "en",
                    "model": "whisper-1"
                }
                
                headers = {
                    "Authorization": f"Bearer {self.auth_token}" if self.auth_token else None
                }
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/upload/",
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    upload_result = response.json()
                    job_id = upload_result.get("task_id")
                    print(f"✅ File upload successful")
                    print(f"   Job ID: {job_id}")
                    print(f"   File size: {upload_result.get('file_info', {}).get('file_size', 0)} bytes")
                    return job_id
                else:
                    print(f"❌ File upload failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
        finally:
            # Cleanup test file
            if os.path.exists(test_audio_path):
                os.remove(test_audio_path)
    
    async def test_job_status(self, job_id):
        """Test job status checking"""
        print(f"\n📊 Testing Job Status for Job ID: {job_id}")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/upload/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                job_data = response.json()
                print(f"✅ Job status retrieved")
                print(f"   Status: {job_data.get('status')}")
                print(f"   Progress: {job_data.get('progress', 0)}%")
                
                # Check if job has results
                if job_data.get("results") and job_data.get("status") == "completed":
                    print(f"   ✅ Transcription completed")
                    print(f"   Text length: {len(job_data['results'].get('full_text', ''))}")
                    print(f"   Language: {job_data['results'].get('language', 'unknown')}")
                
                return job_data
            else:
                print(f"⚠️ Job status check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Job status error: {e}")
            return None
    
    async def test_user_profile(self):
        """Test user profile endpoint"""
        print("\n👤 Testing User Profile...")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}"
            }
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                print(f"✅ User profile retrieved")
                print(f"   Username: {profile_data.get('username')}")
                print(f"   Email: {profile_data.get('email')}")
                return True
            else:
                print(f"⚠️ Profile check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Profile error: {e}")
            return False
    
    async def test_root_endpoint(self):
        """Test root API endpoint"""
        print("\n🏠 Testing Root Endpoint...")
        
        try:
            response = await self.client.get(self.base_url)
            
            if response.status_code == 200:
                root_data = response.json()
                print(f"✅ Root endpoint working")
                print(f"   API: {root_data.get('message')}")
                print(f"   Version: {root_data.get('version')}")
                return True
            else:
                print(f"⚠️ Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
            return False
    
    async def run_full_e2e_test(self):
        """Run complete end-to-end test"""
        print("🚀 Starting End-to-End Backend Test")
        print("=" * 50)
        
        # Test 1: Health check
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Health check failed - stopping test")
            return False
        
        # Test 2: Root endpoint
        root_ok = await self.test_root_endpoint()
        if not root_ok:
            print("❌ Root endpoint failed - stopping test")
            return False
        
        # Test 3: Authentication setup
        auth_ok = await self.setup_test_user()
        if not auth_ok:
            print("❌ Authentication failed - stopping test")
            return False
        
        # Test 4: User profile (with auth)
        profile_ok = await self.test_user_profile()
        if not profile_ok:
            print("⚠️ User profile test failed, continuing...")
        
        # Test 5: File upload (with auth)
        job_id = await self.test_file_upload()
        if not job_id:
            print("❌ File upload failed - stopping test")
            return False
        
        # Test 6: Job status checking (with auth)
        job_status = await self.test_job_status(job_id)
        
        print("\n" + "=" * 50)
        print("📊 End-to-End Test Summary:")
        print(f"   Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"   Root Endpoint: {'✅ PASS' if root_ok else '❌ FAIL'}")
        print(f"   Authentication: {'✅ PASS' if auth_ok else '❌ FAIL'}")
        print(f"   User Profile: {'✅ PASS' if profile_ok else '❌ FAIL'}")
        print(f"   File Upload: {'✅ PASS' if job_id else '❌ FAIL'}")
        print(f"   Job Status: {'✅ PASS' if job_status else '❌ FAIL'}")
        
        # Overall result
        all_tests_passed = all([health_ok, root_ok, auth_ok, profile_ok, bool(job_id), bool(job_status)])
        
        if all_tests_passed:
            print("\n🎉 ALL TESTS PASSED! Backend is ready for production!")
            print("\n📋 Ready for React Native integration")
        else:
            print("\n⚠️ Some tests failed. Check logs and configuration.")
        
        return all_tests_passed
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()

async def main():
    """Main test runner"""
    print("🔧 Backend E2E Test Suite")
    print("Make sure your backend is running: python run.py")
    print("Waiting 3 seconds for server startup...")
    
    await asyncio.sleep(3)
    
    tester = BackendE2ETest()
    
    try:
        success = await tester.run_full_e2e_test()
        return 0 if success else 1
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