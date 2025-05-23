import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from sqlalchemy import text, create_engine
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.pool import QueuePool
from ..config.config import get_db_connection_string, get_db_config, load_config
import re
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

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
        """
        Convenience method for executing parameterized queries with proper binding.
        Example usage:
            db.execute_parameterized_query(
                "SELECT * FROM users WHERE name = :name AND age = :age",
                {"name": "John", "age": 30}
            )
        """
        try:
            if not self.engine:
                raise ValueError("Database connection not established")
            
            with self.engine.connect() as conn:
                parameterized_query = self._build_parameterized_query(query, params)
                result = conn.execute(parameterized_query, params or {})
                return result
                
        except Exception as e:
            logger.error(f"Error executing parameterized query: {str(e)}")
            raise

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Closed connection to database: {self.db_name}")

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()

    def fetch_one(self, query: str, params: Dict = None) -> Optional[Dict]:
        """Fetch a single row from a SELECT query"""
        try:
            result = self.execute_query(query, params)
            row = result.fetchone()
            if row is None:
                return None
                
            # Handle both Row and LegacyRow types
            if hasattr(row, '_mapping'):
                return dict(row._mapping)
            elif hasattr(row, 'keys'):
                return {key: row[key] for key in row.keys()}
            else:
                return dict(row)
        except Exception as e:
            logger.error(f"Error in fetch_one: {str(e)}")
            raise

    def fetch_all(self, query: str, params: Dict = None) -> List[Dict]:
        """Fetch all rows from a SELECT query"""
        try:
            result = self.execute_query(query, params)
            rows = result.fetchall()
            
            # Handle both Row and LegacyRow types
            if rows and hasattr(rows[0], '_mapping'):
                return [dict(row._mapping) for row in rows]
            elif rows and hasattr(rows[0], 'keys'):
                return [{key: row[key] for key in row.keys()} for row in rows]
            else:
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error in fetch_all: {str(e)}")
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
        try:
            db_type = self.engine.url.drivername.split('+')[0]
            
            if db_type == 'postgresql' and use_estimation:
                # Try pg_class statistics first
                stats_sql = """
                    SELECT reltuples::bigint as estimate 
                    FROM pg_class 
                    WHERE relname = :table_name
                """
                stats_result = self.fetch_one(stats_sql, {"table_name": table_name})
                if stats_result and stats_result.get('estimate'):
                    return int(stats_result['estimate'])
                    
                # Try EXPLAIN as fallback
                explain_sql = f"EXPLAIN SELECT * FROM {table_name}"
                explain_result = self.fetch_one(explain_sql)
                if explain_result:
                    explain_text = str(list(explain_result.values())[0])
                    match = re.search(r'rows=(\d+)', explain_text)
                    if match:
                        return int(match.group(1))
                        
            elif db_type == 'mysql' and use_estimation:
                # Try information_schema statistics
                stats_sql = """
                    SELECT table_rows as estimate
                    FROM information_schema.tables
                    WHERE table_name = :table_name
                """
                stats_result = self.fetch_one(stats_sql, {"table_name": table_name})
                if stats_result and stats_result.get('estimate'):
                    return int(stats_result['estimate'])
            
            # Fallback to exact count for all databases
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
    
    _engines = {}  # Class-level dictionary to store connection pools
    
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
        else:
            self._engines[self.db_name] = value

    def connect(self, db_name: str = None) -> None:
        if db_name:
            self.db_name = db_name
        if not self.db_name:
            raise ValueError("Database name not provided")
            
        try:
            # Get or create connection pool for this database
            if self.db_name not in self._engines:
                connection_string = get_db_connection_string(self.db_name)
                db_config = get_db_config(self.db_name)
                
                # Get SQLite-specific configuration if this is a SQLite database
                sqlite_config = {}
                if db_config.get('type') == 'sqlite':
                    config = load_config()
                    sqlite_config = config.get('sqlite', {})
                
                engine_args = {
                    'poolclass': QueuePool,
                    'pool_size': 20,
                    'max_overflow': 10,
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
                self._engines[self.db_name] = create_engine(
                    connection_string,
                    **engine_args
                )
                
                # For SQLite, set pragmas after creating the engine
                if db_config.get('type') == 'sqlite':
                    with self._engines[self.db_name].connect() as conn:
                        conn.execute(text("PRAGMA journal_mode = WAL"))
                        conn.execute(text("PRAGMA synchronous = NORMAL"))
                        conn.execute(text("PRAGMA temp_store = MEMORY"))
                        conn.execute(text(f"PRAGMA cache_size = {sqlite_config.get('cache_size', -2000)}"))
            
            # Get a connection from the pool
            self.connection = self._engines[self.db_name].connect()
            logger.info(f"Connected to database: {self.db_name}")
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise

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

    @classmethod
    def dispose_pools(cls):
        """Dispose all connection pools"""
        for engine in cls._engines.values():
            engine.dispose()
        cls._engines.clear()

    def get_table_schema(self, table_name: str, schema_name: str = None) -> Dict[str, str]:
        """Get table schema"""
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
            
    def get_database_schemas(self) -> List[str]:
        """
        Get all schemas in the database.
        
        Returns:
            List of schema names
        """
        try:
            logger.info(f"Getting schemas for database {self.db_name}")
            
            # Handle different database types
            if self.engine.dialect.name == 'sqlite':
                # SQLite doesn't have schemas in the traditional sense
                return ['main']
                
            elif self.engine.dialect.name == 'mysql':
                # For MySQL, schemas are databases
                query = "SHOW DATABASES"
                results = self.fetch_all(query)
                schemas = [row['Database'] for row in results]
                # Filter out system schemas
                return [schema for schema in schemas if not schema.startswith(('information_schema', 'performance_schema', 'mysql', 'sys'))]
                
            elif self.engine.dialect.name in ('postgresql', 'postgres'):
                # For PostgreSQL
                query = """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT LIKE 'pg_%' 
                    AND schema_name != 'information_schema'
                """
                results = self.fetch_all(query)
                return [row['schema_name'] for row in results]
                
            elif 'duckdb' in self.engine.dialect.name:
                # For DuckDB
                return ['main']
                
            else:
                # Generic approach using SQLAlchemy
                inspector = inspect(self.engine)
                return inspector.get_schema_names()
                
        except Exception as e:
            logger.error(f"Error getting database schemas: {str(e)}")
            return ['public']  # Default fallback
            
    def get_database_tables(self, schema_name: str = None) -> List[str]:
        """
        Get all tables in the specified schema.
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            List of table names
        """
        try:
            logger.info(f"Getting tables for schema {schema_name}")
            
            # Handle different database types
            if self.engine.dialect.name == 'sqlite':
                # For SQLite
                query = """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """
                results = self.fetch_all(query)
                return [row['name'] for row in results]
                
            elif self.engine.dialect.name == 'mysql':
                # For MySQL
                schema_filter = ""
                if schema_name:
                    schema_filter = f"FROM `{schema_name}`"
                query = f"SHOW TABLES {schema_filter}"
                results = self.fetch_all(query)
                key = next(iter(results[0].keys())) if results else None
                return [row[key] for row in results] if key else []
                
            elif self.engine.dialect.name in ('postgresql', 'postgres'):
                # For PostgreSQL
                schema_to_use = schema_name or 'public'
                query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema_name 
                    AND table_type = 'BASE TABLE'
                """
                results = self.fetch_all(query, {"schema_name": schema_to_use})
                return [row['table_name'] for row in results]
                
            elif 'duckdb' in self.engine.dialect.name:
                # For DuckDB
                query = "SHOW TABLES"
                results = self.fetch_all(query)
                return [row['name'] for row in results]
                
            else:
                # Generic approach using SQLAlchemy
                inspector = inspect(self.engine)
                return inspector.get_table_names(schema=schema_name)
                
        except Exception as e:
            logger.error(f"Error getting tables for schema {schema_name}: {str(e)}")
            return []
            
    def check_query_cost(self, query: str, table_name: str, schema_name: str = None) -> Tuple[bool, str]:
        """
        Check if a query would be too costly to execute by analyzing the execution plan.
        
        Args:
            query: The query to analyze
            table_name: Name of the table being queried
            schema_name: Optional schema name
            
        Returns:
            Tuple[bool, str]: (is_safe, reason)
        """
        try:
            # For PostgreSQL, use EXPLAIN
            if self.engine.dialect.name in ('postgresql', 'postgres'):
                plan_query = f"EXPLAIN {query}"
                result = self.fetch_all(plan_query)
                
                # Convert result to string for analysis
                plan_text = "\n".join([str(list(row.values())[0]) for row in result])
                
                # Check for sequential scans on large tables
                if "Seq Scan" in plan_text and "cost=" in plan_text:
                    # Extract cost estimate
                    cost_match = re.search(r'cost=(\d+\.\d+)\.\.(\d+\.\d+)', plan_text)
                    if cost_match and float(cost_match.group(2)) > 1000000:
                        return False, f"Query may be too costly (estimated cost: {cost_match.group(2)})"
                        
            # For MySQL, use EXPLAIN
            elif self.engine.dialect.name == 'mysql':
                plan_query = f"EXPLAIN {query}"
                result = self.fetch_all(plan_query)
                
                # Look for full table scans with high row counts
                for row in result:
                    if row.get('type') == 'ALL' and row.get('rows', 0) > 1000000:
                        return False, f"Query requires full table scan of {row.get('rows')} rows"
                        
            # For SQLite, basic check
            elif self.engine.dialect.name == 'sqlite':
                # SQLite doesn't have sophisticated explain, just check query structure
                if "LIMIT" not in query.upper() and table_name in query:
                    # Check table size
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    result = self.fetch_one(count_query)
                    if result and result.get('count', 0) > 1000000:
                        return False, f"Query without LIMIT on large table ({result.get('count')} rows)"
                        
            # Default: consider query safe
            return True, "Query appears to be safe"
            
        except Exception as e:
            logger.warning(f"Error analyzing query cost: {str(e)}")
            # Default to safe if we can't analyze
            return True, "Could not analyze query cost" 