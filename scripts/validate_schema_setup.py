
#!/usr/bin/env python3
"""
Schema Setup Validation Utility

This script validates that your multi-user authentication schema is properly configured.
"""

import os
import sys
import yaml
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "metadata_builder" / "config" / "config.yaml"
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

def check_environment_variables():
    """Check if required environment variables are set"""
    required_env_vars = [
        'AUTH_SCHEMA',
        'JWT_SECRET_KEY', 
        'SESSION_ENCRYPTION_KEY',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

def check_database_connection():
    """Test database connection"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return False, "DATABASE_URL not set"
        
        # Parse the URL
        result = urlparse(database_url)
        
        # Test connection
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port or 5432,
            database=result.path[1:],  # Remove leading slash
            user=result.username,
            password=result.password
        )
        
        # Test if schema exists
        schema_name = os.getenv('AUTH_SCHEMA', 'metadata_builder')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
            (schema_name,)
        )
        schema_exists = cursor.fetchone() is not None
        
        # Test if tables exist
        if schema_exists:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name IN ('users', 'user_connections', 'system_connections')
            """, (schema_name,))
            tables = [row[0] for row in cursor.fetchall()]
        else:
            tables = []
        
        cursor.close()
        conn.close()
        
        return True, {
            'schema_exists': schema_exists,
            'tables_found': tables,
            'expected_tables': ['users', 'user_connections', 'system_connections', 
                              'user_sessions', 'connection_audit', 'metadata_jobs']
        }
        
    except ImportError:
        return False, "psycopg2 not installed (pip install psycopg2-binary)"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"

def generate_example_env():
    """Generate example .env configuration"""
    env_content = f"""
# Generated Authentication Configuration
AUTH_SCHEMA={os.getenv('AUTH_SCHEMA', 'metadata_builder')}
JWT_SECRET_KEY=your-jwt-secret-key-here
SESSION_ENCRYPTION_KEY=your-session-encryption-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=postgresql://username:password@localhost:5432/database
"""
    return env_content.strip()

def main():
    """Main validation function"""
    print("🔍 Validating Multi-User Authentication Setup")
    print("=" * 50)
    
    # Check environment variables
    print("1. Checking environment variables...")
    missing_vars = check_environment_variables()
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\n📝 Example .env configuration:")
        print(generate_example_env())
        return False
    else:
        print("✅ All required environment variables are set")
    
    # Show current configuration
    schema_name = os.getenv('AUTH_SCHEMA')
    print(f"   📁 Schema name: {schema_name}")
    print(f"   🔑 JWT secret: {'Set' if os.getenv('JWT_SECRET_KEY') else 'Not set'}")
    print(f"   🔐 Encryption key: {'Set' if os.getenv('SESSION_ENCRYPTION_KEY') else 'Not set'}")
    
    # Check database connection
    print("\n2. Testing database connection...")
    db_success, db_result = check_database_connection()
    
    if not db_success:
        print(f"❌ Database connection failed: {db_result}")
        return False
    
    print("✅ Database connection successful")
    
    # Check schema and tables
    print("\n3. Checking schema and tables...")
    if db_result['schema_exists']:
        print(f"✅ Schema '{schema_name}' exists")
        
        found_tables = db_result['tables_found']
        expected_tables = db_result['expected_tables']
        
        missing_tables = set(expected_tables) - set(found_tables)
        extra_tables = set(found_tables) - set(expected_tables)
        
        if not missing_tables:
            print("✅ All required tables found")
        else:
            print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            print("   Run: psql -f scripts/create_user_tables.sql")
        
        if found_tables:
            print(f"   📊 Tables found: {', '.join(found_tables)}")
    else:
        print(f"❌ Schema '{schema_name}' does not exist")
        print("   Run: psql -f scripts/create_user_tables.sql")
        return False
    
    # Final status
    print("\n" + "=" * 50)
    if db_result['schema_exists'] and len(db_result['tables_found']) >= 3:
        print("🎉 Setup validation PASSED!")
        print("   Ready to implement authentication backend!")
        return True
    else:
        print("❌ Setup validation FAILED")
        print("   Please run the schema creation script")
        return False

if __name__ == "__main__":
    # Load environment variables from .env if it exists
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print(f"📁 Loading environment from: {env_path}")
        from dotenv import load_dotenv
        load_dotenv(env_path)
    
    success = main()
    sys.exit(0 if success else 1) 