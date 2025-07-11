"""
SQLAlchemy models for user authentication and connection management.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Text, JSON,
    ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Get schema name from environment or config
AUTH_SCHEMA = os.getenv('AUTH_SCHEMA', 'metadata_builder')

# Create base class with configurable schema
Base = declarative_base()

# Helper function to create schema-qualified table references
def get_table_ref(table_name: str) -> str:
    """Get schema-qualified table reference."""
    return f"{AUTH_SCHEMA}.{table_name}"


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default='user', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime)
    
    # Relationships
    user_connections = relationship("UserConnection", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_system_connections = relationship("SystemConnection", back_populates="creator")
    metadata_jobs = relationship("MetadataJob", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("ConnectionAudit", back_populates="user")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'user']), name='check_user_role'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, role={self.role})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password)."""
        return {
            'user_id': str(self.user_id),
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class SystemConnection(Base):
    """System-level database connections managed by admins."""
    
    __tablename__ = "system_connections"
    
    connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_name = Column(String(100), unique=True, nullable=False)
    db_type = Column(String(20), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    db_username = Column(String(100), nullable=False)
    password_env_var = Column(String(100))  # Environment variable name for password
    allowed_schemas = Column(JSON, default=list)
    
    # Advanced schema and table filtering
    predefined_schemas = Column(JSON, default=dict)  # {"schema_name": {"tables": ["table1", "table2"], "enabled": true}}
    
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.users.user_id'))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="created_system_connections")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(db_type.in_(['postgresql', 'mysql', 'sqlite', 'oracle', 'bigquery', 'duckdb', 'kinetica']), 
                       name='check_system_connection_db_type'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<SystemConnection(name={self.connection_name}, type={self.db_type}, host={self.host})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system connection to dictionary."""
        return {
            'connection_id': str(self.connection_id),
            'connection_name': self.connection_name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'db_username': self.db_username,
            'allowed_schemas': self.allowed_schemas,
            'predefined_schemas': self.predefined_schemas,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserConnection(Base):
    """User-specific database connections."""
    
    __tablename__ = "user_connections"
    
    connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.users.user_id', ondelete='CASCADE'), nullable=False)
    connection_name = Column(String(100), nullable=False)
    db_type = Column(String(20), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database_name = Column(String(100), nullable=False)
    db_username = Column(String(100), nullable=False)
    
    # Password strategy and storage
    password_strategy = Column(String(20), default='session', nullable=False)
    password_encrypted = Column(Text)  # For future encrypted storage strategy
    
    # Schema access control
    allowed_schemas = Column(JSON, default=list)
    
    # Advanced schema and table filtering
    predefined_schemas = Column(JSON, default=dict)  # {"schema_name": {"tables": ["table1", "table2"], "enabled": true}}
    
    # Additional connection parameters (JSON for flexibility)
    connection_params = Column(JSON, default=dict)
    
    # Metadata
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_used = Column(DateTime, index=True)
    
    # Relationships
    user = relationship("User", back_populates="user_connections")
    metadata_jobs = relationship("MetadataJob", back_populates="connection", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'connection_name', name='uq_user_connection_name'),
        CheckConstraint(db_type.in_(['postgresql', 'mysql', 'sqlite', 'oracle', 'bigquery', 'duckdb', 'kinetica']), 
                       name='check_user_connection_db_type'),
        CheckConstraint(password_strategy.in_(['session', 'prompt', 'encrypted']), 
                       name='check_password_strategy'),
        Index('idx_user_connections_user_id', 'user_id'),
        Index('idx_user_connections_last_used', 'last_used'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<UserConnection(user_id={self.user_id}, name={self.connection_name}, type={self.db_type})>"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user connection to dictionary."""
        data = {
            'connection_id': str(self.connection_id),
            'connection_name': self.connection_name,
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database_name': self.database_name,
            'db_username': self.db_username,
            'password_strategy': self.password_strategy,
            'allowed_schemas': self.allowed_schemas,
            'predefined_schemas': self.predefined_schemas,
            'connection_params': self.connection_params,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
        
        if include_sensitive:
            data['password_encrypted'] = self.password_encrypted
        
        return data


class UserSession(Base):
    """User sessions for authentication and temporary credential storage."""
    
    __tablename__ = "user_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.users.user_id', ondelete='CASCADE'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Encrypted connection passwords for session strategy
    connection_passwords = Column(Text)  # Encrypted JSON: {"conn_id": "encrypted_password", ...}
    
    # Session management
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_activity = Column(DateTime, default=func.now(), nullable=False)
    user_agent = Column(Text)
    ip_address = Column(INET)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_expires', 'expires_at'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<UserSession(user_id={self.user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': str(self.session_id),
            'user_id': str(self.user_id),
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'user_agent': self.user_agent,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'is_expired': self.is_expired
        }


class ConnectionAudit(Base):
    """Audit log for connection usage and security."""
    
    __tablename__ = "connection_audit"
    
    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.users.user_id'))
    connection_id = Column(UUID(as_uuid=True))  # Can reference either user_connections or system_connections
    connection_type = Column(String(10))  # 'user' or 'system'
    action = Column(String(50), nullable=False)  # 'connect', 'test', 'query', 'metadata_generate', etc.
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(connection_type.in_(['user', 'system']), name='check_connection_type'),
        Index('idx_connection_audit_user_id', 'user_id'),
        Index('idx_connection_audit_created_at', 'created_at'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<ConnectionAudit(user_id={self.user_id}, action={self.action}, success={self.success})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            'audit_id': str(self.audit_id),
            'user_id': str(self.user_id) if self.user_id else None,
            'connection_id': str(self.connection_id) if self.connection_id else None,
            'connection_type': self.connection_type,
            'action': self.action,
            'success': self.success,
            'error_message': self.error_message,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MetadataJob(Base):
    """Metadata generation jobs (user-specific)."""
    
    __tablename__ = "metadata_jobs"
    
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.users.user_id', ondelete='CASCADE'), nullable=False)
    connection_id = Column(UUID(as_uuid=True), ForeignKey(f'{AUTH_SCHEMA}.user_connections.connection_id', ondelete='CASCADE'), nullable=False)
    job_type = Column(String(50), nullable=False)  # 'metadata', 'lookml', 'analysis'
    status = Column(String(20), default='pending', nullable=False)
    
    # Job configuration
    config = Column(JSON, nullable=False)  # Job parameters (tables, schemas, options)
    
    # Results
    result = Column(JSON)  # Generated metadata/lookml
    error_message = Column(Text)
    progress = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # File storage (if results are stored as files)
    result_file_path = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="metadata_jobs")
    connection = relationship("UserConnection", back_populates="metadata_jobs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(status.in_(['pending', 'running', 'completed', 'failed']), name='check_job_status'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_job_progress'),
        Index('idx_metadata_jobs_user_id', 'user_id'),
        Index('idx_metadata_jobs_status', 'status'),
        Index('idx_metadata_jobs_created_at', 'created_at'),
        {'schema': AUTH_SCHEMA}
    )
    
    def __repr__(self):
        return f"<MetadataJob(job_id={self.job_id}, type={self.job_type}, status={self.status})>"
    
    @property
    def duration(self) -> Optional[int]:
        """Get job duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata job to dictionary."""
        return {
            'job_id': str(self.job_id),
            'user_id': str(self.user_id),
            'connection_id': str(self.connection_id),
            'job_type': self.job_type,
            'status': self.status,
            'config': self.config,
            'result': self.result,
            'error_message': self.error_message,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': self.duration,
            'result_file_path': self.result_file_path
        } 