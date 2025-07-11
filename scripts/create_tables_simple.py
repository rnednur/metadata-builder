#!/usr/bin/env python3
"""
Simple User Management Tables Creation Script

This script creates all user management tables WITHOUT JWT dependencies.
Use this if you're having JWT import issues.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    from dotenv import load_dotenv
    
    # Import our authentication models
    from metadata_builder.auth.models import Base, User, SystemConnection
    
    # Simple password hashing without full auth_utils
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure core dependencies are installed:")
    print("pip install sqlalchemy psycopg2-binary python-dotenv passlib[bcrypt]")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file."""
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"📁 Loaded environment from: {env_path}")
    else:
        logger.warning("⚠️  No .env file found, using system environment variables")


def main():
    """Main function to create user management tables."""
    print("🚀 Creating User Management Tables (Simple Version)")
    print("=" * 55)
    
    # Load environment
    load_environment()
    
    # Get configuration
    database_url = os.getenv('DATABASE_URL')
    auth_schema = os.getenv('AUTH_SCHEMA', 'metadata_builder')
    
    if not database_url:
        print("❌ DATABASE_URL not set in environment")
        print("   Set it in your .env file or environment variables")
        return False
    
    logger.info(f"📁 Using schema: {auth_schema}")
    logger.info(f"🔗 Database URL: {database_url[:20]}...")
    
    try:
        # Connect to database
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Connected to database successfully")
        
        # Create schema
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {auth_schema}"))
            conn.commit()
        logger.info(f"✅ Schema '{auth_schema}' created/verified")
        
        # Create extensions (optional)
        try:
            with engine.connect() as conn:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                conn.commit()
            logger.info("✅ PostgreSQL extensions created/verified")
        except:
            logger.warning("⚠️  Extension creation failed (continuing anyway)")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All user management tables created successfully")
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create default admin user
        existing_admin = session.query(User).filter_by(username='admin').first()
        if not existing_admin:
            admin_user = User(
                username='admin',
                email='admin@metadata-builder.com',
                password_hash=pwd_context.hash('admin123'),
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            session.add(admin_user)
            session.commit()
            logger.info("✅ Default admin user created successfully")
            logger.warning("⚠️  Default password is 'admin123' - CHANGE THIS IMMEDIATELY!")
            
            # Create system connection
            system_conn = SystemConnection(
                connection_name='system_postgres',
                db_type='postgresql',
                host='localhost',
                port=5432,
                database_name='postgres',
                db_username='postgres',
                password_env_var='POSTGRES_PASSWORD',
                allowed_schemas=['public', 'information_schema'],
                description='System PostgreSQL database for metadata and user management',
                created_by=admin_user.user_id
            )
            session.add(system_conn)
            session.commit()
            logger.info("✅ Default system connection created successfully")
        else:
            logger.info("ℹ️  Default admin user already exists")
        
        session.close()
        engine.dispose()
        
        print("\n" + "=" * 55)
        print("🎉 User Management Tables Created Successfully!")
        print(f"📁 Schema: {auth_schema}")
        print("👤 Default admin user: admin / admin123")
        print("⚠️  IMPORTANT: Change the default password immediately!")
        print("🔗 System connection: system_postgres")
        print("\n🔧 Next: Fix JWT dependencies if needed:")
        print("   python scripts/fix_auth_dependencies.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 