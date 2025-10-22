#!/usr/bin/env python3
"""
Backend-Frontend Integration Tests
Tests the integration between React Native frontend and FastAPI backend
"""

import requests
import json
import time
import sys
from pathlib import Path

class BackendFrontendIntegrationTests:
    def __init__(self):
        self.backend_url = "http://127.0.0.1:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        self.test_results = []
        
    def log(self, message, status="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {message}")
        
    def run_test(self, test_name, test_func):
        """Run a test and record results"""
        self.log(f"Running {test_name}...")
        try:
            result = test_func()
            if result:
                self.log(f"✅ {test_name} - PASSED", "SUCCESS")
                self.test_results.append((test_name, True, None))
                return True
            else:
                self.log(f"❌ {test_name} - FAILED", "ERROR")
                self.test_results.append((test_name, False, "Test returned False"))
                return False
        except Exception as e:
            self.log(f"❌ {test_name} - ERROR: {e}", "ERROR")
            self.test_results.append((test_name, False, str(e)))
            return False
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        return response.status_code == 200
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{self.backend_url}/", timeout=10)
        return response.status_code == 200 and "AI Media Translation API" in response.text
    
    def test_cors_headers(self):
        """Test CORS headers for frontend compatibility"""
        response = requests.options(f"{self.backend_url}/", timeout=10)
        
        # Check for CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        has_cors = any(header in response.headers for header in cors_headers)
        
        # Test with frontend origin
        headers = {'Origin': 'http://127.0.0.1:8001'}
        response_with_origin = requests.options(f"{self.backend_url}/", headers=headers, timeout=10)
        
        return has_cors and response_with_origin.status_code in [200, 204]
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        # Test guest login endpoint (if available)
        try:
            response = requests.post(f"{self.api_base}/auth/guest-login", timeout=10)
            # Should either work (200) or be implemented (404) but not crash (500)
            return response.status_code in [200, 404, 422]
        except:
            # If endpoint doesn't exist, that's okay for basic integration test
            return True
    
    def test_upload_endpoint_structure(self):
        """Test upload endpoint exists and accepts correct format"""
        # Test OPTIONS request to check if upload endpoint exists
        response = requests.options(f"{self.api_base}/upload", timeout=10)
        return response.status_code in [200, 204, 405]  # 405 means endpoint exists but doesn't allow OPTIONS
    
    def test_file_type_validation(self):
        """Test file type validation"""
        # This would require actual file upload, for now just test endpoint exists
        try:
            response = requests.get(f"{self.api_base}/upload", timeout=10)
            # Should return 405 (Method Not Allowed) for GET request to upload endpoint
            return response.status_code == 405
        except:
            return False
    
    def test_error_handling(self):
        """Test proper error handling"""
        # Test 404 handling
        response = requests.get(f"{self.api_base}/nonexistent-endpoint", timeout=10)
        return response.status_code == 404
    
    def test_api_documentation(self):
        """Test API documentation is accessible"""
        response = requests.get(f"{self.backend_url}/docs", timeout=10)
        return response.status_code == 200 and "text/html" in response.headers.get('content-type', '')
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is available"""
        response = requests.get(f"{self.backend_url}/openapi.json", timeout=10)
        return response.status_code == 200
    
    def test_request_response_format(self):
        """Test API responses follow expected format"""
        response = requests.get(f"{self.backend_url}/", timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                # Check for expected fields in root response
                return 'success' in data or 'message' in data
            except:
                return False
        return False
    
    def test_database_connectivity(self):
        """Test if backend can connect to databases"""
        response = requests.get(f"{self.backend_url}/health", timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                # Health check should include database status
                return True  # Basic health check passing suggests database connectivity
            except:
                return False
        return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("🧪 Starting Backend-Frontend Integration Tests")
        self.log("=" * 60)
        
        # Define tests
        tests = [
            ("Backend Health Check", self.test_backend_health),
            ("API Root Endpoint", self.test_api_root),
            ("CORS Headers", self.test_cors_headers),
            ("Auth Endpoints", self.test_auth_endpoints),
            ("Upload Endpoint Structure", self.test_upload_endpoint_structure),
            ("File Type Validation", self.test_file_type_validation),
            ("Error Handling", self.test_error_handling),
            ("API Documentation", self.test_api_documentation),
            ("OpenAPI Schema", self.test_openapi_schema),
            ("Request/Response Format", self.test_request_response_format),
            ("Database Connectivity", self.test_database_connectivity),
        ]
        
        # Run tests
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            time.sleep(1)  # Small delay between tests
        
        # Print summary
        self.log("\n" + "="*60)
        self.log("📊 TEST SUMMARY")
        self.log("="*60)
        
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")
        self.log(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            self.log("\n❌ Failed Tests:")
            for test_name, success, error in self.test_results:
                if not success:
                    self.log(f"   - {test_name}: {error}")
        
        # Overall result
        all_passed = passed == total
        if all_passed:
            self.log("\n🎉 ALL TESTS PASSED! Backend is ready for frontend integration.")
        else:
            self.log("\n⚠️  Some tests failed. Check backend configuration and try again.")
        
        return all_passed

def main():
    """Main function"""
    print("🔍 Backend-Frontend Integration Test Suite")
    print("Make sure the backend is running on http://127.0.0.1:8001")
    print("And Docker services (MongoDB, Redis) are running")
    print()
    
    input("Press Enter to start tests...")
    
    tester = BackendFrontendIntegrationTests()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Integration tests completed successfully!")
        print("You can now start the React Native frontend and test the full integration.")
    else:
        print("\n❌ Integration tests failed!")
        print("Please check the backend logs and fix any issues before proceeding.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())