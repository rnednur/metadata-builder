#!/usr/bin/env python3
"""
Fix Authentication Dependencies

This script fixes JWT library compatibility issues by:
1. Uninstalling problematic jose libraries
2. Installing compatible PyJWT
3. Verifying the installation
"""

import subprocess
import sys
import importlib

def run_command(command):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {command}")
        print(f"   Error: {e.stderr}")
        return False

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} imports successfully")
        return True
    except ImportError as e:
        print(f"❌ {module_name} import failed: {e}")
        return False

def main():
    print("🔧 Fixing Authentication Dependencies")
    print("=" * 40)
    
    # Step 1: Uninstall problematic jose libraries
    print("\n1. Removing problematic jose libraries...")
    uninstall_commands = [
        "pip uninstall python-jose -y",
        "pip uninstall python-jwt -y",
        "pip uninstall jose -y"
    ]
    
    for cmd in uninstall_commands:
        run_command(cmd)
    
    # Step 2: Install compatible dependencies
    print("\n2. Installing compatible dependencies...")
    install_commands = [
        "pip install PyJWT==2.8.0",
        "pip install passlib[bcrypt]==1.7.4",
        "pip install cryptography==41.0.7"
    ]
    
    success = True
    for cmd in install_commands:
        if not run_command(cmd):
            success = False
    
    # Step 3: Test imports
    print("\n3. Testing imports...")
    test_modules = [
        "jwt",
        "passlib",
        "cryptography"
    ]
    
    for module in test_modules:
        if not test_import(module):
            success = False
    
    # Step 4: Test JWT functionality
    print("\n4. Testing JWT functionality...")
    try:
        import jwt
        from datetime import datetime, timedelta
        
        # Test token creation and verification
        secret = "test-secret"
        payload = {"test": "data", "exp": datetime.utcnow() + timedelta(minutes=5)}
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        
        print("✅ JWT encode/decode test passed")
        
        # Test exception handling
        try:
            jwt.decode("invalid.token.format", secret, algorithms=["HS256"])
        except (jwt.DecodeError, jwt.InvalidSignatureError, Exception):
            print("✅ JWT exception handling works")
        
    except Exception as e:
        print(f"❌ JWT test failed: {e}")
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Authentication dependencies fixed successfully!")
        print("   You can now run: python scripts/setup_auth.py")
    else:
        print("❌ Some issues remain - check error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 