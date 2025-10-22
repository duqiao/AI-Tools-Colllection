#!/usr/bin/env python3
"""
Integration Test Environment Setup
Sets up backend and frontend for integration testing
"""

import subprocess
import sys
import time
import os
import requests
from pathlib import Path
import threading

class IntegrationTestEnvironment:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "react-native-app"
        self.processes = []
        
    def log(self, message, service="MAIN"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{service}] {message}")
        
    def run_command(self, command, description, shell=True, cwd=None):
        """Run a command and return success status"""
        try:
            result = subprocess.run(
                command, 
                shell=shell, 
                cwd=cwd or self.project_root,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                self.log(f"✅ {description}")
                return True
            else:
                self.log(f"❌ {description}: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} (timeout)")
            return False
        except Exception as e:
            self.log(f"❌ {description}: {e}")
            return False
    
    def check_docker(self):
        """Check if Docker is running"""
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def start_docker_services(self):
        """Start MongoDB and Redis Docker services"""
        self.log("Starting Docker database services...")
        
        # Stop any existing services
        self.run_command(
            "docker-compose -f docker-compose.dev.yml down",
            "Stopping existing services"
        )
        
        # Start services
        success = self.run_command(
            "docker-compose -f docker-compose.dev.yml up -d mongodb redis",
            "Starting MongoDB and Redis"
        )
        
        if not success:
            return False
            
        # Wait for services to be ready
        self.log("Waiting for database services to be ready...")
        time.sleep(15)
        
        # Check MongoDB
        mongo_check = self.run_command(
            'docker exec ai-mongodb-dev mongosh --eval "db.adminCommand(\'ping\')"',
            "MongoDB health check"
        )
        
        # Check Redis
        redis_check = self.run_command(
            'docker exec ai-redis-dev redis-cli -a dev123456 ping',
            "Redis health check"
        )
        
        return mongo_check and redis_check
    
    def start_backend(self):
        """Start the backend API server"""
        self.log("Starting backend API server...")
        
        # Check if virtual environment exists
        venv_python = self.backend_dir / "venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            self.log("❌ Backend virtual environment not found")
            return False
            
        # Start backend in background
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            # Start backend process
            process = subprocess.Popen(
                [str(venv_python), "run.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(process)
            self.log("Backend server started")
            
            # Wait for backend to be ready
            self.log("Waiting for backend to be ready...")
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get("http://127.0.0.1:8001/health", timeout=5)
                    if response.status_code == 200:
                        self.log("✅ Backend is ready")
                        return True
                except:
                    pass
                
                time.sleep(1)
                if i % 5 == 0:
                    self.log(f"Still waiting for backend... ({i}s)")
            
            self.log("❌ Backend failed to start within timeout")
            return False
            
        except Exception as e:
            self.log(f"❌ Failed to start backend: {e}")
            return False
    
    def test_backend_endpoints(self):
        """Test basic backend endpoints"""
        self.log("Testing backend endpoints...")
        
        endpoints = [
            ("GET", "http://127.0.0.1:8001/", "Root endpoint"),
            ("GET", "http://127.0.0.1:8001/health", "Health check"),
            ("GET", "http://127.0.0.1:8001/docs", "API documentation"),
        ]
        
        all_passed = True
        for method, url, description in endpoints:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log(f"✅ {description} - OK")
                else:
                    self.log(f"❌ {description} - Status: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log(f"❌ {description} - Error: {e}")
                all_passed = False
        
        return all_passed
    
    def setup_frontend(self):
        """Setup React Native frontend"""
        self.log("Setting up React Native frontend...")
        
        # Check if node_modules exists
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            self.log("Installing frontend dependencies...")
            success = self.run_command(
                "npm install",
                "Installing npm dependencies",
                cwd=self.frontend_dir
            )
            if not success:
                return False
        
        return True
    
    def print_frontend_instructions(self):
        """Print instructions for starting the frontend"""
        self.log("\n" + "="*60)
        self.log("🚀 INTEGRATION TEST ENVIRONMENT READY")
        self.log("="*60)
        
        self.log("\n📋 Environment Summary:")
        self.log(f"   ✅ Backend API: http://127.0.0.1:8001")
        self.log(f"   ✅ MongoDB: localhost:27018")
        self.log(f"   ✅ Redis: localhost:6379")
        self.log(f"   ✅ Frontend: Ready to start")
        
        self.log("\n🌐 Access Points:")
        self.log(f"   📚 API Docs: http://127.0.0.1:8001/docs")
        self.log(f"   ❤️  Health Check: http://127.0.0.1:8001/health")
        
        self.log("\n📱 To Start React Native Frontend:")
        self.log(f"   cd {self.frontend_dir}")
        self.log(f"   npm start")
        
        self.log("\n🔗 Integration Testing:")
        self.log(f"   1. Start React Native with: npm start")
        self.log(f"   2. Open Expo Go app and scan QR code")
        self.log(f"   3. Test file upload and translation features")
        self.log(f"   4. Check API calls in browser network tab")
        
        self.log("\n🛑 To Stop Environment:")
        self.log(f"   Press Ctrl+C to stop backend")
        self.log(f"   docker-compose -f docker-compose.dev.yml down")
    
    def cleanup(self):
        """Clean up processes"""
        self.log("\n🧹 Cleaning up...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
    
    def run(self):
        """Main setup routine"""
        try:
            self.log("🚀 Starting Integration Test Environment Setup")
            self.log("="*60)
            
            # Check prerequisites
            if not self.check_docker():
                self.log("❌ Docker is not running. Please start Docker Desktop first.")
                return False
            
            # Start Docker services
            if not self.start_docker_services():
                self.log("❌ Failed to start Docker services")
                return False
            
            # Start backend
            if not self.start_backend():
                self.log("❌ Failed to start backend")
                return False
            
            # Test backend
            if not self.test_backend_endpoints():
                self.log("❌ Backend endpoint tests failed")
                return False
            
            # Setup frontend
            if not self.setup_frontend():
                self.log("❌ Frontend setup failed")
                return False
            
            # Print instructions
            self.print_frontend_instructions()
            
            # Keep running
            self.log("\n🔄 Keeping environment running... Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.log("\n🛑 Stopping environment...")
            
        except Exception as e:
            self.log(f"❌ Setup failed: {e}")
            return False
        finally:
            self.cleanup()
        
        return True

if __name__ == "__main__":
    env = IntegrationTestEnvironment()
    success = env.run()
    sys.exit(0 if success else 1)