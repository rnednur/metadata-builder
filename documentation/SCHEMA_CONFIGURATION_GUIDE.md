# Database Schema Configuration Guide

## 📋 **Overview**

The Metadata Builder multi-user authentication system supports **configurable database schemas**, allowing you to deploy user management tables in any PostgreSQL schema you choose.

## 🎯 **Why Configurable Schemas?**

### **Flexibility**
- Deploy in existing databases without conflicts
- Organize tables according to your naming conventions
- Support multi-tenant deployments

### **Security**  
- Isolate user management data in dedicated schemas
- Apply schema-level permissions and access controls
- Separate application data from user data

### **Integration**
- Work with existing database structures
- Support corporate database standards
- Enable easier backup and migration strategies

## ⚙️ **Configuration Methods**

### **Method 1: Environment Variable (Recommended)**

Set the `AUTH_SCHEMA` environment variable:

```bash
# In your .env file
AUTH_SCHEMA=metadata_builder
```

**Precedence:** Environment variable overrides all other settings

### **Method 2: SQL Script Variable**

When running the schema creation script:

```bash
# Option A: Command line variable
psql -v SCHEMA_NAME=your_schema -f scripts/create_user_tables.sql

# Option B: Edit the script directly
# Change line 8 in scripts/create_user_tables.sql:
\set SCHEMA_NAME 'your_custom_schema'
```

### **Method 3: Config File**

The schema name is also stored in the main configuration:

```yaml
# metadata_builder/config/config.yaml
database:
  auth_schema: metadata_builder
```

## 🏗️ **Schema Structure**

When you specify a schema name (e.g., `my_auth_schema`), the following will be created:

```sql
-- Schema and tables
CREATE SCHEMA IF NOT EXISTS my_auth_schema;

-- All tables with schema prefix
my_auth_schema.users
my_auth_schema.user_connections  
my_auth_schema.system_connections
my_auth_schema.user_sessions
my_auth_schema.connection_audit
my_auth_schema.metadata_jobs

-- Functions and triggers
my_auth_schema.update_updated_at_column()
```

## 🔍 **Schema Detection**

The system automatically detects your schema configuration:

```python
# Backend code reads from environment
AUTH_SCHEMA = os.getenv('AUTH_SCHEMA', 'metadata_builder')

# SQLAlchemy models use the configured schema
class User(Base):
    __table_args__ = ({'schema': AUTH_SCHEMA})
```

## 📊 **Examples**

### **Corporate Environment**
```bash
AUTH_SCHEMA=corp_user_management
```

### **Multi-Tenant SaaS**  
```bash
AUTH_SCHEMA=tenant_auth_prod
```

### **Development/Testing**
```bash
AUTH_SCHEMA=dev_auth
```

### **Legacy Integration**
```bash
AUTH_SCHEMA=legacy_users
```

## 🛠️ **Schema Management Commands**

### **Create Schema**
```sql
-- Manual schema creation
CREATE SCHEMA IF NOT EXISTS your_schema_name;
```

### **List Schemas**
```sql
-- See all schemas
SELECT schema_name FROM information_schema.schemata;
```

### **Check Tables in Schema**
```sql
-- List tables in your auth schema
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'your_schema_name';
```

### **Drop Schema (Careful!)**
```sql
-- Remove entire schema and all tables
DROP SCHEMA your_schema_name CASCADE;
```

## 🔐 **Security Considerations**

### **Schema Permissions**
```sql
-- Grant schema usage to application user
GRANT USAGE ON SCHEMA metadata_builder TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA metadata_builder TO app_user;

-- Restrict schema access
REVOKE ALL ON SCHEMA metadata_builder FROM public;
```

### **Search Path Configuration**
```sql
-- Set default schema for user
ALTER USER app_user SET search_path = metadata_builder, public;
```

## 🧪 **Validation**

Use the validation script to verify your schema setup:

```bash
# Validate current configuration
python scripts/validate_schema_setup.py
```

**Output includes:**
- ✅ Schema existence confirmation
- 📊 Table inventory  
- 🔍 Environment variable validation
- 🗄️ Database connection testing

## 🚨 **Migration Between Schemas**

### **Moving to a New Schema**

1. **Export data from old schema:**
```bash
pg_dump -n old_schema database_name > schema_backup.sql
```

2. **Update environment variables:**
```bash
AUTH_SCHEMA=new_schema_name
```

3. **Create new schema:**
```bash
psql -v SCHEMA_NAME=new_schema_name -f scripts/create_user_tables.sql
```

4. **Import data (modify schema references):**
```bash
# Edit schema_backup.sql to reference new schema
sed 's/old_schema/new_schema_name/g' schema_backup.sql > new_schema.sql
psql -f new_schema.sql
```

## ⚠️ **Important Notes**

### **Schema Name Requirements**
- Must be valid PostgreSQL identifier
- Cannot start with numbers
- No special characters (except underscores)
- Case-sensitive
- Maximum 63 characters

### **Compatibility**
- PostgreSQL 12+ recommended
- Works with all supported database types
- Environment variables take precedence
- Default fallback: `metadata_builder`

### **Best Practices**
- Use descriptive, consistent naming
- Document your schema choice
- Test with validation script
- Backup before migrations
- Set appropriate permissions

## 🎉 **Ready to Use**

Your configurable schema setup provides:

✅ **Flexible deployment** in any PostgreSQL schema  
✅ **Environment-based configuration** for different environments  
✅ **Automatic detection** by backend code  
✅ **Validation tools** to verify setup  
✅ **Migration support** for schema changes  

Choose your schema name and follow the setup instructions to get started! 