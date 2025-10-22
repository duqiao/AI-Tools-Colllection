#!/usr/bin/env python3
"""
Quick Start Script for AI Media Translation Backend
Starts the required Docker services and launches the backend API
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(command, description, shell=True):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"✅ {description} completed successfully")
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def main():
    print("🚀 AI Media Translation Backend - Quick Start")
    print("=" * 50)
    
    # Check Docker
    if not check_docker():
        print("❌ Docker is not running. Please start Docker Desktop first.")
        sys.exit(1)
    
    print("✅ Docker is running")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Step 1: Start Docker databases
    print("\n📦 Starting Docker database services...")
    success = run_command(
        "docker-compose -f docker-compose.dev.yml up -d mongodb redis",
        "Starting MongoDB and Redis services"
    )
    
    if not success:
        print("❌ Failed to start Docker services")
        sys.exit(1)
    
    # Step 2: Wait for services to be ready
    print("\n⏳ Waiting for database services to be ready...")
    time.sleep(10)
    
    # Check MongoDB
    print("\n🔍 Checking service health...")
    run_command(
        'docker exec ai-mongodb-dev mongosh --eval "db.adminCommand(\'ping\')"',
        "MongoDB health check"
    )
    
    # Check Redis
    run_command(
        'docker exec ai-redis-dev redis-cli -a dev123456 ping',
        "Redis health check"
    )
    
    # Step 3: Start backend API
    print("\n🌐 Starting backend API...")
    backend_dir = project_root / "backend"
    os.chdir(backend_dir)
    
    print(f"📂 Backend directory: {backend_dir}")
    print(f"🔗 API will be available at: http://127.0.0.1:8001")
    print(f"📚 API Documentation: http://127.0.0.1:8001/docs")
    print(f"❤️  Health Check: http://127.0.0.1:8001/health")
    
    print("\n🎯 Starting FastAPI server...")
    print("   Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Activate virtual environment and start server
    if os.name == 'nt':  # Windows
        venv_python = backend_dir / "venv" / "Scripts" / "python.exe"
    else:  # Unix/Mac
        venv_python = backend_dir / "venv" / "bin" / "python"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run setup first.")
        sys.exit(1)
    
    # Start the backend server
    try:
        subprocess.run([str(venv_python), "run.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()