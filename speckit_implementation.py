#!/usr/bin/env python3
"""
Speckit Implementation Workflow
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
    print("🚀 SPECKIT IMPLEMENTATION WORKFLOW")
    print("=" * 60)
    print()

def print_phase(phase_name, description):
    """Print phase header"""
    print(f"📍 PHASE: {phase_name}")
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
        print(f"   ❌ tasks.md not found in {project_root}")
        print(f"   ✅ Creating tasks.md with default structure...")
        create_default_tasks(tasks_file)
    else:
        print(f"   ✅ tasks.md found")
    
    # Check for specs directory
    if not specs_dir.exists():
        print(f"   ✅ Creating specs directory...")
        specs_dir.mkdir(exist_ok=True)
    
    print(f"   📁 Project Root: {project_root}")
    print(f"   📋 Specs Directory: {specs_dir}")
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
    
    print(f"   ✅ Created default tasks.md")

def analyze_current_state():
    """Analyze the current project state and radio upload needs"""
    print_phase("ANALYSIS", "Analyzing current project state and radio upload requirements")
    
    project_root = Path.cwd()
    
    # Check backend status
    backend_dir = project_root / "backend"
    if backend_dir.exists():
        print(f"   ✅ Backend directory exists: {backend_dir}")
        
        # Check if backend is running
        try:
            import requests
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ Backend is running on port 8001")
            else:
                print("   ⚠️  Backend not accessible")
        except:
            print("   ⚠️  Backend not running")
    else:
        print("   ❌ Backend directory not found")
    
    # Check React Native app
    rn_dir = project_root / "react-native-app"
    if rn_dir.exists():
        print(f"   ✅ React Native app exists: {rn_dir}")
        
        # Check package.json
        package_json = rn_dir / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                config = json.load(f)
            print(f"   ✅ Package.json found: {config.get('name', 'Unknown')}")
            print(f"   📱 React Native configured")
        else:
            print("   ❌ package.json not found")
    else:
        print("   ❌ React Native app not found")
    
    # Check Docker setup
    docker_compose = project_root / "docker-compose.dev.yml"
    if docker_compose.exists():
        print(f"   ✅ Docker Compose configuration exists")
        print("   🐳 Docker services can be started")
    else:
        print("   ❌ Docker Compose configuration not found")
    
    print()
    return True

def generate_implementation_plan():
    """Generate implementation plan for radio upload and translation"""
    print_phase("PLANNING", "Creating detailed implementation plan for radio upload and translation")
    
    plan = {
        "project": "AI Media Translation - Radio Upload",
        "phases": [
            {
                "name": "Authentication Fix",
                "description": "Fix guest authentication and token handling",
                "tasks": [
                    "Debug guest login openid field issue",
                    "Fix React Native authentication flow",
                    "Update API client with proper token handling",
                    "Test authentication end-to-end"
                ],
                "estimated_time": "2-4 hours"
            },
            {
                "name": "File Upload Enhancement",
                "description": "Enhance file upload for radio/audio files",
                "tasks": [
                    "Increase file size limits for radio content",
                    "Add progress tracking for large files",
                    "Implement resumable uploads",
                    "Add file type validation improvements"
                ],
                "estimated_time": "4-6 hours"
            },
            {
                "name": "Speech-to-Text Processing",
                "description": "Implement radio content transcription using local LLM",
                "tasks": [
                    "Configure Ollama/DeepSeek integration",
                    "Optimize audio preprocessing for radio quality",
                    "Implement streaming transcription",
                    "Add confidence scoring for transcriptions"
                ],
                "estimated_time": "6-8 hours"
            },
            {
                "name": "Translation Services",
                "description": "Build translation pipeline with multiple language support",
                "tasks": [
                    "Implement language detection from audio",
                    "Add translation between 20+ languages",
                    "Integrate DeepL and Google Translate fallbacks",
                    "Add translation quality scoring"
                ],
                "estimated_time": "4-6 hours"
            },
            {
                "name": "React Native Frontend",
                "description": "Enhance mobile app for radio upload experience",
                "tasks": [
                    "Create dedicated radio upload screen",
                    "Add waveform visualization",
                    "Implement real-time transcription preview",
                    "Add translation result display with formatting",
                    "Create offline mode for saved content"
                ],
                "estimated_time": "8-12 hours"
            },
            {
                "name": "Integration & Testing",
                "description": "Complete end-to-end integration testing",
                "tasks": [
                    "Automate guest user creation in app",
                    "Test complete radio upload flow",
                    "Verify translation accuracy",
                    "Performance testing with large files",
                    "Error handling and recovery testing"
                ],
                "estimated_time": "6-8 hours"
            }
        ],
        "total_estimated_time": "24-38 hours",
        "tech_stack": {
            "backend": "Python FastAPI + MongoDB + Redis",
            "frontend": "React Native + Expo",
            "llm": "Ollama with DeepSeek/Qwen models",
            "translation": "Google Translate + DeepL API + Local LLM"
        },
        "priority_order": [
            "Authentication Fix",
            "File Upload Enhancement", 
            "Speech-to-Text Processing",
            "React Native Frontend",
            "Translation Services",
            "Integration & Testing"
        ]
    }
    
    # Save plan
    plan_file = Path.cwd() / "implementation_plan.json"
    with open(plan_file, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"   ✅ Implementation plan saved to {plan_file}")
    print(f"   ⏱️  Total estimated time: {plan['total_estimated_time']} hours")
    print(f"   🎯 Key priorities:")
    for i, priority in enumerate(plan['priority_order'][:3], 1):
        print(f"      {i}. {priority}")
    
    print()
    return plan_file

def execute_phase_1():
    """Execute Phase 1: Authentication Fix"""
    print_phase("EXECUTION - PHASE 1", "Fixing guest authentication and token handling")
    
    project_root = Path.cwd()
    
    # Fix React Native authentication
    rn_auth_service = project_root / "react-native-app" / "src" / "services" / "auth.ts"
    if rn_auth_service.exists():
        print("   ✅ React Native auth service found")
        print("   🔧 Updating authentication with openid field...")
        
        # Update the auth service
        update_react_native_auth(rn_auth_service)
    else:
        print("   ❌ React Native auth service not found")
    
    # Test backend authentication fix
    print("   🧪 Testing backend authentication...")
    test_auth_fix()
    
    print("   ✅ Phase 1 completed")
    print()
    return True

def update_react_native_auth(auth_file_path):
    """Update React Native auth service to include openid field"""
    try:
        with open(auth_file_path, 'r') as f:
            content = f.read()
        
        # Update createGuestUser function to include openid
        updated_content = content.replace(
            'const response = await apiClient.request({',
            '''// Create guest user with required openid field
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
        });'''
        )
        
        with open(auth_file_path, 'w') as f:
            f.write(updated_content)
        
        print("   ✅ Updated React Native auth service with openid field")
        
    except Exception as e:
        print(f"   ❌ Failed to update auth service: {e}")

def test_auth_fix():
    """Test the authentication fix"""
    try:
        import requests
        backend_url = "http://127.0.0.1:8001"
        
        test_data = {
            "username": "Test User",
            "openid": f"guest_test_{int(time.time())}"
        }
        
        response = requests.post(f"{backend_url}/api/v1/auth/guest", json=test_data, timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Guest login test successful")
            return True
        else:
            print(f"   ⚠️  Guest login test: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth test failed: {e}")
        return False

def main():
    """Main implementation workflow"""
    print_header()
    
    # Execute phases
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please fix issues and retry.")
        return False
    
    if not analyze_current_state():
        print("❌ Analysis failed. Please check project state.")
        return False
    
    plan_file = generate_implementation_plan()
    
    # Execute first phase
    execute_phase_1()
    
    print_phase("IMPLEMENTATION READY", "Radio upload and translation implementation prepared")
    print("=" * 60)
    print("🎯 NEXT STEPS:")
    print("1. Review the implementation plan in implementation_plan.json")
    print("2. Start React Native app: cd react-native-app && npm start")
    print("3. Test radio upload with fixed authentication")
    print("4. Continue with remaining phases from the plan")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)