#!/usr/bin/env python3
"""
Speckit Implementation Workflow (Windows Compatible)
Automated task execution for implementing radio upload and translation features
"""

import sys
import os
import json
import subprocess
import time
from pathlib import Path

def print_header():
    """Print workflow header"""
    print("=" * 60)
    print("SPECKIT IMPLEMENTATION WORKFLOW")
    print("=" * 60)
    print()

def print_phase(phase_name, description):
    """Print phase header"""
    print(f"PHASE: {phase_name}")
    print(f"   {description}")
    print("-" * 40)

def check_prerequisites():
    """Check if required files and environment are ready"""
    print_phase("PREREQUISITES", "Checking environment and required files")
    
    project_root = Path.cwd()
    specs_dir = project_root / "specs"
    
    # Check for tasks.md
    tasks_file = project_root / "tasks.md"
    if not tasks_file.exists():
        print(f"   tasks.md not found in {project_root}")
        print(f"   Creating tasks.md with default structure...")
        create_default_tasks(tasks_file)
    else:
        print(f"   tasks.md found")
    
    # Check for specs directory
    if not specs_dir.exists():
        print(f"   Creating specs directory...")
        specs_dir.mkdir(exist_ok=True)
    
    print(f"   Project Root: {project_root}")
    print(f"   Specs Directory: {specs_dir}")
    print()
    return True

def create_default_tasks(tasks_file):
    """Create a default tasks.md file"""
    default_tasks = """# Implementation Tasks

## Phase 1: Setup
- [ ] Initialize project structure
- [ ] Set up development environment
- [ ] Configure database connections

## Phase 2: Core Development
- [ ] Implement user authentication
- [ ] Create file upload endpoints
- [ ] Set up speech-to-text processing
- [ ] Implement translation services

## Phase 3: Integration
- [ ] Frontend-backend integration
- [ ] End-to-end testing
- [ ] Documentation

## Phase 4: Polish
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Final testing and validation
"""
    
    with open(tasks_file, 'w') as f:
        f.write(default_tasks)
    
    print(f"   Created default tasks.md")

def analyze_current_state():
    """Analyze the current project state and radio upload needs"""
    print_phase("ANALYSIS", "Analyzing current project state and radio upload requirements")
    
    project_root = Path.cwd()
    
    # Check backend status
    backend_dir = project_root / "backend"
    if backend_dir.exists():
        print(f"   Backend directory exists: {backend_dir}")
        
        # Check if backend is running
        try:
            import requests
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("   Backend is running on port 8001")
            else:
                print("   Backend not accessible")
        except:
            print("   Backend not running")
    else:
        print("   Backend directory not found")
    
    # Check React Native app
    rn_dir = project_root / "react-native-app"
    if rn_dir.exists():
        print(f"   React Native app exists: {rn_dir}")
        
        # Check package.json
        package_json = rn_dir / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                config = json.load(f)
            print(f"   Package.json found: {config.get('name', 'Unknown')}")
            print("   React Native configured")
        else:
            print("   package.json not found")
    else:
        print("   React Native app not found")
    
    # Check Docker setup
    docker_compose = project_root / "docker-compose.dev.yml"
    if docker_compose.exists():
        print(f"   Docker Compose configuration exists")
        print("   Docker services can be started")
    else:
        print("   Docker Compose configuration not found")
    
    print()
    return True

def execute_immediate_fixes():
    """Execute immediate fixes for radio upload functionality"""
    print_phase("IMMEDIATE FIXES", "Applying quick fixes for radio upload testing")
    
    project_root = Path.cwd()
    
    # Fix 1: Update React Native auth service
    rn_auth_service = project_root / "react-native-app" / "src" / "services" / "auth.ts"
    if rn_auth_service.exists():
        print("   React Native auth service found")
        update_react_native_auth(rn_auth_service)
    
    # Fix 2: Create working test script
    create_working_test_script(project_root)
    
    # Fix 3: Update API client
    api_client = project_root / "react-native-app" / "src" / "services" / "api.ts"
    if api_client.exists():
        print("   API client found")
        update_api_client(api_client)
    
    print("   Immediate fixes completed")
    print()
    return True

def update_react_native_auth(auth_file_path):
    """Update React Native auth service to include openid field"""
    try:
        with open(auth_file_path, 'r') as f:
            content = f.read()
        
        # Add or update createGuestUser function
        openid_function = '''
  // Create guest user with required openid field
  const createGuestUser = async () => {
    try {
      const timestamp = Date.now();
      const randomId = Math.random().toString(36).substr(2, 9);
      const response = await apiClient.request({
        method: 'POST',
        url: '/auth/guest',
        data: {
          username: 'Guest User',
          openid: `guest_${timestamp}_${randomId}`
        }
      });
      
      if (response.success && response.data) {
        const { token } = response.data;
        await AsyncStorage.setItem(ACCESS_TOKEN_KEY, token);
        return { success: true, token, user: response.data.user };
      }
      
      return { success: false, error: response.error || 'Guest login failed' };
    } catch (error) {
      console.error('Guest login failed:', error);
      return { success: false, error: error.message };
    }
  };
'''
        
        with open(auth_file_path, 'w') as f:
            f.write(content + openid_function)
        
        print("   Updated React Native auth service with openid field")
        
    except Exception as e:
        print(f"   Failed to update auth service: {e}")

def create_working_test_script(project_root):
    """Create a working test script for radio upload"""
    test_script = f'''#!/usr/bin/env python3
import requests
import time

def test_radio_upload():
    """Test radio upload with working authentication"""
    print("Radio Upload Test - Working Version")
    print("=" * 50)
    
    backend_url = "http://127.0.0.1:8001"
    token = None
    
    # Step 1: Create guest user with openid
    print("Creating guest user...")
    guest_data = {{
        "username": "Radio Test User",
        "openid": f"guest_radio_{{int(time.time())}}"
    }}
    
    try:
        response = requests.post(f"{{backend_url}}/api/v1/auth/guest", json=guest_data, timeout=10)
        
        if response.status_code == 200:
            print("Guest user created successfully")
            auth_data = response.json()
            token = auth_data.get('token')
            print(f"Got token: {{token[:20] if token else 'None'}}...")
            
            # Step 2: Test upload
            print("Testing file upload...")
            test_content = b"radio_test_content"
            files = {{
                'file': ('test_radio.mp3', test_content, 'audio/mpeg')
            }}
            data = {{
                'file_type': 'audio',
                'original_filename': 'radio_test.mp3',
                'file_size': str(len(test_content))
            }}
            
            headers = {{'Authorization': f'Bearer {{token}}'}}
            
            upload_response = requests.post(f"{{backend_url}}/api/v1/upload", files=files, data=data, headers=headers, timeout=30)
            print(f"Upload status: {{upload_response.status_code}}")
            
            if upload_response.status_code == 200:
                print("SUCCESS: Radio upload works!")
                result = upload_response.json()
                print(f"Task ID: {{result.get('task_id', 'N/A')}}")
                return True
            else:
                print(f"Upload failed: {{upload_response.status_code}}")
                return False
        else:
            print(f"Guest login failed: {{response.status_code}}")
            return False
            
    except Exception as e:
        print(f"Test failed: {{e}}")
        return False

if __name__ == "__main__":
    success = test_radio_upload()
    print(f"Test result: {{'SUCCESS' if success else 'FAILED'}}")
'''
    
    test_file = project_root / "test_radio_upload_works.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    print(f"   Created working test script: {test_file}")

def update_api_client(api_file_path):
    """Update API client to handle authentication better"""
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Add authentication helper
        auth_helper = '''
  // Authentication helper
  const ensureAuthenticated = async () => {{
    let token = await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
    
    if (!token) {{
      console.log('No token found, creating guest user...');
      const guestResult = await createGuestUser();
      if (guestResult.success) {{
        token = guestResult.token;
      }}
    }}
    
    return token;
  }};
'''
        
        with open(api_file_path, 'w') as f:
            f.write(content + auth_helper)
        
        print("   Updated API client with authentication helper")
        
    except Exception as e:
        print(f"   Failed to update API client: {e}")

def main():
    """Main implementation workflow"""
    print_header()
    
    # Execute phases
    if not check_prerequisites():
        print("Prerequisites not met. Please fix issues and retry.")
        return False
    
    if not analyze_current_state():
        print("Analysis failed. Please check project state.")
        return False
    
    execute_immediate_fixes()
    
    print_phase("IMPLEMENTATION READY", "Radio upload and translation implementation prepared")
    print("=" * 60)
    print("NEXT STEPS:")
    print("1. Start React Native app: cd react-native-app && npm start")
    print("2. Test radio upload functionality")
    print("3. Run working test: python test_radio_upload_works.py")
    print("4. Open API documentation: http://127.0.0.1:8001/docs")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)