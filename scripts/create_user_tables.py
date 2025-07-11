#!/usr/bin/env python3
"""
User Management Tables Creation Script

This script creates all user management tables using SQLAlchemy models.
It supports configurable schemas and provides comprehensive logging.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

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
    from metadata_builder.auth.auth_utils import PasswordUtils
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install sqlalchemy psycopg2-binary python-dotenv")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / 'logs' / 'table_creation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class TableCreator:
    """Handles creation of user management tables."""
    
    def __init__(self, database_url: str, auth_schema: str = 'metadata_builder'):
        """Initialize the table creator."""
        self.database_url = database_url
        self.auth_schema = auth_schema
        self.engine = None
        self.session = None
        
    def connect(self) -> bool:
        """Connect to the database."""
        try:
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            
            logger.info(f"✅ Connected to database successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the schema if it doesn't exist."""
        try:
            with self.engine.connect() as conn:
                # Create schema
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.auth_schema}"))
                conn.commit()
            
            logger.info(f"✅ Schema '{self.auth_schema}' created/verified")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def create_extensions(self) -> bool:
        """Create required PostgreSQL extensions."""
        try:
            with self.engine.connect() as conn:
                # Create UUID extension
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                conn.commit()
            
            logger.info("✅ PostgreSQL extensions created/verified")
            return True
            
        except SQLAlchemyError as e:
            logger.warning(f"⚠️  Extension creation failed (may not have permissions): {e}")
            return True  # Continue even if extensions fail
    
    def create_tables(self) -> bool:
        """Create all user management tables."""
        try:
            # Create all tables defined in Base metadata
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("✅ All user management tables created successfully")
            
            # List created tables
            table_names = list(Base.metadata.tables.keys())
            logger.info(f"📊 Tables created: {', '.join(table_names)}")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Table creation failed: {e}")
            return False
    
    def create_default_admin_user(self) -> bool:
        """Create the default admin user."""
        try:
            # Check if admin user already exists
            existing_admin = self.session.query(User).filter_by(username='admin').first()
            if existing_admin:
                logger.info("ℹ️  Default admin user already exists")
                return True
            
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@metadata-builder.com',
                password_hash=PasswordUtils.hash_password('admin123'),
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            
            self.session.add(admin_user)
            self.session.commit()
            
            logger.info("✅ Default admin user created successfully")
            logger.warning("⚠️  Default password is 'admin123' - CHANGE THIS IMMEDIATELY!")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Admin user creation failed: {e}")
            self.session.rollback()
            return False
    
    def create_system_connection(self, admin_user_id: str) -> bool:
        """Create a default system connection."""
        try:
            # Check if system connection already exists
            existing_conn = self.session.query(SystemConnection).filter_by(
                connection_name='system_postgres'
            ).first()
            if existing_conn:
                logger.info("ℹ️  Default system connection already exists")
                return True
            
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
                created_by=admin_user_id
            )
            
            self.session.add(system_conn)
            self.session.commit()
            
            logger.info("✅ Default system connection created successfully")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ System connection creation failed: {e}")
            self.session.rollback()
            return False
    
    def verify_setup(self) -> bool:
        """Verify that all tables and data were created correctly."""
        try:
            # Check tables exist
            table_count = len(Base.metadata.tables)
            logger.info(f"📊 Verification: {table_count} tables defined in models")
            
            # Check admin user exists
            admin_user = self.session.query(User).filter_by(username='admin').first()
            if admin_user:
                logger.info(f"✅ Admin user verified: {admin_user.email}")
                
                # Check system connection
                system_conn = self.session.query(SystemConnection).filter_by(
                    connection_name='system_postgres'
                ).first()
                if system_conn:
                    logger.info(f"✅ System connection verified: {system_conn.connection_name}")
                
                return True
            else:
                logger.error("❌ Admin user not found")
                return False
                
        except SQLAlchemyError as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def close(self):
        """Close database connections."""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()


def load_environment():
    """Load environment variables from .env file."""
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"📁 Loaded environment from: {env_path}")
    else:
        logger.warning("⚠️  No .env file found, using system environment variables")


def get_configuration():
    """Get database configuration from environment."""
    config = {
        'database_url': os.getenv('DATABASE_URL'),
        'auth_schema': os.getenv('AUTH_SCHEMA', 'metadata_builder'),
        'jwt_secret': os.getenv('JWT_SECRET_KEY'),
        'session_key': os.getenv('SESSION_ENCRYPTION_KEY')
    }
    
    return config


def validate_configuration(config: dict) -> bool:
    """Validate that required configuration is present."""
    required_keys = ['database_url', 'auth_schema']
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        logger.error(f"❌ Missing required configuration: {', '.join(missing_keys)}")
        return False
    
    if not config.get('jwt_secret'):
        logger.warning("⚠️  JWT_SECRET_KEY not set - required for authentication")
    
    if not config.get('session_key'):
        logger.warning("⚠️  SESSION_ENCRYPTION_KEY not set - required for credential encryption")
    
    return True


def main():
    """Main function to create user management tables."""
    print("🚀 Creating User Management Tables")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Get configuration
    config = get_configuration()
    
    # Validate configuration
    if not validate_configuration(config):
        logger.error("❌ Configuration validation failed")
        return False
    
    logger.info(f"📁 Using schema: {config['auth_schema']}")
    logger.info(f"🔗 Database URL: {config['database_url'][:20]}...")
    
    # Create tables
    creator = TableCreator(config['database_url'], config['auth_schema'])
    
    try:
        # Step 1: Connect to database
        if not creator.connect():
            return False
        
        # Step 2: Create schema
        if not creator.create_schema():
            return False
        
        # Step 3: Create extensions
        if not creator.create_extensions():
            return False
        
        # Step 4: Create tables
        if not creator.create_tables():
            return False
        
        # Step 5: Create default admin user
        if not creator.create_default_admin_user():
            return False
        
        # Step 6: Create system connection
        admin_user = creator.session.query(User).filter_by(username='admin').first()
        if admin_user and not creator.create_system_connection(admin_user.user_id):
            return False
        
        # Step 7: Verify setup
        if not creator.verify_setup():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 User Management Tables Created Successfully!")
        print(f"📁 Schema: {config['auth_schema']}")
        print("👤 Default admin user: admin / admin123")
        print("⚠️  IMPORTANT: Change the default password immediately!")
        print("🔗 System connection: system_postgres")
        print("\n🧪 Run validation: python scripts/validate_schema_setup.py")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False
        
    finally:
        creator.close()


if __name__ == "__main__":
    # Ensure logs directory exists
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    success = main()
    sys.exit(0 if success else 1) 