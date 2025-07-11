# Authentication Setup Scripts

This directory contains Python scripts for setting up the multi-user authentication system.

## 🚀 Quick Setup

### **Option 1: Simple Interactive Setup**

```bash
# Interactive setup with prompts
python scripts/setup_auth.py
```

This script will:
- ✅ Check for `.env` file
- ✅ Ask for schema name
- ✅ Create all tables and default data
- ✅ Provide confirmation and next steps

### **Option 2: Direct Table Creation**

```bash
# Direct table creation using environment variables
python scripts/create_user_tables.py
```

## 📋 Prerequisites

### **1. Install Dependencies**

```bash
pip install -r requirements.txt
```

**Required packages:**
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variable loading
- `passlib[bcrypt]` - Password hashing
- `python-jose[cryptography]` - JWT tokens

### **2. Environment Configuration**

Create and configure your `.env` file:

```bash
# Copy the example
cp env.example .env

# Edit with your settings
# Minimum required:
DATABASE_URL=postgresql://username:password@localhost:5432/database
AUTH_SCHEMA=metadata_builder
JWT_SECRET_KEY=your-secret-key
SESSION_ENCRYPTION_KEY=your-encryption-key
```

### **3. Database Requirements**

- **PostgreSQL 12+** (recommended)
- **Database user** with CREATE privileges
- **Existing database** (tables will be created in specified schema)

## 📊 What Gets Created

### **Tables Created:**
1. **users** - User accounts and authentication
2. **user_connections** - User-specific database connections
3. **system_connections** - Admin-managed shared connections
4. **user_sessions** - Authentication sessions and encrypted credentials
5. **connection_audit** - Security and usage audit log
6. **metadata_jobs** - User-specific metadata generation jobs

### **Default Data:**
- **Admin User:** `admin` / `admin123` ⚠️ *Change immediately!*
- **System Connection:** `system_postgres` (localhost PostgreSQL)

### **Schema Structure:**
```
{your_schema}.users
{your_schema}.user_connections
{your_schema}.system_connections
{your_schema}.user_sessions
{your_schema}.connection_audit
{your_schema}.metadata_jobs
```

## 🔧 Script Details

### **`setup_auth.py`** (Recommended)
- 🎯 **Interactive setup** with user prompts
- 🔍 **Environment validation** before proceeding
- 🛡️ **Confirmation prompts** to prevent accidents
- 📝 **Clear success/failure messaging**

**Usage:**
```bash
python scripts/setup_auth.py
```

### **`create_user_tables.py`** (Advanced)
- 🏗️ **Full table creation** using SQLAlchemy models
- 📝 **Comprehensive logging** to console and file
- 🔄 **Idempotent operations** (safe to run multiple times)
- ✅ **Built-in verification** of created tables

**Usage:**
```bash
# Using environment variables
python scripts/create_user_tables.py

# With custom schema (overrides environment)
AUTH_SCHEMA=custom_schema python scripts/create_user_tables.py
```

### **`validate_schema_setup.py`** (Validation)
- 🧪 **Verify setup** after table creation
- 🔍 **Environment variable** validation
- 🗄️ **Database connection** testing
- 📊 **Table existence** verification

**Usage:**
```bash
python scripts/validate_schema_setup.py
```

## 🎯 Common Workflows

### **First Time Setup:**
```bash
# 1. Configure environment
cp env.example .env
# Edit .env with your database settings

# 2. Run interactive setup
python scripts/setup_auth.py

# 3. Validate setup
python scripts/validate_schema_setup.py
```

### **Development/Testing:**
```bash
# Use different schema for testing
AUTH_SCHEMA=test_auth python scripts/create_user_tables.py
```

### **Production Deployment:**
```bash
# Set production schema
export AUTH_SCHEMA=prod_auth
export DATABASE_URL=postgresql://...

# Create tables
python scripts/create_user_tables.py

# Validate
python scripts/validate_schema_setup.py
```

## 🚨 Troubleshooting

### **Common Issues:**

**"Import error" / "Module not found":**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

**"Database connection failed":**
- Check `DATABASE_URL` in `.env`
- Ensure PostgreSQL is running
- Verify credentials and database exists

**"Schema creation failed":**
- Check database user has CREATE privileges
- Verify schema name is valid (no special characters)

**"Extension creation failed":**
- Usually safe to ignore (UUID extension)
- Check if user has SUPERUSER privileges

### **Logs:**
Check `logs/table_creation.log` for detailed error information.

### **Clean Start:**
```bash
# Drop schema and recreate (⚠️ DESTRUCTIVE!)
psql -c "DROP SCHEMA IF EXISTS your_schema CASCADE;"
python scripts/create_user_tables.py
```

## ✅ Success Indicators

**You should see:**
```
🎉 User Management Tables Created Successfully!
📁 Schema: metadata_builder
👤 Default admin user: admin / admin123
⚠️  IMPORTANT: Change the default password immediately!
🔗 System connection: system_postgres
```

**Validation should show:**
```
🎉 Setup validation PASSED!
   Ready to implement authentication backend!
```

## 🔐 Security Notes

1. **Change default password** immediately after setup
2. **Set strong JWT_SECRET_KEY** and **SESSION_ENCRYPTION_KEY**
3. **Use environment variables** for sensitive configuration
4. **Restrict database permissions** for production users
5. **Enable audit logging** for compliance requirements

## 🔄 Next Steps

After successful table creation:

1. **Implement backend authentication APIs**
2. **Add JWT middleware** for route protection
3. **Update existing endpoints** to be user-specific
4. **Create frontend authentication** pages

Your foundation is ready for building the complete multi-user system! 🚀 