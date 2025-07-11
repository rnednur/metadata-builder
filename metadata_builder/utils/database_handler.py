import json
import logging
import re
import weakref
from typing import Dict, Any, List, Tuple, Optional, Union
from sqlalchemy import text, create_engine
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.pool import QueuePool
from ..config.config import get_db_connection_string, get_db_config, load_config
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

def _validate_sql_identifier(identifier: str) -> bool:
    """Validate SQL identifier to prevent injection attacks."""
    # Allow alphanumeric, underscore, and basic characters
    # Reject suspicious patterns
    if not identifier or len(identifier) > 128:
        return False
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier) is not None

class DatabaseHandler:
    """Base database handler interface"""
    
    def __init__(self, db_name: str = None):
        self.db_name = db_name
        self.connection = None
        self._engine = None
        self.config = get_db_config(db_name) if db_name else None

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        self._engine = value

    def connect(self, db_name: str = None) -> None:
        """Establish database connection"""
        try:
            if db_name:
                self.db_name = db_name
                self.config = get_db_config(db_name)
            
            if not self.config:
                raise ValueError(f"No configuration found for database: {self.db_name}")
            
            connection_string = self.config.get('connection_string')
            if not connection_string:
                raise ValueError(f"No connection string found for database: {self.db_name}")
            
            self._engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10
            )
            
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info(f"Successfully connected to database: {self.db_name}")
            
        except Exception as e:
            logger.error(f"Error connecting to database {self.db_name}: {str(e)}")
            raise

    def _build_parameterized_query(self, query: str, params: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Build a parameterized query based on database type.
        Returns a tuple of (modified_query, modified_params).
        
        Handles different parameter styles:
        - SQLite/SQLAlchemy: :param
        - PostgreSQL/MySQL: %(param)s
        - DuckDB: ?
        - BigQuery/Snowflake: @param
        - Kinetica: ${param}
        """
        if not params:
            return query, {}
            
        db_type = self.config.get('type', '').lower() if self.config else ''
        modified_query = query
        modified_params = params.copy()
        
        if db_type == 'duckdb':
            # Convert :param to ? and maintain parameter order
            param_values = []
            for param_name in sorted(params.keys(), key=len, reverse=True):
                modified_query = modified_query.replace(f":{param_name}", "?")
                param_values.append(params[param_name])
            return modified_query, param_values
            
        elif db_type in ['bigquery', 'snowflake']:
            # Convert :param to @param
            for param_name in sorted(params.keys(), key=len, reverse=True):
                modified_query = modified_query.replace(f":{param_name}", f"@{param_name}")
            return modified_query, modified_params
            
        elif db_type == 'kinetica':
            # Convert :param to ${param}
            for param_name in sorted(params.keys(), key=len, reverse=True):
                modified_query = modified_query.replace(f":{param_name}", f"${{{param_name}}}")
            return modified_query, modified_params
            
        elif db_type in ['postgresql', 'mysql']:
            # Convert :param to %(param)s if needed
            if ':' in query:
                for param_name in sorted(params.keys(), key=len, reverse=True):
                    modified_query = modified_query.replace(f":{param_name}", f"%({param_name})s")
            return modified_query, modified_params
            
        # Default SQLite/:param style for SQLAlchemy
        return modified_query, modified_params

    def execute_query(self, query: Union[str, TextClause], params: Optional[Dict] = None) -> Any:
        """Execute a query with parameters"""
        try:
            if not self.engine:
                raise ValueError("Database connection not established")
            
            if isinstance(query, str):
                # Build parameterized query based on database type
                modified_query, modified_params = self._build_parameterized_query(query, params)
                
                # Convert to TextClause for SQLAlchemy
                if isinstance(modified_query, str):
                    modified_query = text(modified_query)
                
                # Execute with modified parameters
                with self.engine.connect() as conn:
                    result = conn.execute(modified_query, modified_params or {})
                    return result
            else:
                # If query is already a TextClause, execute as is
                with self.engine.connect() as conn:
                    result = conn.execute(query, params or {})
                    return result
                
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise

    def execute_parameterized_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute a parameterized query safely"""
        try:
            if not self.engine:
                raise ValueError("Database connection not established")
                
            # Build parameterized query
            modified_query, modified_params = self._build_parameterized_query(query, params)
            
            # Execute the query
            with self.engine.connect() as conn:
                result = conn.execute(text(modified_query), modified_params or {})
                return result
                
        except Exception as e:
            logger.error(f"Error executing parameterized query: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        if hasattr(self, '_engine') and self._engine:
            self._engine.dispose()
            self._engine = None
        self.connection = None

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

    def fetch_one(self, query: str, params: Dict = None) -> Optional[Dict]:
        """Execute query and return first result"""
        try:
            result = self.execute_query(query, params)
            row = result.fetchone()
            if row:
                # Convert row to dictionary
                return dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
            return None
        except Exception as e:
            logger.error(f"Error fetching one result: {str(e)}")
            raise
        
    def fetch_all(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute query and return all results"""
        try:
            result = self.execute_query(query, params)
            rows = result.fetchall()
            # Convert rows to list of dictionaries
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error fetching all results: {str(e)}")
            raise

    def insert(self, table: str, data: Dict) -> Any:
        """Insert data into table"""
        raise NotImplementedError

    def update(self, table: str, data: Dict, condition: Dict) -> Any:
        """Update data in table"""
        raise NotImplementedError

    def delete(self, table: str, condition: Dict) -> Any:
        """Delete data from table"""
        raise NotImplementedError

    def get_table_schema(self, table_name: str, schema_name: str = None) -> Dict[str, str]:
        """Get table schema"""
        # Validate inputs to prevent SQL injection
        if not _validate_sql_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        if schema_name and not _validate_sql_identifier(schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")
            
        try:
            logger.info(f"Getting table schema for {table_name} {self.engine.dialect.name}")
            if self.engine.dialect.name == 'sqlite':
                # For SQLite, use PRAGMA table_info
                query = f"PRAGMA table_info({table_name})"
                results = self.fetch_all(query)
                return {row['name']: row['type'] for row in results}
            
            # For other databases, use information_schema
            query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = :table_name
            """
            params = {"table_name": table_name}
            
            # Add schema filter if provided
            if schema_name:
                query += " AND table_schema = :schema_name"
                params["schema_name"] = schema_name
                
            results = self.fetch_all(query, params)
            return {row['column_name']: row['data_type'] for row in results}
            
        except Exception as e:
            logger.error(f"Error getting table schema: {str(e)}")
            return {}

    def get_table_data(self, table_name: str, limit: int = None, offset: int = None) -> List[Dict]:
        """Get table data with optional pagination"""
        raise NotImplementedError

    def get_primary_keys(self, table_name: str, schema_name: str = None) -> List[str]:
        """
        Get primary key columns for a given table.
        
        Args:
            table_name: Name of the table
            schema_name: Optional schema name
            
        Returns:
            List of primary key column names
        """
        # Validate inputs
        if not _validate_sql_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        if schema_name and not _validate_sql_identifier(schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")
            
        try:
            # Check if this is a SQLite database
            if self.config and self.config.get('type') == 'sqlite':
                # SQLite-specific query to get primary keys
                # Pass table name as a parameter to be handled by execute_query
                query = """
                    SELECT name FROM pragma_table_info(?) 
                    WHERE pk > 0 
                    ORDER BY pk
                """
                result = self.fetch_all(query, {"table_name": table_name})
                return [row['name'] for row in result]
            else:
                # PostgreSQL/other databases using information_schema
                query = """
                    SELECT column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = :table_name 
                    AND tc.constraint_type = 'PRIMARY KEY'
                """
                params = {"table_name": table_name}
                
                # Add schema filter if provided
                if schema_name:
                    query += " AND tc.table_schema = :schema_name"
                    params["schema_name"] = schema_name
                    
                result = self.fetch_all(query, params)
                return [row['column_name'] for row in result]
                
        except Exception as e:
            logger.error(f"Error getting primary keys for table {table_name}: {str(e)}")
            # Return empty list instead of raising error
            return []

    def get_table_constraints(self, table_name: str, schema_name: str = 'public') -> Dict[str, Any]:
        """Base method for getting table constraints"""
        raise NotImplementedError

    def get_database_schemas(self) -> List[str]:
        """Get all schemas in the database"""
        raise NotImplementedError

    def get_database_tables(self, schema_name: str = None) -> List[str]:
        """Get all tables in the specified schema"""
        raise NotImplementedError

    def get_table_indexes(self, table_name: str, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """
        Get table indexes for different database types
        
        Returns:
            List of dictionaries containing index information:
            [
                {
                    "name": "Name of the Index",
                    "columns": ["List of Columns"],
                    "description": "Description of Index"
                }
            ]
        """
        raise NotImplementedError("Each database handler must implement get_table_indexes")

    def get_row_count(self, table_name: str, schema_name: str = None, use_estimation: bool = True) -> Optional[int]:
        # Validate inputs
        if not _validate_sql_identifier(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        if schema_name and not _validate_sql_identifier(schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")
            
        try:
            # For now, let's use the simple and reliable exact count method
            # The estimation methods can be added back later once parameter binding is fixed
            table_ref = f"{schema_name}.{table_name}" if schema_name else table_name
            count_sql = f"SELECT COUNT(*) as count FROM {table_ref}"
            result = self.fetch_one(count_sql)
            return int(result['count']) if result else None
            
        except Exception as e:
            logger.warning(f"Error getting row count for table {table_name}: {str(e)}")
            return None

    def check_query_cost(self, query: str, table_name: str, schema_name: str = None) -> Tuple[bool, str]:
        """
        Check if a query would be too costly to execute by analyzing the execution plan.
        
        Args:
            query: The query to analyze
            table_name: Name of the table being queried
            schema_name: Optional schema name
            
        Returns:
            Tuple[bool, str]: (is_safe, reason)
            - is_safe: True if query is safe to execute, False otherwise
            - reason: Explanation of why query is unsafe (if is_safe is False)
        """
        raise NotImplementedError("Each database handler must implement check_query_cost")

class SQLAlchemyHandler(DatabaseHandler):
    """SQLAlchemy implementation of DatabaseHandler"""
    
    # Use weak references to prevent memory leaks
    _engines = weakref.WeakValueDictionary()
    _connection_count = {}
    _max_connections_per_db = 5  # Limit concurrent connections per database
    
    def __init__(self, db_name: str = None):
        super().__init__(db_name)
        if db_name:
            self.connect(db_name)

    @property
    def engine(self):
        """Get the SQLAlchemy engine for the current database"""
        if self.db_name not in self._engines:
            raise ValueError(f"No engine found for database {self.db_name}")
        return self._engines[self.db_name]

    @engine.setter
    def engine(self, value):
        if value is None:
            if self.db_name in self._engines:
                del self._engines[self.db_name]
                self._connection_count.pop(self.db_name, None)
        else:
            self._engines[self.db_name] = value
            self._connection_count[self.db_name] = self._connection_count.get(self.db_name, 0) + 1

    def connect(self, db_name: str = None) -> None:
        if db_name:
            self.db_name = db_name
        if not self.db_name:
            raise ValueError("Database name not provided")
            
        try:
            # Check if we already have too many connections to this database
            current_connections = self._connection_count.get(self.db_name, 0)
            if current_connections >= self._max_connections_per_db:
                logger.warning(f"Maximum connections ({self._max_connections_per_db}) reached for database {self.db_name}")
            
            # Get or create connection pool for this database
            if self.db_name not in self._engines:
                connection_string = get_db_connection_string(self.db_name)
                db_config = get_db_config(self.db_name)
                
                # Get SQLite-specific configuration if this is a SQLite database
                sqlite_config = {}
                if db_config.get('type') == 'sqlite':
                    config = load_config()
                    sqlite_config = config.get('sqlite', {})
                
                # Reduced pool sizes to limit connections
                engine_args = {
                    'poolclass': QueuePool,
                    'pool_size': 3,  # Reduced from 20
                    'max_overflow': 2,  # Reduced from 10
                    'pool_timeout': 30,
                    'pool_recycle': 1800,
                    'pool_pre_ping': True
                }
                
                # Add SQLite-specific configuration
                if db_config.get('type') == 'sqlite':
                    engine_args.update({
                        'connect_args': {
                            'timeout': 30,  # Connection timeout in seconds
                            'check_same_thread': False  # Allow multi-threading
                        }
                    })
                
                # Create the engine
                engine = create_engine(
                    connection_string,
                    **engine_args
                )
                self._engines[self.db_name] = engine
                
                # For SQLite, set pragmas after creating the engine
                if db_config.get('type') == 'sqlite':
                    with engine.connect() as conn:
                        conn.execute(text("PRAGMA journal_mode = WAL"))
                        conn.execute(text("PRAGMA synchronous = NORMAL"))
                        conn.execute(text("PRAGMA temp_store = MEMORY"))
                        conn.execute(text(f"PRAGMA cache_size = {sqlite_config.get('cache_size', -2000)}"))
            
            # Don't create a new connection if we already have one
            if not self.connection:
                # Get a connection from the pool
                self.connection = self._engines[self.db_name].connect()
                self._connection_count[self.db_name] = self._connection_count.get(self.db_name, 0) + 1
                logger.info(f"Connected to database: {self.db_name}")
            else:
                logger.debug(f"Reusing existing connection to database: {self.db_name}")
                
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise

    def connect_with_config(self, db_config: Dict[str, Any]) -> None:
        """
        Connect to database using provided configuration instead of looking up config files.
        This is used when connection info comes from ConnectionManager (user/system connections).
        """
        if not self.db_name:
            raise ValueError("Database name not provided")
            
        try:
            # Get or create connection pool for this database
            if self.db_name not in self._engines:
                # Build connection string from provided config
                connection_string = self._build_connection_string(db_config)
                
                # Get SQLite-specific configuration if this is a SQLite database
                sqlite_config = {}
                if db_config.get('type') == 'sqlite':
                    config = load_config()
                    sqlite_config = config.get('sqlite', {})
                
                # Reduced pool sizes to limit connections
                engine_args = {
                    'poolclass': QueuePool,
                    'pool_size': 3,  # Reduced from 20
                    'max_overflow': 2,  # Reduced from 10
                    'pool_timeout': 30,
                    'pool_recycle': 1800,
                    'pool_pre_ping': True
                }
                
                # Add SQLite-specific configuration
                if db_config.get('type') == 'sqlite':
                    engine_args.update({
                        'connect_args': {
                            'timeout': 30,  # Connection timeout in seconds
                            'check_same_thread': False  # Allow multi-threading
                        }
                    })
                
                # Create the engine
                engine = create_engine(
                    connection_string,
                    **engine_args
                )
                self._engines[self.db_name] = engine
                
                # For SQLite, set pragmas after creating the engine
                if db_config.get('type') == 'sqlite':
                    with engine.connect() as conn:
                        conn.execute(text("PRAGMA journal_mode = WAL"))
                        conn.execute(text("PRAGMA synchronous = NORMAL"))
                        conn.execute(text("PRAGMA temp_store = MEMORY"))
                        conn.execute(text(f"PRAGMA cache_size = {sqlite_config.get('cache_size', -2000)}"))
            
            # Don't create a new connection if we already have one
            if not self.connection:
                # Get a connection from the pool
                self.connection = self._engines[self.db_name].connect()
                self._connection_count[self.db_name] = self._connection_count.get(self.db_name, 0) + 1
                logger.info(f"Connected to database: {self.db_name}")
            else:
                logger.debug(f"Reusing existing connection to database: {self.db_name}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise

    def _build_connection_string(self, config: Dict[str, Any]) -> str:
        """
        Build a connection string from configuration dictionary.
        """
        db_type = config.get('type', '').lower()
        
        if db_type == 'postgresql':
            return (f"postgresql://{config.get('username')}:{config.get('password')}@"
                   f"{config.get('host')}:{config.get('port', 5432)}/"
                   f"{config.get('database')}")
                   
        elif db_type == 'mysql':
            return (f"mysql+pymysql://{config.get('username')}:{config.get('password')}@"
                   f"{config.get('host')}:{config.get('port', 3306)}/"
                   f"{config.get('database')}")
                   
        elif db_type == 'sqlite':
            db_path = config.get('database', config.get('path'))
            if not db_path:
                raise ValueError("SQLite database path not specified")
            return f"sqlite:///{db_path}"
            
        elif db_type == 'oracle':
            if config.get('service_name'):
                return (f"oracle+cx_oracle://{config.get('username')}:{config.get('password')}@"
                       f"{config.get('host')}:{config.get('port', 1521)}/"
                       f"?service_name={config.get('service_name')}")
            elif config.get('sid'):
                return (f"oracle+cx_oracle://{config.get('username')}:{config.get('password')}@"
                       f"{config.get('host')}:{config.get('port', 1521)}/"
                       f"{config.get('sid')}")
            else:
                raise ValueError("Oracle connection requires either service_name or sid")
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def execute_query(self, query: Union[str, TextClause], params: Optional[Dict] = None) -> Any:
        try:
            if not self.connection:
                self.connect(self.db_name)
                
            if isinstance(query, str):
                query = text(query)
                
            result = self.connection.execute(query, params or {})
            return result
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise
        
    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None
            # Decrement connection count
            if self.db_name in self._connection_count:
                self._connection_count[self.db_name] = max(0, self._connection_count[self.db_name] - 1)

    @classmethod
    def dispose_pools(cls):
        """Dispose all connection pools"""
        for engine in list(cls._engines.values()):
            try:
                engine.dispose()
            except Exception as e:
                logger.warning(f"Error disposing engine: {e}")
        cls._engines.clear()
        cls._connection_count.clear()

    @classmethod
    def get_connection_stats(cls) -> Dict[str, int]:
        """Get connection pool statistics"""
        return dict(cls._connection_count) 