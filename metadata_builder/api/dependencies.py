"""
FastAPI dependencies for the Metadata Builder API.
"""

import yaml
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from ..config.config import load_config

logger = logging.getLogger(__name__)


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


class ConnectionManager:
    """Manages database connections configuration."""
    
    def __init__(self):
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._load_connections()
    
    def _load_connections(self):
        """Load connections from configuration."""
        try:
            config = load_config()
            databases = config.get('databases', {})
            
            for name, config_data in databases.items():
                self._connections[name] = config_data
                
            logger.info(f"Loaded {len(self._connections)} database connections")
            
        except Exception as e:
            logger.warning(f"Failed to load connections from config: {str(e)}")
    
    def connection_exists(self, name: str) -> bool:
        """Check if a connection exists."""
        return name in self._connections
    
    def get_connection(self, name: str) -> Dict[str, Any]:
        """Get connection configuration by name."""
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        return self._connections[name].copy()
    
    def get_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Get all connections."""
        return self._connections.copy()
    
    def add_connection(self, name: str, config: Dict[str, Any]):
        """Add a new connection."""
        self._connections[name] = config
        logger.info(f"Added connection '{name}'")
    
    def remove_connection(self, name: str):
        """Remove a connection."""
        if name in self._connections:
            del self._connections[name]
            logger.info(f"Removed connection '{name}'")
    
    def update_connection(self, name: str, config: Dict[str, Any]):
        """Update an existing connection."""
        if name not in self._connections:
            raise ValueError(f"Connection '{name}' not found")
        self._connections[name] = config
        logger.info(f"Updated connection '{name}'")


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
_connection_manager = None
_job_manager = None


def get_connection_manager() -> ConnectionManager:
    """Dependency to get the connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_job_manager() -> JobManager:
    """Dependency to get the job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager 