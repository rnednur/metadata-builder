"""
FastAPI dependencies for the Metadata Builder API.
"""

import yaml
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ..config.config import load_config
from ..auth.auth_utils import verify_token, get_database_session
from ..auth.models import User, SystemConnection, UserConnection

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer()


@dataclass
class Job:
    """Represents a background job."""
    job_id: str
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    try:
        # Verify token and get user_id
        user_id = verify_token(credentials.credentials)
        
        # Get user from database
        user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Update last activity
        user.last_login = datetime.now()
        db.commit()
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Used for endpoints that work both authenticated and unauthenticated.
    """
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


class ConnectionManager:
    """Manages database connections from both system and user sources."""
    
    # Class-level cache to avoid repeated loading
    _system_cache: Dict[str, Dict[str, Any]] = {}
    _config_cache: Dict[str, Dict[str, Any]] = {}
    _cache_loaded = False
    
    # Session-based credential cache
    _credential_cache: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, db: Session, current_user: Optional[User] = None):
        self.db = db
        self.current_user = current_user
        self._system_connections: Dict[str, Dict[str, Any]] = {}
        self._user_connections: Dict[str, Dict[str, Any]] = {}
        self._config_connections: Dict[str, Dict[str, Any]] = {}
        self._load_all_connections()
    
    def _load_all_connections(self):
        """Load connections from all sources: database tables + config fallback."""
        self._load_system_connections()
        self._load_user_connections()
        self._load_config_connections()
        # Mark cache as loaded after first successful load
        ConnectionManager._cache_loaded = True
    
    @classmethod
    def clear_cache(cls):
        """Clear the connection cache. Call this when connections are updated."""
        cls._system_cache.clear()
        cls._config_cache.clear()
        cls._cache_loaded = False
        logger.info("Connection cache cleared")
    
    def _load_system_connections(self):
        """Load system-level connections from database (with caching)."""
        # Use cached system connections if available
        if ConnectionManager._cache_loaded:
            self._system_connections = ConnectionManager._system_cache.copy()
            return
            
        try:
            system_conns = self.db.query(SystemConnection).filter(
                SystemConnection.is_active == True
            ).all()
            
            for conn in system_conns:
                config = {
                    "type": conn.db_type,
                    "host": conn.host,
                    "port": conn.port,
                    "database": conn.database_name,
                    "username": conn.db_username,
                    "password_env_var": conn.password_env_var,
                    "allowed_schemas": conn.allowed_schemas or [],
                    "description": conn.description,
                    "connection_source": "system"
                }
                self._system_connections[conn.connection_name] = config
            
            # Cache the results
            ConnectionManager._system_cache = self._system_connections.copy()
            logger.info(f"Loaded {len(self._system_connections)} system connections")
            
        except Exception as e:
            logger.warning(f"Failed to load system connections: {str(e)}")
    
    def _load_user_connections(self):
        """Load user-specific connections from database."""
        if not self.current_user:
            return
            
        try:
            user_conns = self.db.query(UserConnection).filter(
                UserConnection.user_id == self.current_user.user_id,
                UserConnection.is_active == True
            ).all()
            
            for conn in user_conns:
                config = {
                    "type": conn.db_type,
                    "host": conn.host,
                    "port": conn.port,
                    "database": conn.database_name,
                    "username": conn.db_username,
                    "password_strategy": conn.password_strategy,
                    "allowed_schemas": conn.allowed_schemas or [],
                    "connection_params": conn.connection_params or {},
                    "description": conn.description,
                    "connection_source": "user",
                    "connection_id": str(conn.connection_id)
                }
                self._user_connections[conn.connection_name] = config
            
            logger.info(f"Loaded {len(self._user_connections)} user connections for user {self.current_user.username}")
            
        except Exception as e:
            logger.warning(f"Failed to load user connections: {str(e)}")
    
    def _load_config_connections(self):
        """Load connections from configuration as fallback (with caching)."""
        # Use cached config connections if available
        if ConnectionManager._cache_loaded:
            # Still need to filter out connections that exist in system/user
            for name, config_data in ConnectionManager._config_cache.items():
                if name not in self._system_connections and name not in self._user_connections:
                    self._config_connections[name] = config_data
            return
            
        try:
            config = load_config()
            databases = config.get('databases', {})
            
            # Cache all config connections
            for name, config_data in databases.items():
                config_data = config_data.copy()
                config_data["connection_source"] = "config"
                ConnectionManager._config_cache[name] = config_data
            
            # Load only those not in system/user connections
            for name, config_data in ConnectionManager._config_cache.items():
                if name not in self._system_connections and name not in self._user_connections:
                    self._config_connections[name] = config_data
                    
            logger.info(f"Loaded {len(self._config_connections)} config connections as fallback")
            
        except Exception as e:
            logger.warning(f"Failed to load config connections: {str(e)}")
    
    def connection_exists(self, name: str) -> bool:
        """Check if a connection exists in any source."""
        return (name in self._system_connections or 
                name in self._user_connections or 
                name in self._config_connections)
    
    def get_connection(self, name: str) -> Dict[str, Any]:
        """Get connection configuration by name (priority: user > system > config)."""
        # Priority: user connections first, then system, then config
        if name in self._user_connections:
            return self._user_connections[name].copy()
        elif name in self._system_connections:
            return self._system_connections[name].copy()
        elif name in self._config_connections:
            return self._config_connections[name].copy()
        else:
            raise ValueError(f"Connection '{name}' not found")
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get all accessible connections (user + system + config)."""
        all_connections = {}
        
        # Add in priority order (user overrides system overrides config)
        all_connections.update(self._config_connections)
        all_connections.update(self._system_connections)
        all_connections.update(self._user_connections)
        
        return all_connections
    
    def get_user_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get only user-specific connections."""
        return self._user_connections.copy()
    
    def get_system_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get only system connections."""
        return self._system_connections.copy()
    
    def add_user_connection(self, name: str, config: Dict[str, Any]) -> str:
        """Add a new user connection to the database."""
        if not self.current_user:
            raise ValueError("User authentication required to add connections")
        
        try:
            # Create new user connection
            user_conn = UserConnection(
                user_id=self.current_user.user_id,
                connection_name=name,
                db_type=config.get("type"),
                host=config.get("host"),
                port=config.get("port"),
                database_name=config.get("database"),
                db_username=config.get("username"),
                password_strategy=config.get("password_strategy", "session"),
                allowed_schemas=config.get("allowed_schemas", []),
                connection_params=config.get("connection_params", {}),
                description=config.get("description")
            )
            
            self.db.add(user_conn)
            self.db.commit()
            self.db.refresh(user_conn)
            
            # Add to local cache
            config_with_meta = config.copy()
            config_with_meta["connection_source"] = "user"
            config_with_meta["connection_id"] = str(user_conn.connection_id)
            self._user_connections[name] = config_with_meta
            
            logger.info(f"Added user connection '{name}' for user {self.current_user.username}")
            return str(user_conn.connection_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add user connection '{name}': {str(e)}")
            raise
    
    def remove_connection(self, name: str):
        """Remove a user connection (only user connections can be removed)."""
        if not self.current_user:
            raise ValueError("User authentication required to remove connections")
        
        if name not in self._user_connections:
            raise ValueError(f"User connection '{name}' not found or not removable")
        
        try:
            # Remove from database
            user_conn = self.db.query(UserConnection).filter(
                UserConnection.user_id == self.current_user.user_id,
                UserConnection.connection_name == name
            ).first()
            
            if user_conn:
                self.db.delete(user_conn)
                self.db.commit()
            
            # Remove from cache
            del self._user_connections[name]
            
            logger.info(f"Removed user connection '{name}' for user {self.current_user.username}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to remove user connection '{name}': {str(e)}")
            raise
    
    def update_user_connection(self, name: str, config: Dict[str, Any]):
        """Update an existing user connection."""
        if not self.current_user:
            raise ValueError("User authentication required to update connections")
        
        if name not in self._user_connections:
            raise ValueError(f"User connection '{name}' not found")
        
        try:
            # Update in database
            user_conn = self.db.query(UserConnection).filter(
                UserConnection.user_id == self.current_user.user_id,
                UserConnection.connection_name == name
            ).first()
            
            if user_conn:
                user_conn.db_type = config.get("type", user_conn.db_type)
                user_conn.host = config.get("host", user_conn.host)
                user_conn.port = config.get("port", user_conn.port)
                user_conn.database_name = config.get("database", user_conn.database_name)
                user_conn.db_username = config.get("username", user_conn.db_username)
                user_conn.password_strategy = config.get("password_strategy", user_conn.password_strategy)
                user_conn.allowed_schemas = config.get("allowed_schemas", user_conn.allowed_schemas)
                user_conn.connection_params = config.get("connection_params", user_conn.connection_params)
                user_conn.description = config.get("description", user_conn.description)
                user_conn.updated_at = datetime.now()
                
                self.db.commit()
            
            # Update cache
            config_with_meta = config.copy()
            config_with_meta["connection_source"] = "user"
            config_with_meta["connection_id"] = self._user_connections[name]["connection_id"]
            self._user_connections[name] = config_with_meta
            
            logger.info(f"Updated user connection '{name}' for user {self.current_user.username}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user connection '{name}': {str(e)}")
            raise
    
    def cache_credentials(self, connection_name: str, credentials: Dict[str, Any]):
        """Cache sensitive credentials temporarily for a connection."""
        cache_key = f"{self.current_user.user_id if self.current_user else 'anonymous'}:{connection_name}"
        ConnectionManager._credential_cache[cache_key] = credentials
        logger.info(f"Cached credentials for connection '{connection_name}'")
    
    def get_cached_credentials(self, connection_name: str) -> Optional[Dict[str, Any]]:
        """Get cached credentials for a connection."""
        cache_key = f"{self.current_user.user_id if self.current_user else 'anonymous'}:{connection_name}"
        return ConnectionManager._credential_cache.get(cache_key)
    
    def clear_cached_credentials(self, connection_name: str):
        """Clear cached credentials for a connection."""
        cache_key = f"{self.current_user.user_id if self.current_user else 'anonymous'}:{connection_name}"
        if cache_key in ConnectionManager._credential_cache:
            del ConnectionManager._credential_cache[cache_key]
            logger.info(f"Cleared cached credentials for connection '{connection_name}'")
    
    def has_cached_credentials(self, connection_name: str) -> bool:
        """Check if connection has cached credentials."""
        cache_key = f"{self.current_user.user_id if self.current_user else 'anonymous'}:{connection_name}"
        return cache_key in ConnectionManager._credential_cache
    
    def get_connection_with_credentials(self, connection_name: str) -> Dict[str, Any]:
        """Get connection config with cached credentials merged in."""
        config = self.get_connection(connection_name)
        cached_creds = self.get_cached_credentials(connection_name)
        
        if cached_creds:
            config.update(cached_creds)
        
        return config


class JobManager:
    """Manages background jobs."""
    
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
    
    def create_job(self, job_id: str, job_type: str) -> Job:
        """Create a new job."""
        job = Job(
            job_id=job_id,
            job_type=job_type,
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self._jobs[job_id] = job
        logger.info(f"Created job '{job_id}' of type '{job_type}'")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: str, 
                         progress: Optional[float] = None,
                         result: Optional[Dict[str, Any]] = None,
                         error: Optional[str] = None):
        """Update job status."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = status
            job.updated_at = datetime.now()
            
            if progress is not None:
                job.progress = progress
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
                
            logger.info(f"Updated job '{job_id}' status to '{status}'")
    
    def list_jobs(self) -> Dict[str, Job]:
        """List all jobs."""
        return self._jobs.copy()
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old jobs to prevent memory issues."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        jobs_to_remove = []
        
        for job_id, job in self._jobs.items():
            if job.updated_at < cutoff and job.status in ["completed", "failed"]:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self._jobs[job_id]
            
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")


# Global instances
_job_manager = None
_metadata_agent = None
_conversation_agent = None
_connection_managers = {}  # Cache for connection managers by user


def get_connection_manager(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_database_session)
) -> ConnectionManager:
    """Dependency to get the connection manager with user context."""
    # Create a cache key based on user ID
    cache_key = current_user.user_id if current_user else "anonymous"
    
    # Check if we have a cached instance
    if cache_key in _connection_managers:
        # Update the database session in case it's stale
        cached_manager = _connection_managers[cache_key]
        cached_manager.db = db
        return cached_manager
    
    # Create new instance and cache it
    manager = ConnectionManager(db, current_user)
    _connection_managers[cache_key] = manager
    return manager


def clear_connection_manager_cache():
    """Clear the connection manager cache. Call this when connections are updated."""
    global _connection_managers
    _connection_managers.clear()
    ConnectionManager.clear_cache()
    
    # Also clear database handler cache
    try:
        from ..utils.database_handlers import clear_database_handler_cache
        clear_database_handler_cache()
    except ImportError:
        logger.warning("Could not import clear_database_handler_cache")
    
    logger.info("Connection manager cache cleared")


def cleanup_stale_connections():
    """Clean up stale connections to prevent memory leaks."""
    try:
        from ..utils.database_handler import SQLAlchemyHandler
        # Dispose connection pools that are no longer needed
        SQLAlchemyHandler.dispose_pools()
        logger.info("Cleaned up stale database connections")
    except Exception as e:
        logger.warning(f"Error cleaning up stale connections: {e}")


def get_job_manager() -> JobManager:
    """Dependency to get the job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


def get_metadata_agent():
    """Dependency to get the metadata agent."""
    global _metadata_agent
    if _metadata_agent is None:
        from ..agent.core import MetadataAgent
        config = {
            'monitoring_interval': 300,
            'learning_interval': 3600,
        }
        _metadata_agent = MetadataAgent(config)
    return _metadata_agent


def get_conversation_agent():
    """Dependency to get the conversation agent."""
    global _conversation_agent
    if _conversation_agent is None:
        from ..agent.conversation import ConversationAgent
        metadata_agent = get_metadata_agent()
        _conversation_agent = ConversationAgent(metadata_agent)
    return _conversation_agent 