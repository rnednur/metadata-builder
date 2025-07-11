#!/usr/bin/env python3
"""
Migration script to add predefined_schemas column to connection tables.
This script adds the new predefined_schemas JSON column to both 
user_connections and system_connections tables.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metadata_builder.auth.database import get_database_url

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add predefined_schemas column."""
    
    print("=" * 60)
    print("PREDEFINED SCHEMAS COLUMN MIGRATION")
    print("=" * 60)
    
    try:
        # Get database URL
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Get schema name from environment
        auth_schema = os.getenv('AUTH_SCHEMA', 'metadata_builder')
        
        print(f"Using schema: {auth_schema}")
        print(f"Database URL: {database_url.replace(database_url.split('@')[0].split('://')[-1], '***')}")
        
        with engine.connect() as connection:
            # Check if columns already exist
            check_user_conn_sql = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{auth_schema}' 
                AND table_name = 'user_connections' 
                AND column_name = 'predefined_schemas'
            """
            
            check_system_conn_sql = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '{auth_schema}' 
                AND table_name = 'system_connections' 
                AND column_name = 'predefined_schemas'
            """
            
            user_conn_exists = connection.execute(text(check_user_conn_sql)).fetchone()
            system_conn_exists = connection.execute(text(check_system_conn_sql)).fetchone()
            
            # Add column to user_connections if it doesn't exist
            if not user_conn_exists:
                print("\\n📝 Adding predefined_schemas column to user_connections table...")
                alter_user_conn_sql = f"""
                    ALTER TABLE {auth_schema}.user_connections 
                    ADD COLUMN predefined_schemas JSON DEFAULT '{{}}'::json
                """
                connection.execute(text(alter_user_conn_sql))
                print("✅ Added predefined_schemas column to user_connections")
            else:
                print("ℹ️  predefined_schemas column already exists in user_connections")
            
            # Add column to system_connections if it doesn't exist
            if not system_conn_exists:
                print("\\n📝 Adding predefined_schemas column to system_connections table...")
                alter_system_conn_sql = f"""
                    ALTER TABLE {auth_schema}.system_connections 
                    ADD COLUMN predefined_schemas JSON DEFAULT '{{}}'::json
                """
                connection.execute(text(alter_system_conn_sql))
                print("✅ Added predefined_schemas column to system_connections")
            else:
                print("ℹ️  predefined_schemas column already exists in system_connections")
            
            # Commit the changes
            connection.commit()
            
            print("\\n✅ Migration completed successfully!")
            
            # Show example of how to use the new column
            print("\\n📚 USAGE EXAMPLE:")
            print("The predefined_schemas column stores JSON configuration like this:")
            
            example_config = {
                "public": {
                    "enabled": True,
                    "tables": ["users", "orders"],
                    "excluded_tables": ["temp_data"],
                    "table_patterns": ["user_.*", "order_.*"],
                    "excluded_patterns": [".*_temp", ".*_backup"],
                    "description": "Core application tables"
                },
                "analytics": {
                    "enabled": True,
                    "tables": [],
                    "excluded_tables": [],
                    "table_patterns": [],
                    "excluded_patterns": [".*_raw"],
                    "description": "Analytics tables"
                }
            }
            
            import json
            print(json.dumps(example_config, indent=2))
            
            print("\\n🔧 API ENDPOINTS:")
            print("Use these endpoints to manage predefined schemas:")
            print("  • GET /database/connections/{name}/predefined-schemas")
            print("  • PUT /database/connections/{name}/predefined-schemas")
            print("  • POST /database/connections/{name}/predefined-schemas/{schema}")
            print("  • DELETE /database/connections/{name}/predefined-schemas/{schema}")
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

def rollback_migration():
    """Rollback the migration by removing predefined_schemas columns."""
    
    print("=" * 60)
    print("ROLLBACK PREDEFINED SCHEMAS COLUMN MIGRATION")
    print("=" * 60)
    
    try:
        # Get database URL
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # Get schema name from environment
        auth_schema = os.getenv('AUTH_SCHEMA', 'metadata_builder')
        
        print(f"Using schema: {auth_schema}")
        
        with engine.connect() as connection:
            # Remove column from user_connections
            print("\\n📝 Removing predefined_schemas column from user_connections table...")
            try:
                alter_user_conn_sql = f"""
                    ALTER TABLE {auth_schema}.user_connections 
                    DROP COLUMN IF EXISTS predefined_schemas
                """
                connection.execute(text(alter_user_conn_sql))
                print("✅ Removed predefined_schemas column from user_connections")
            except Exception as e:
                print(f"⚠️  Could not remove from user_connections: {e}")
            
            # Remove column from system_connections
            print("\\n📝 Removing predefined_schemas column from system_connections table...")
            try:
                alter_system_conn_sql = f"""
                    ALTER TABLE {auth_schema}.system_connections 
                    DROP COLUMN IF EXISTS predefined_schemas
                """
                connection.execute(text(alter_system_conn_sql))
                print("✅ Removed predefined_schemas column from system_connections")
            except Exception as e:
                print(f"⚠️  Could not remove from system_connections: {e}")
            
            # Commit the changes
            connection.commit()
            
            print("\\n✅ Rollback completed successfully!")
            
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Predefined schemas column migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()