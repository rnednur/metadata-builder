-- Metadata Builder Multi-User Database Schema
-- Run this against your PostgreSQL database
--
-- CONFIGURATION: Set your desired schema name
-- Replace 'metadata_builder' with your preferred schema name
-- Or use \set to define it: \set SCHEMA_NAME 'your_schema_name'

-- Set the schema name (change this to your desired schema)
-- You can also pass this as a variable: psql -v SCHEMA_NAME=your_schema -f create_user_tables.sql
\set SCHEMA_NAME 'metadata_builder'

-- Create the schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS :SCHEMA_NAME;

-- Set the search path to use the specified schema
SET search_path TO :SCHEMA_NAME, public;

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and user management
CREATE TABLE :SCHEMA_NAME.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- System-level database connections (managed by admins, use env vars)
CREATE TABLE :SCHEMA_NAME.system_connections (
    connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_name VARCHAR(100) UNIQUE NOT NULL,
    db_type VARCHAR(20) NOT NULL CHECK (db_type IN ('postgresql', 'mysql', 'sqlite', 'oracle', 'bigquery', 'duckdb', 'kinetica')),
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    db_username VARCHAR(100) NOT NULL,
    password_env_var VARCHAR(100), -- Environment variable name for password
    allowed_schemas JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES :SCHEMA_NAME.users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User-specific database connections
CREATE TABLE :SCHEMA_NAME.user_connections (
    connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES :SCHEMA_NAME.users(user_id) ON DELETE CASCADE,
    connection_name VARCHAR(100) NOT NULL,
    db_type VARCHAR(20) NOT NULL CHECK (db_type IN ('postgresql', 'mysql', 'sqlite', 'oracle', 'bigquery', 'duckdb', 'kinetica')),
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    db_username VARCHAR(100) NOT NULL,
    
    -- Password strategy and storage
    password_strategy VARCHAR(20) NOT NULL DEFAULT 'session' CHECK (password_strategy IN ('session', 'prompt', 'encrypted')),
    password_encrypted TEXT, -- For future encrypted storage strategy
    
    -- Schema access control
    allowed_schemas JSONB DEFAULT '[]'::jsonb,
    
    -- Additional connection parameters (JSON for flexibility)
    connection_params JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    
    UNIQUE(user_id, connection_name)
);

-- User sessions for authentication and temporary credential storage
CREATE TABLE :SCHEMA_NAME.user_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES :SCHEMA_NAME.users(user_id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL, -- JWT token or session identifier
    
    -- Encrypted connection passwords for session strategy
    connection_passwords TEXT, -- Encrypted JSON: {"conn_id": "encrypted_password", ...}
    
    -- Session management
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_activity TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

-- Audit log for connection usage and security
CREATE TABLE :SCHEMA_NAME.connection_audit (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES :SCHEMA_NAME.users(user_id),
    connection_id UUID, -- Can reference either user_connections or system_connections
    connection_type VARCHAR(10) CHECK (connection_type IN ('user', 'system')),
    action VARCHAR(50) NOT NULL, -- 'connect', 'test', 'query', 'metadata_generate', etc.
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Metadata generation jobs (user-specific)
CREATE TABLE :SCHEMA_NAME.metadata_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES :SCHEMA_NAME.users(user_id) ON DELETE CASCADE,
    connection_id UUID REFERENCES :SCHEMA_NAME.user_connections(connection_id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'metadata', 'lookml', 'analysis'
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    
    -- Job configuration
    config JSONB NOT NULL, -- Job parameters (tables, schemas, options)
    
    -- Results
    result JSONB, -- Generated metadata/lookml
    error_message TEXT,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    
    -- Timing
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- File storage (if results are stored as files)
    result_file_path TEXT
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON :SCHEMA_NAME.users(username);
CREATE INDEX idx_users_email ON :SCHEMA_NAME.users(email);
CREATE INDEX idx_users_active ON :SCHEMA_NAME.users(is_active);

CREATE INDEX idx_user_connections_user_id ON :SCHEMA_NAME.user_connections(user_id);
CREATE INDEX idx_user_connections_active ON :SCHEMA_NAME.user_connections(is_active);
CREATE INDEX idx_user_connections_last_used ON :SCHEMA_NAME.user_connections(last_used);

CREATE INDEX idx_system_connections_active ON :SCHEMA_NAME.system_connections(is_active);

CREATE INDEX idx_user_sessions_user_id ON :SCHEMA_NAME.user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON :SCHEMA_NAME.user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON :SCHEMA_NAME.user_sessions(expires_at);

CREATE INDEX idx_connection_audit_user_id ON :SCHEMA_NAME.connection_audit(user_id);
CREATE INDEX idx_connection_audit_created_at ON :SCHEMA_NAME.connection_audit(created_at);

CREATE INDEX idx_metadata_jobs_user_id ON :SCHEMA_NAME.metadata_jobs(user_id);
CREATE INDEX idx_metadata_jobs_status ON :SCHEMA_NAME.metadata_jobs(status);
CREATE INDEX idx_metadata_jobs_created_at ON :SCHEMA_NAME.metadata_jobs(created_at);

-- Create updated_at trigger function (in the specified schema)
CREATE OR REPLACE FUNCTION :SCHEMA_NAME.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON :SCHEMA_NAME.users FOR EACH ROW EXECUTE FUNCTION :SCHEMA_NAME.update_updated_at_column();
CREATE TRIGGER update_system_connections_updated_at BEFORE UPDATE ON :SCHEMA_NAME.system_connections FOR EACH ROW EXECUTE FUNCTION :SCHEMA_NAME.update_updated_at_column();
CREATE TRIGGER update_user_connections_updated_at BEFORE UPDATE ON :SCHEMA_NAME.user_connections FOR EACH ROW EXECUTE FUNCTION :SCHEMA_NAME.update_updated_at_column();

-- Insert default admin user (password: 'admin123' - change this!)
INSERT INTO :SCHEMA_NAME.users (username, email, password_hash, first_name, last_name, role) 
VALUES (
    'admin', 
    'admin@metadata-builder.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdZvkj0wGJzQu', -- bcrypt hash of 'admin123'
    'System', 
    'Administrator', 
    'admin'
);

-- Create a sample system connection (using the existing postgres connection)
INSERT INTO :SCHEMA_NAME.system_connections (connection_name, db_type, host, port, database_name, db_username, password_env_var, allowed_schemas, description, created_by)
VALUES (
    'system_postgres',
    'postgresql',
    'localhost',
    5432,
    'postgres',
    'postgres',
    'POSTGRES_PASSWORD', -- This should be set in environment
    '["public", "information_schema"]',
    'System PostgreSQL database for metadata and user management',
    (SELECT user_id FROM :SCHEMA_NAME.users WHERE username = 'admin')
);

-- Show table creation summary
SELECT 
    'Database schema created successfully in schema: :SCHEMA_NAME' as message,
    COUNT(*) as total_tables
FROM information_schema.tables 
WHERE table_schema = :'SCHEMA_NAME'
AND table_name IN ('users', 'user_connections', 'system_connections', 'user_sessions', 'connection_audit', 'metadata_jobs');

-- Display final status
\echo 'Schema setup complete!'
\echo 'Tables created in schema: :SCHEMA_NAME'
\echo 'Default admin user: admin / admin123'
\echo 'Remember to change the default password!' 