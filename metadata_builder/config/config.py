"""Configuration management for metadata builder."""

import os
import logging
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import yaml
from dotenv import load_dotenv
import json

# Load environment variables from .env file if it exists
load_dotenv()

logger = logging.getLogger(__name__)

# Global configuration cache
_config = None

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file, defaults to .config.yaml in the user's directory,
                    then config.yaml in the same directory
        
    Returns:
        Dictionary with configuration
    """
    global _config
    
    if _config is not None:
        return _config
        
    if config_path is None:
        # First try .config.yaml in the current directory
        local_config_path = os.path.join(os.getcwd(), '.config.yaml')
        if os.path.exists(local_config_path):
            config_path = local_config_path
            logger.info(f"Using local configuration from {local_config_path}")
        else:
            # Default to config.yaml in the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            _config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return _config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        # Return empty dict as fallback
        _config = {}
        return _config

def get_db_config(db_name: str) -> Dict[str, Any]:
    """
    Get database configuration.
    
    Args:
        db_name: Name of the database
        
    Returns:
        Dictionary with database configuration
    """
    config = load_config()
    databases = config.get('databases', {})
    
    if db_name not in databases:
        raise ValueError(f"Database '{db_name}' not found in configuration")
        
    return databases[db_name]

def get_db_connection_string(db_name: str) -> str:
    """
    Get database connection string.
    
    Args:
        db_name: Name of the database
        
    Returns:
        Connection string for SQLAlchemy
    """
    db_config = get_db_config(db_name)
    
    # Get connection string from config
    connection_string = db_config.get('connection_string')
    if connection_string:
        # Check for environment variable placeholders
        if '${' in connection_string:
            import re
            env_vars = re.findall(r'\${(.*?)}', connection_string)
            for var in env_vars:
                env_value = os.environ.get(var)
                if env_value:
                    connection_string = connection_string.replace(f'${{{var}}}', env_value)
                else:
                    logger.warning(f"Environment variable {var} not found")
        return connection_string
    
    # Build connection string from individual parameters
    db_type = db_config.get('type', '')
    
    if db_type == 'postgresql':
        return (f"postgresql://{db_config.get('username')}:{db_config.get('password')}@"
                f"{db_config.get('host')}:{db_config.get('port', 5432)}/"
                f"{db_config.get('database')}")
    elif db_type == 'mysql':
        return (f"mysql+pymysql://{db_config.get('username')}:{db_config.get('password')}@"
                f"{db_config.get('host')}:{db_config.get('port', 3306)}/"
                f"{db_config.get('database')}")
    elif db_type == 'sqlite':
        return f"sqlite:///{db_config.get('database')}"
    elif db_type == 'duckdb':
        return f"duckdb:///{db_config.get('database')}"
    elif db_type == 'oracle':
        # Oracle connection string format
        # Format: oracle+cx_oracle://username:password@host:port/?service_name=service
        host = db_config.get('host', 'localhost')
        port = db_config.get('port', 1521)
        username = db_config.get('username', '')
        password = db_config.get('password', '')
        
        # Oracle supports different connection methods
        if db_config.get('service_name'):
            # Connect using service name
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?service_name={db_config.get('service_name')}"
        elif db_config.get('sid'):
            # Connect using SID
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}/?sid={db_config.get('sid')}"
        elif db_config.get('tns_name'):
            # Connect using TNS name
            return f"oracle+cx_oracle://{username}:{password}@{db_config.get('tns_name')}"
        else:
            # Default to basic connection
            return f"oracle+cx_oracle://{username}:{password}@{host}:{port}"
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def get_db_handler(db_name: str):
    """
    Get database handler based on database type.
    
    Args:
        db_name: Name of the database
        
    Returns:
        Database handler instance
    """
    db_config = get_db_config(db_name)
    db_type = db_config.get('type', '')
    
    if db_type == 'postgresql':
        from ..utils.database_handlers import PostgreSQLHandler
        return PostgreSQLHandler(db_name)
    elif db_type == 'sqlite':
        from ..utils.database_handlers import SQLiteHandler
        return SQLiteHandler(db_name)
    elif db_type == 'mysql':
        from ..utils.database_handlers import MySQLHandler
        return MySQLHandler(db_name)
    elif db_type == 'oracle':
        from ..utils.database_handlers import OracleHandler
        return OracleHandler(db_name)
    elif db_type == 'duckdb':
        from ..utils.database_handler import SQLAlchemyHandler
        return SQLAlchemyHandler(db_name)
    else:
        # Default to generic SQLAlchemy handler
        from ..utils.database_handler import SQLAlchemyHandler
        return SQLAlchemyHandler(db_name)

def get_llm_api_config() -> Dict[str, Any]:
    """
    Get LLM API configuration.
    
    Returns:
        Dictionary with LLM API configuration
    """
    config = load_config()
    
    # Get base config with defaults
    llm_config = config.get('llm_api', {}).copy()
    
    # Override with environment variables if set
    if os.environ.get('OPENAI_API_KEY'):
        llm_config['api_key'] = os.environ.get('OPENAI_API_KEY')
    
    if os.environ.get('OPENAI_API_BASE_URL'):
        llm_config['base_url'] = os.environ.get('OPENAI_API_BASE_URL')
        
    if os.environ.get('OPENAI_API_MODEL'):
        llm_config['model'] = os.environ.get('OPENAI_API_MODEL')
        
    return llm_config

def get_glossary_config() -> Dict[str, Any]:
    """
    Get glossary configuration.
    
    Returns:
        Dictionary with glossary configuration
    """
    config = load_config()
    return config.get('glossary', {})

def get_metadata_config() -> Dict[str, Any]:
    """
    Get metadata configuration.
    
    Returns:
        Dictionary with metadata configuration
    """
    config = load_config()
    return config.get('metadata', {})

def get_column_simplification_fields() -> Dict[str, Any]:
    """
    Get column simplification fields.
    
    Returns:
        Dictionary with column simplification fields
    """
    config = load_config()
    return config.get('column_simplification', {})

def get_retry_config() -> Dict[str, Any]:
    """Get retry configuration for API calls.
    
    Returns:
        Dictionary with retry configuration
    """
    return {
        "max_attempts": int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
        "initial_wait": float(os.getenv("RETRY_INITIAL_WAIT_SECONDS", "1")),
        "max_wait": float(os.getenv("RETRY_MAX_WAIT_SECONDS", "10"))
    }

def get_token_tracking_config() -> Dict[str, Any]:
    """Get token tracking configuration.
    
    Returns:
        Dictionary with token tracking configuration
    """
    return {
        "enabled": os.getenv("ENABLE_TOKEN_TRACKING", "true").lower() in ("true", "1", "yes"),
        "max_tokens": int(os.getenv("MAX_TOKENS_PER_REQUEST", "8192"))
    }

def get_database_config() -> Dict[str, Any]:
    """Load database connection configurations from config file.
    
    Returns:
        Dictionary with database configurations
    """
    # First check for .config.yaml in current directory
    local_config_path = Path(".config.yaml")
    if local_config_path.exists():
        try:
            with open(local_config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded database configuration from {local_config_path}")
            return config.get("database", {"connections": {}})
        except Exception as e:
            logger.error(f"Error loading local database config: {str(e)}")
            # Fall through to try the default config
    
    # Check for config.yaml in the current directory
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}")
        return {"connections": {}}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        return config.get("database", {"connections": {}})
    except Exception as e:
        logger.error(f"Error loading database config: {str(e)}")
        return {"connections": {}}

def get_log_level() -> int:
    """Get log level from environment.
    
    Returns:
        Logging level as integer
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return log_levels.get(log_level_name, logging.INFO) 