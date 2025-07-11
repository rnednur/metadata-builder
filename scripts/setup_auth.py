#!/usr/bin/env python3
"""
Simple Authentication Setup CLI

Quick setup script for the multi-user authentication system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    print("🔐 Metadata Builder Authentication Setup")
    print("=" * 45)
    
    # Check if .env file exists
    env_file = project_root / '.env'
    if not env_file.exists():
        print("❌ No .env file found!")
        print("   Create one by copying env.example:")
        print("   cp env.example .env")
        print("   Then configure your database settings.")
        return False
    
    print("✅ .env file found")
    
    # Ask user for schema name
    schema_name = input("\n📁 Enter schema name (default: metadata_builder): ").strip()
    if not schema_name:
        schema_name = 'metadata_builder'
    
    # Set environment variable
    os.environ['AUTH_SCHEMA'] = schema_name
    
    print(f"🏗️  Using schema: {schema_name}")
    
    # Confirm before proceeding
    proceed = input("\n🚀 Create tables and default admin user? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("❌ Setup cancelled")
        return False
    
    # Import and run the table creator
    try:
        from scripts.create_user_tables import main as create_tables
        success = create_tables()
        
        if success:
            print("\n🎉 Setup completed successfully!")
            print(f"📁 Schema: {schema_name}")
            print("👤 Admin login: admin / admin123")
            print("⚠️  CHANGE THE DEFAULT PASSWORD!")
            return True
        else:
            print("\n❌ Setup failed - check logs for details")
            return False
            
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 