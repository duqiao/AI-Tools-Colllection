#!/usr/bin/env python3
"""
Backend API Debug Tool
Comprehensive debugging script for the AI Media Translation API
"""

import requests
import json
import time
import sys
from pathlib import Path

class APIDebugger:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.user_id = None

    def print_section(self, title):
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print('='*60)

    def print_success(self, message):
        print(f"✅ {message}")

    def print_error(self, message):
        print(f"❌ {message}")

    def print_info(self, message):
        print(f"ℹ️  {message}")

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        self.print_section("Testing Basic Connectivity")
        
        try:
            # Test root endpoint
            response = self.session.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.print_success("Root endpoint accessible")
                data = response.json()
                self.print_info(f"API Version: {data.get('version', 'unknown')}")
                self.print_info(f"Available endpoints: {list(data.get('endpoints', {}).keys())}")
            else:
                self.print_error(f"Root endpoint failed: {response.status_code}")
                return False

            # Test health endpoint
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.print_success("Health check passed")
                data = response.json()
                self.print_info(f"Service status: {data.get('status', 'unknown')}")
            else:
                self.print_error(f"Health check failed: {response.status_code}")
                return False

            return True

        except requests.exceptions.ConnectionError:
            self.print_error("Cannot connect to backend - is it running?")
            self.print_info("Start with: cd backend && python run_windows.py")
            return False
        except Exception as e:
            self.print_error(f"Connection error: {e}")
            return False

    def test_guest_authentication(self):
        """Test guest user creation and authentication"""
        self.print_section("Testing Guest Authentication")
        
        try:
            guest_data = {
                "username": f"DebugUser_{int(time.time())}",
                "openid": f"debug_guest_{int(time.time())}"
            }

            response = self.session.post(
                f"{self.base_url}/auth/guest",
                json=guest_data,
                timeout=10
            )

            if response.status_code == 200:
                self.print_success("Guest user created successfully")
                auth_data = response.json()
                self.token = auth_data.get('token')
                self.user_id = auth_data.get('user', {}).get('id')
                
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.print_success(f"Authentication token received: {self.token[:20]}...")
                    self.print_info(f"User ID: {self.user_id}")
                    return True
                else:
                    self.print_error("No token received in response")
                    return False
            else:
                self.print_error(f"Guest creation failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.print_error(f"Error details: {error_data.get('detail', 'unknown')}")
                except:
                    self.print_error(f"Raw response: {response.text}")
                return False

        except Exception as e:
            self.print_error(f"Authentication error: {e}")
            return False

    def test_user_registration_login(self):
        """Test user registration and login"""
        self.print_section("Testing User Registration and Login")
        
        try:
            # Test registration
            timestamp = int(time.time())
            register_data = {
                "email": f"debug_{timestamp}@test.com",
                "username": f"debuguser_{timestamp}",
                "password": "TestPassword123!",
                "firstName": "Debug",
                "lastName": "User"
            }

            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=register_data,
                timeout=10
            )

            if response.status_code == 200 or response.status_code == 201:
                self.print_success("User registration successful")
                reg_data = response.json()
                self.token = reg_data.get('access_token')
                
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.print_success("Registered user authenticated")
                    return True
            else:
                self.print_error(f"Registration failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.print_error(f"Error: {error_data.get('detail', 'unknown')}")
                except:
                    self.print_error(f"Raw response: {response.text}")

            # Test login with existing user
            login_data = {
                "email": "debug@test.com",
                "password": "TestPassword123!"
            }

            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                timeout=10
            )

            if response.status_code == 200:
                self.print_success("User login successful")
                login_data = response.json()
                self.token = login_data.get('access_token')
                
                if self.token:
                    self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                    self.print_success("User authenticated")
                    return True
            else:
                self.print_error(f"Login failed: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"Auth error: {e}")
            return False

    def test_file_upload(self):
        """Test file upload functionality"""
        self.print_section("Testing File Upload")
        
        if not self.token:
            self.print_error("No authentication token available")
            return False

        try:
            # Create a small test file
            test_content = b"fake_audio_content_for_testing"
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

            self.print_info(f"Uploading test file: {test_filename}")
            self.print_info(f"File size: {len(test_content)} bytes")

            response = self.session.post(
                f"{self.base_url}/upload/",
                files=files,
                data=data,
                timeout=30
            )

            if response.status_code == 200 or response.status_code == 201:
                self.print_success("File upload successful")
                upload_data = response.json()
                job_id = upload_data.get('job_id')
                
                if job_id:
                    self.print_info(f"Job ID: {job_id}")
                    self.print_info(f"Status: {upload_data.get('status')}")
                    self.print_info(f"File info: {upload_data.get('file_info', {})}")
                    return job_id
                else:
                    self.print_error("No job ID in response")
                    return False
            else:
                self.print_error(f"Upload failed: {response.status_code}")
                try:
                    error_data = response.json()
                    self.print_error(f"Error details: {error_data.get('detail', 'unknown')}")
                except:
                    self.print_error(f"Raw response: {response.text}")
                return False

        except Exception as e:
            self.print_error(f"Upload error: {e}")
            return False

    def test_job_status(self, job_id):
        """Test job status checking"""
        self.print_section("Testing Job Status")
        
        if not job_id:
            self.print_error("No job ID provided")
            return False

        try:
            response = self.session.get(
                f"{self.base_url}/upload/{job_id}",
                timeout=10
            )

            if response.status_code == 200:
                self.print_success("Job status retrieved")
                job_data = response.json()
                
                self.print_info(f"Job Status: {job_data.get('status')}")
                self.print_info(f"Progress: {job_data.get('progress')}%")
                self.print_info(f"File: {job_data.get('file_info', {}).get('original_name', 'unknown')}")
                
                # Show processing info if available
                processing_info = job_data.get('processing_info', {})
                if processing_info:
                    self.print_info(f"Started: {processing_info.get('started_at')}")
                    self.print_info(f"Completed: {processing_info.get('completed_at')}")
                
                # Show results if available
                results = job_data.get('results')
                if results:
                    self.print_info(f"Transcription text: {results.get('text', '')[:100]}...")
                    self.print_info(f"Language: {results.get('language')}")
                    self.print_info(f"Confidence: {results.get('confidence')}")
                
                return True
            else:
                self.print_error(f"Status check failed: {response.status_code}")
                return False

        except Exception as e:
            self.print_error(f"Status check error: {e}")
            return False

    def test_user_endpoints(self):
        """Test user management endpoints"""
        self.print_section("Testing User Management")
        
        if not self.token:
            self.print_error("No authentication token available")
            return False

        try:
            # Test user profile
            response = self.session.get(
                f"{self.base_url}/users/profile",
                timeout=10
            )

            if response.status_code == 200:
                self.print_success("User profile retrieved")
                profile = response.json()
                self.print_info(f"Username: {profile.get('username')}")
                self.print_info(f"Email: {profile.get('email')}")
            else:
                self.print_error(f"Profile fetch failed: {response.status_code}")

            # Test user stats
            response = self.session.get(
                f"{self.base_url}/users/stats",
                timeout=10
            )

            if response.status_code == 200:
                self.print_success("User statistics retrieved")
                stats = response.json()
                self.print_info(f"Files uploaded: {stats.get('files', {}).get('total', 0)}")
                self.print_info(f"Transcriptions: {stats.get('transcriptions', {}).get('total', 0)}")
            else:
                self.print_error(f"Stats fetch failed: {response.status_code}")

            return True

        except Exception as e:
            self.print_error(f"User endpoint error: {e}")
            return False

    def test_api_documentation(self):
        """Test API documentation endpoints"""
        self.print_section("Testing API Documentation")
        
        try:
            # Test OpenAPI docs
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            if response.status_code == 200:
                self.print_success("Swagger UI accessible")
            else:
                self.print_error(f"Swagger UI failed: {response.status_code}")

            # Test OpenAPI JSON
            response = self.session.get(f"{self.base_url}/openapi.json", timeout=10)
            if response.status_code == 200:
                self.print_success("OpenAPI schema accessible")
                schema = response.json()
                self.print_info(f"API title: {schema.get('info', {}).get('title')}")
                self.print_info(f"Version: {schema.get('info', {}).get('version')}")
                paths = schema.get('paths', {})
                self.print_info(f"Available endpoints: {len(paths)}")
            else:
                self.print_error(f"OpenAPI schema failed: {response.status_code}")

            return True

        except Exception as e:
            self.print_error(f"Documentation error: {e}")
            return False

    def run_full_debug(self):
        """Run complete debugging suite"""
        print("🚀 Starting Backend API Debug Suite")
        print(f"Target URL: {self.base_url}")
        
        results = {
            'connectivity': False,
            'guest_auth': False,
            'user_auth': False,
            'upload': False,
            'status': False,
            'user_endpoints': False,
            'docs': False
        }

        # Test basic connectivity
        results['connectivity'] = self.test_basic_connectivity()
        if not results['connectivity']:
            self.print_section("Debug Summary")
            self.print_error("Cannot proceed - backend not accessible")
            return results

        # Test authentication (try guest first, then regular)
        results['guest_auth'] = self.test_guest_authentication()
        if not results['guest_auth']:
            results['user_auth'] = self.test_user_registration_login()

        if results['guest_auth'] or results['user_auth']:
            # Test file upload
            job_id = self.test_file_upload()
            results['upload'] = bool(job_id)

            if job_id:
                # Test job status
                results['status'] = self.test_job_status(job_id)

            # Test user endpoints
            results['user_endpoints'] = self.test_user_endpoints()

        # Test documentation
        results['docs'] = self.test_api_documentation()

        # Print summary
        self.print_section("Debug Summary")
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title():<20} {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.print_success("All tests passed! Your API is working correctly.")
        else:
            self.print_error(f"{total - passed} tests failed. Check the errors above.")
        
        return results

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backend API Debug Tool')
    parser.add_argument('--url', default='http://localhost:8001', 
                       help='Backend URL (default: http://localhost:8001)')
    parser.add_argument('--test', choices=['connectivity', 'auth', 'upload', 'status', 'user', 'docs'],
                       help='Run specific test only')
    
    args = parser.parse_args()
    
    debugger = APIDebugger(args.url)
    
    if args.test:
        test_map = {
            'connectivity': debugger.test_basic_connectivity,
            'auth': debugger.test_guest_authentication,
            'upload': lambda: debugger.test_file_upload() and debugger.test_job_status(debugger.test_file_upload()),
            'status': lambda: debugger.test_job_status("test_job_id"),
            'user': debugger.test_user_endpoints,
            'docs': debugger.test_api_documentation
        }
        
        if args.test in test_map:
            test_map[args.test]()
    else:
        debugger.run_full_debug()

if __name__ == "__main__":
    main()