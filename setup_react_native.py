#!/usr/bin/env python3
"""
React Native App Setup and Fix Script
Cleans up dependency issues and sets up the React Native app
"""

import subprocess
import sys
import os
from pathlib import Path

class ReactNativeSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.react_native_dir = self.project_root / "react-native-app"
        
    def log(self, message, status="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {message}")
        
    def run_command(self, command, description, cwd=None, shell=True):
        """Run a command and handle output"""
        try:
            self.log(f"Running: {command}")
            result = subprocess.run(
                command,
                shell=shell,
                cwd=cwd or self.react_native_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.log(f"✅ {description} completed successfully")
                if result.stdout.strip():
                    self.log(f"Output: {result.stdout.strip()[:200]}...")
                return True
            else:
                self.log(f"❌ {description} failed")
                self.log(f"Error: {result.stderr.strip()}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} timed out")
            return False
        except Exception as e:
            self.log(f"❌ {description} failed: {e}")
            return False
    
    def cleanup_node_modules(self):
        """Clean up existing node_modules and package-lock.json"""
        self.log("Cleaning up existing Node.js modules...")
        
        # Remove node_modules
        node_modules = self.react_native_dir / "node_modules"
        if node_modules.exists():
            try:
                import shutil
                shutil.rmtree(node_modules)
                self.log("Removed node_modules directory")
            except Exception as e:
                self.log(f"Could not remove node_modules: {e}")
        
        # Remove package-lock.json
        package_lock = self.react_native_dir / "package-lock.json"
        if package_lock.exists():
            package_lock.unlink()
            self.log("Removed package-lock.json")
        
        # Clear npm cache
        self.run_command("npm cache clean --force", "Clearing npm cache")
        return True
    
    def install_dependencies(self):
        """Install React Native dependencies"""
        self.log("Installing React Native dependencies...")
        
        # Use npm install with legacy peer deps to resolve conflicts
        success = self.run_command(
            "npm install --legacy-peer-deps",
            "Installing dependencies with legacy peer deps"
        )
        
        if not success:
            # Try with --force as fallback
            self.log("Trying with --force flag...")
            success = self.run_command(
                "npm install --force",
                "Installing dependencies with force flag"
            )
        
        return success
    
    def verify_installation(self):
        """Verify the installation was successful"""
        self.log("Verifying installation...")
        
        # Check if key dependencies are installed
        checks = [
            ("React", self.react_native_dir / "node_modules" / "react"),
            ("React Native", self.react_native_dir / "node_modules" / "react-native"),
            ("Expo", self.react_native_dir / "node_modules" / "expo"),
            ("Axios", self.react_native_dir / "node_modules" / "axios"),
        ]
        
        all_good = True
        for name, path in checks:
            if path.exists():
                self.log(f"✅ {name} installed")
            else:
                self.log(f"❌ {name} not found")
                all_good = False
        
        return all_good
    
    def test_expo_command(self):
        """Test if Expo CLI works"""
        return self.run_command("npx expo --version", "Testing Expo CLI")
    
    def create_fix_script(self):
        """Create a Windows batch file for easy fixes"""
        batch_content = """@echo off
echo React Native App Fix Script
echo ==========================

cd /d "%~dp0react-native-app"

echo Cleaning up...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del package-lock.json

echo Clearing npm cache...
npm cache clean --force

echo Installing dependencies...
npm install --legacy-peer-deps

echo Verifying installation...
if exist node_modules\react (
    echo ✅ React installed successfully
) else (
    echo ❌ React installation failed
)

echo.
echo Setup complete! You can now run:
echo   cd react-native-app
echo   npm start

pause
"""
        
        batch_file = self.project_root / "fix-react-native.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        self.log(f"Created fix script: {batch_file}")
    
    def print_instructions(self):
        """Print next steps"""
        self.log("\n" + "="*60)
        self.log("🎉 React Native Setup Complete!")
        self.log("="*60)
        
        self.log("\n📱 Next Steps:")
        self.log("1. Start the backend:")
        self.log("   cd backend")
        self.log("   python run.py")
        
        self.log("\n2. Start React Native app:")
        self.log("   cd react-native-app")
        self.log("   npm start")
        
        self.log("\n3. Test integration:")
        self.log("   - Scan QR code with Expo Go app")
        self.log("   - Test file upload features")
        self.log("   - Verify API connectivity")
        
        self.log("\n🔧 If you encounter issues:")
        self.log("   - Run: fix-react-native.bat")
        self.log("   - Or manually: cd react-native-app && npm install --legacy-peer-deps")
        
        self.log("\n📚 Documentation:")
        self.log("   - React Native Guide: REACT_NATIVE_GUIDE.md")
        self.log("   - Integration Tests: python test_integration.py")
    
    def run(self):
        """Main setup process"""
        try:
            self.log("🚀 React Native Setup and Fix")
            self.log("="*50)
            
            # Check if React Native directory exists
            if not self.react_native_dir.exists():
                self.log("❌ react-native-app directory not found")
                return False
            
            # Change to React Native directory
            os.chdir(self.react_native_dir)
            
            # Clean up existing installation
            if not self.cleanup_node_modules():
                self.log("❌ Cleanup failed")
                return False
            
            # Install dependencies
            if not self.install_dependencies():
                self.log("❌ Dependency installation failed")
                return False
            
            # Verify installation
            if not self.verify_installation():
                self.log("❌ Installation verification failed")
                return False
            
            # Test Expo CLI
            if not self.test_expo_command():
                self.log("⚠️  Expo CLI test failed, but setup may still work")
            
            # Create fix script
            self.create_fix_script()
            
            # Print instructions
            self.print_instructions()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Setup failed: {e}")
            return False

if __name__ == "__main__":
    import time
    
    setup = ReactNativeSetup()
    success = setup.run()
    
    if success:
        print("\n✅ React Native setup completed successfully!")
    else:
        print("\n❌ React Native setup failed!")
        print("Please check the error messages above and try again.")
    
    sys.exit(0 if success else 1)