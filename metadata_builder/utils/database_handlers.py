import json
import logging
import re
from typing import Dict, Any, List, Tuple, Optional

from .database_handler import SQLAlchemyHandler
from ..config.config import get_db_connection_string, get_db_config

logger = logging.getLogger(__name__)

# Cache for database handlers to avoid creating too many instances
_handler_cache = {}

def get_database_handler(db_name: str, connection_manager=None) -> SQLAlchemyHandler:
    """
    Factory function to get the appropriate database handler based on database type.
    Uses caching to avoid creating too many handler instances.
    
    Args:
        db_name: Database connection name
        connection_manager: Optional ConnectionManager instance to get connection config
        
    Returns:
        Appropriate database handler instance
    """
    try:
        # Check cache first
        if db_name in _handler_cache:
            cached_handler = _handler_cache[db_name]
            # Verify the connection is still valid
            if cached_handler.connection and not cached_handler.connection.closed:
                logger.debug(f"Reusing cached database handler for {db_name}")
                return cached_handler
            else:
                # Remove invalid cached handler
                logger.debug(f"Removing invalid cached handler for {db_name}")
                del _handler_cache[db_name]
        
        # Try to get config from connection manager first (handles user/system/config connections)
        db_config = None
        if connection_manager and connection_manager.connection_exists(db_name):
            # Get config with cached credentials merged in
            db_config = connection_manager.get_connection_with_credentials(db_name)
        
        # Fallback to config file if no connection manager provided
        if not db_config:
            db_config = get_db_config(db_name)
        
        if not db_config:
            logger.warning(f"No config found for database {db_name}, using default SQLAlchemyHandler")
            handler = SQLAlchemyHandler(db_name)
            _handler_cache[db_name] = handler
            return handler
        
        db_type = db_config.get('type', '').lower()
        
        # Create handler without auto-connecting to avoid config file dependency
        if db_type == 'postgresql':
            handler = PostgreSQLHandler(None)  # Don't auto-connect
        elif db_type == 'sqlite':
            handler = SQLiteHandler(None)
        elif db_type == 'mysql':
            handler = MySQLHandler(None)
        elif db_type == 'oracle':
            handler = OracleHandler(None)
        elif db_type == 'bigquery':
            from ..utils.bigquery_handler import BigQueryHandler
            handler = BigQueryHandler(None)
        else:
            logger.warning(f"Unsupported database type {db_type} for {db_name}, using default SQLAlchemyHandler")
            handler = SQLAlchemyHandler(None)
        
        # Set connection info and connect manually
        handler.db_name = db_name
        handler.config = db_config
        handler.connect_with_config(db_config)
        
        # Cache the handler
        _handler_cache[db_name] = handler
        
        return handler
            
    except Exception as e:
        logger.error(f"Error creating database handler for {db_name}: {str(e)}")
        # Fallback to basic handler
        handler = SQLAlchemyHandler(db_name)
        _handler_cache[db_name] = handler
        return handler


def clear_database_handler_cache():
    """Clear the database handler cache. Call this when connections are updated."""
    global _handler_cache
    # Close all cached connections
    for handler in _handler_cache.values():
        try:
            handler.close()
        except Exception as e:
            logger.warning(f"Error closing cached handler: {e}")
    _handler_cache.clear()
    logger.info("Database handler cache cleared")

class PostgreSQLHandler(SQLAlchemyHandler):
    """PostgreSQL specific implementation of DatabaseHandler"""
    
    def get_database_tables(self, schema_name: str = None) -> List[str]:
        """
        Get tables in PostgreSQL database
        
        Args:
            schema_name: Schema name (optional, defaults to 'public')
            
        Returns:
            List of table names
        """
        try:
            if not schema_name:
                schema_name = 'public'
            
            # PostgreSQL-specific query to get tables
            tables_query = """
                SELECT 
                    table_name 
                FROM 
                    information_schema.tables 
                WHERE 
                    table_schema = :schema_name
                    AND table_type = 'BASE TABLE'
                ORDER BY 
                    table_name
            """
            results = self.fetch_all(tables_query, {"schema_name": schema_name})
            return [row.get('table_name') for row in results]
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL tables: {str(e)}")
            return []
    
    def get_table_indexes(self, table_name: str, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """
        Get table indexes for PostgreSQL
        
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
        try:
            # PostgreSQL specific query
            index_query = """
                SELECT
                    i.relname as index_name,
                    array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as column_names,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary,
                    am.amname as index_type
                FROM
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a,
                    pg_am am
                WHERE
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relname = :table_name
                    AND t.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = :schema_name)
                    AND i.relam = am.oid
                GROUP BY
                    i.relname,
                    ix.indisunique,
                    ix.indisprimary,
                    am.amname;
            """
            results = self.fetch_all(index_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Convert results to standard format
            indexes = []
            for row in results:
                # Skip primary key indexes as they're handled by constraints
                if row.get('is_primary', False):
                    continue
                    
                index_type = row.get('index_type', 'INDEX')
                is_unique = row.get('is_unique', False)
                
                # Build index description
                description = f"{index_type.upper()} index"
                if is_unique:
                    description = f"UNIQUE {description}"
                
                indexes.append({
                    "name": row['index_name'],
                    "columns": row['column_names'] if isinstance(row['column_names'], list) else [row['column_names']],
                    "description": description
                })
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL table indexes: {str(e)}")
            return []

    def get_detailed_table_info(self, table_name: str, schema_name: str = 'public') -> Dict[str, Any]:
        """
        Get comprehensive table information including columns with constraints and indexes
        
        Args:
            table_name: Table name
            schema_name: Schema name (defaults to 'public')
            
        Returns:
            Dictionary with detailed table information including:
            - columns: List of ColumnInfo objects
            - indexes: List of IndexInfo objects  
            - table_type: Type of table
            - comment: Table comment
        """
        try:
            # Get detailed column information with constraints
            columns_query = """
                SELECT 
                    c.column_name,
                    c.data_type,
                    c.is_nullable,
                    c.column_default,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale,
                    col_desc.description as column_comment,
                    -- Check if column is part of primary key
                    CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                    -- Check if column is part of unique constraint
                    CASE WHEN uc.column_name IS NOT NULL THEN true ELSE false END as is_unique,
                    -- Foreign key information
                    fk.foreign_table_name,
                    fk.foreign_column_name
                FROM 
                    information_schema.columns c
                LEFT JOIN (
                    -- Primary key columns
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = :table_name 
                        AND tc.table_schema = :schema_name
                        AND tc.constraint_type = 'PRIMARY KEY'
                ) pk ON c.column_name = pk.column_name
                LEFT JOIN (
                    -- Unique constraint columns
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = :table_name 
                        AND tc.table_schema = :schema_name
                        AND tc.constraint_type = 'UNIQUE'
                ) uc ON c.column_name = uc.column_name
                LEFT JOIN (
                    -- Foreign key information
                    SELECT 
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.table_name = :table_name 
                        AND tc.table_schema = :schema_name
                        AND tc.constraint_type = 'FOREIGN KEY'
                ) fk ON c.column_name = fk.column_name
                LEFT JOIN (
                    -- Column comments
                    SELECT 
                        a.attname as column_name,
                        pg_catalog.col_description(a.attrelid, a.attnum) as description
                    FROM pg_catalog.pg_attribute a
                    JOIN pg_catalog.pg_class pgc ON pgc.oid = a.attrelid
                    JOIN pg_catalog.pg_namespace n ON n.oid = pgc.relnamespace
                    WHERE pgc.relname = :table_name
                        AND n.nspname = :schema_name
                        AND a.attnum > 0
                        AND NOT a.attisdropped
                ) col_desc ON c.column_name = col_desc.column_name
                WHERE 
                    c.table_name = :table_name 
                    AND c.table_schema = :schema_name
                ORDER BY c.ordinal_position
            """
            
            columns_result = self.fetch_all(columns_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Convert to ColumnInfo objects
            from ..api.models import ColumnInfo
            columns = []
            for col in columns_result:
                columns.append(ColumnInfo(
                    name=col['column_name'],
                    data_type=col['data_type'],
                    is_nullable=col['is_nullable'] == 'YES',
                    default_value=col['column_default'],
                    is_primary_key=col['is_primary_key'],
                    is_foreign_key=bool(col['foreign_table_name']),
                    foreign_key_table=col['foreign_table_name'],
                    foreign_key_column=col['foreign_column_name'],
                    is_unique=col['is_unique'],
                    character_maximum_length=col['character_maximum_length'],
                    numeric_precision=col['numeric_precision'],
                    numeric_scale=col['numeric_scale'],
                    comment=col['column_comment']
                ))
            
            # Get indexes using existing method
            indexes_data = self.get_table_indexes(table_name, schema_name)
            
            # Convert to IndexInfo objects
            from ..api.models import IndexInfo
            indexes = []
            for idx in indexes_data:
                indexes.append(IndexInfo(
                    name=idx['name'],
                    columns=idx['columns'],
                    is_unique='UNIQUE' in idx.get('description', '').upper(),
                    is_primary='PRIMARY' in idx.get('description', '').upper(),
                    index_type=idx.get('description', 'INDEX')
                ))
            
            # Get table information
            table_info_query = """
                SELECT 
                    table_type,
                    obj_description(pgc.oid) as table_comment
                FROM information_schema.tables t
                LEFT JOIN pg_catalog.pg_class pgc ON pgc.relname = t.table_name
                LEFT JOIN pg_catalog.pg_namespace n ON n.oid = pgc.relnamespace
                WHERE t.table_name = :table_name 
                    AND t.table_schema = :schema_name
                    AND n.nspname = :schema_name
            """
            
            table_info_result = self.fetch_one(table_info_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            table_type = "table"
            table_comment = None
            if table_info_result:
                table_type = table_info_result.get('table_type', 'BASE TABLE').lower()
                table_comment = table_info_result.get('table_comment')
                
            return {
                "columns": columns,
                "indexes": indexes,
                "table_type": table_type,
                "comment": table_comment
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed PostgreSQL table info: {str(e)}")
            return {
                "columns": [],
                "indexes": [],
                "table_type": "table",
                "comment": None
            }
    
    def get_database_schemas(self) -> List[str]:
        """
        Get available schemas in PostgreSQL database
        
        Returns:
            List of schema names
        """
        try:
            # PostgreSQL-specific query to get accessible schemas
            schema_query = """
                SELECT 
                    schema_name 
                FROM 
                    information_schema.schemata 
                WHERE 
                    schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND schema_name NOT LIKE 'pg_temp_%'
                    AND schema_name NOT LIKE 'pg_toast_temp_%'
                ORDER BY 
                    schema_name
            """
            results = self.fetch_all(schema_query, {})
            return [row.get('schema_name') for row in results]
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL schemas: {str(e)}")
            return []

class SQLiteHandler(SQLAlchemyHandler):
    """SQLite specific implementation of DatabaseHandler"""
    
    def get_table_indexes(self, table_name: str, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """
        Get table indexes for SQLite
        
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
        try:
            # SQLite specific query
            index_query = """
                SELECT 
                    name as index_name,
                    sql as index_sql
                FROM sqlite_master 
                WHERE type = 'index' 
                AND tbl_name = :table_name
                AND name NOT LIKE 'sqlite_autoindex%'
            """
            results = self.fetch_all(index_query, {"table_name": table_name})
            
            # Process SQLite results
            indexes = []
            for row in results:
                # Parse column names from index SQL
                index_sql = row['index_sql']
                if index_sql:
                    # Extract column names from SQL like "CREATE INDEX idx_name ON table_name (col1, col2)"
                    match = re.search(r'\((.*?)\)', index_sql)
                    if match:
                        columns = [c.strip() for c in match.group(1).split(',')]
                        is_unique = 'UNIQUE' in index_sql.upper()
                        
                        # Build index description
                        description = "INDEX"
                        if is_unique:
                            description = "UNIQUE INDEX"
                        
                        indexes.append({
                            "name": row['index_name'],
                            "columns": columns,
                            "description": description
                        })
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting SQLite table indexes: {str(e)}")
            return []

class MySQLHandler(SQLAlchemyHandler):
    """MySQL specific implementation of DatabaseHandler"""
    
    def get_table_indexes(self, table_name: str, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """
        Get table indexes for MySQL
        
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
        try:
            # MySQL specific query
            index_query = """
                SHOW INDEX FROM `{table_name}`
            """.format(table_name=table_name)
            results = self.fetch_all(index_query)
            
            # Process MySQL results
            indexes = []
            current_index = None
            
            for row in results:
                if row['Key_name'] == 'PRIMARY':
                    continue
                    
                if current_index is None or current_index['name'] != row['Key_name']:
                    if current_index is not None:
                        indexes.append(current_index)
                    
                    is_unique = row['Non_unique'] == 0
                    description = "UNIQUE INDEX" if is_unique else "INDEX"
                    
                    current_index = {
                        'name': row['Key_name'],
                        'columns': [],
                        'description': description
                    }
                current_index['columns'].append(row['Column_name'])
            
            if current_index is not None:
                indexes.append(current_index)
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting MySQL table indexes: {str(e)}")
            return []

class OracleHandler(SQLAlchemyHandler):
    """Oracle specific implementation of DatabaseHandler"""
    
    def get_database_schemas(self) -> List[str]:
        """
        Get available schemas/users in Oracle database
        
        Returns:
            List of schema names
        """
        try:
            # Oracle-specific query to get accessible schemas
            schema_query = """
                SELECT 
                    username AS schema_name
                FROM 
                    all_users
                WHERE 
                    username NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'CTXSYS', 'DBSFWUSER', 'GSMADMIN_INTERNAL', 
                                   'GSMCATUSER', 'GSMUSER', 'LBACSYS', 'MDSYS', 'OJVMSYS', 'OLAPSYS', 'ORDDATA', 'ORDPLUGINS', 
                                   'ORDSYS', 'WMSYS', 'XDB', 'DVSYS', 'DVF', 'AUDSYS')
                AND
                    username NOT LIKE 'APEX%'
                ORDER BY 
                    username
            """
            results = self.fetch_all(schema_query)
            return [row.get('schema_name') for row in results]
            
        except Exception as e:
            logger.error(f"Error getting Oracle schemas: {str(e)}")
            return []
    
    def get_database_tables(self, schema_name: str = None) -> List[str]:
        """
        Get tables in Oracle database
        
        Args:
            schema_name: Schema/owner name (optional, defaults to current user schema)
            
        Returns:
            List of table names
        """
        try:
            # If schema_name not provided, use current user schema
            if not schema_name:
                current_user_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS current_schema FROM DUAL"
                result = self.fetch_one(current_user_query)
                if result:
                    schema_name = result.get('current_schema')
                else:
                    logger.error("Unable to determine current Oracle schema")
                    return []
            
            # Oracle-specific query to get tables
            tables_query = """
                SELECT 
                    table_name 
                FROM 
                    all_tables 
                WHERE 
                    owner = :schema_name
                ORDER BY 
                    table_name
            """
            results = self.fetch_all(tables_query, {"schema_name": schema_name.upper()})
            return [row.get('table_name') for row in results]
            
        except Exception as e:
            logger.error(f"Error getting Oracle tables: {str(e)}")
            return []
            
    def get_table_indexes(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        """
        Get table indexes for Oracle
        
        Args:
            table_name: Table name
            schema_name: Schema/owner name (optional, defaults to current user schema)
            
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
        try:
            # If schema_name not provided, use current user schema
            if not schema_name:
                current_user_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS current_schema FROM DUAL"
                result = self.fetch_one(current_user_query)
                if result:
                    schema_name = result.get('current_schema')
                else:
                    logger.error("Unable to determine current Oracle schema")
                    return []
            
            # Oracle-specific query to get indexes
            index_query = """
                SELECT 
                    i.index_name,
                    i.uniqueness,
                    i.index_type,
                    c.column_name
                FROM 
                    all_indexes i
                JOIN 
                    all_ind_columns c ON i.index_name = c.index_name AND i.owner = c.index_owner
                WHERE 
                    i.table_name = :table_name
                AND 
                    i.owner = :schema_name
                AND 
                    i.index_type != 'LOB'
                AND 
                    i.constraint_index = 'NO'
                ORDER BY 
                    i.index_name, c.column_position
            """
            
            results = self.fetch_all(index_query, {
                "table_name": table_name.upper(),
                "schema_name": schema_name.upper()
            })
            
            # Process Oracle results
            indexes = []
            current_index = None
            
            for row in results:
                if current_index is None or current_index['name'] != row['index_name']:
                    if current_index is not None:
                        indexes.append(current_index)
                    
                    is_unique = row['uniqueness'] == 'UNIQUE'
                    index_type = row['index_type']
                    
                    # Build index description
                    description = f"{index_type.upper()} index"
                    if is_unique:
                        description = f"UNIQUE {description}"
                    
                    current_index = {
                        'name': row['index_name'],
                        'columns': [],
                        'description': description
                    }
                
                current_index['columns'].append(row['column_name'])
            
            if current_index is not None:
                indexes.append(current_index)
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting Oracle table indexes: {str(e)}")
            return []
            
    def get_table_constraints(self, table_name: str, schema_name: str = None) -> Dict[str, Any]:
        """
        Get table constraints for Oracle
        
        Args:
            table_name: Table name
            schema_name: Schema/owner name (optional, defaults to current user schema)
            
        Returns:
            Dictionary with constraint information:
            {
                "primary_keys": ["col1", "col2"],
                "foreign_keys": [
                    {
                        "name": "FK_NAME",
                        "columns": ["col1"],
                        "ref_table": "ref_table",
                        "ref_columns": ["ref_col1"],
                        "description": "Foreign key description"
                    }
                ],
                "unique_constraints": [
                    {
                        "name": "UQ_NAME",
                        "columns": ["col1", "col2"],
                        "description": "Unique constraint description"
                    }
                ],
                "check_constraints": [
                    {
                        "name": "CHK_NAME",
                        "columns": ["col1"],
                        "definition": "col1 > 0",
                        "description": "Check constraint description"
                    }
                ]
            }
        """
        constraints = {
            "primary_keys": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "check_constraints": []
        }
        
        try:
            # If schema_name not provided, use current user schema
            if not schema_name:
                current_user_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS current_schema FROM DUAL"
                result = self.fetch_one(current_user_query)
                if result:
                    schema_name = result.get('current_schema')
                else:
                    logger.error("Unable to determine current Oracle schema")
                    return constraints
            
            # Convert to uppercase for Oracle
            table_name = table_name.upper()
            schema_name = schema_name.upper()
            
            # 1. Get primary key constraints
            pk_query = """
                SELECT 
                    cols.column_name
                FROM 
                    all_constraints cons
                JOIN 
                    all_cons_columns cols ON cons.constraint_name = cols.constraint_name 
                    AND cons.owner = cols.owner
                WHERE 
                    cons.constraint_type = 'P'
                AND 
                    cons.table_name = :table_name
                AND 
                    cons.owner = :schema_name
                ORDER BY 
                    cols.position
            """
            
            pk_results = self.fetch_all(pk_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            constraints["primary_keys"] = [row.get('column_name') for row in pk_results]
            
            # 2. Get foreign key constraints
            fk_query = """
                SELECT 
                    a.constraint_name,
                    a.column_name,
                    r.table_name as ref_table,
                    r.column_name as ref_column,
                    c.delete_rule
                FROM 
                    all_cons_columns a
                JOIN 
                    all_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
                JOIN 
                    all_cons_columns r ON c.r_owner = r.owner AND c.r_constraint_name = r.constraint_name
                WHERE 
                    c.constraint_type = 'R'
                AND 
                    a.table_name = :table_name
                AND 
                    a.owner = :schema_name
                ORDER BY 
                    a.constraint_name, a.position
            """
            
            fk_results = self.fetch_all(fk_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Process FK results to group by constraint name
            fk_dict = {}
            for row in fk_results:
                constraint_name = row.get('constraint_name')
                
                if constraint_name not in fk_dict:
                    delete_rule = row.get('delete_rule', 'NO ACTION')
                    description = f"Foreign key to {row.get('ref_table')} "
                    if delete_rule == 'CASCADE':
                        description += "with CASCADE DELETE"
                    elif delete_rule == 'SET NULL':
                        description += "with SET NULL on delete"
                    
                    fk_dict[constraint_name] = {
                        "name": constraint_name,
                        "columns": [],
                        "ref_table": row.get('ref_table'),
                        "ref_columns": [],
                        "description": description
                    }
                
                fk_dict[constraint_name]["columns"].append(row.get('column_name'))
                fk_dict[constraint_name]["ref_columns"].append(row.get('ref_column'))
            
            constraints["foreign_keys"] = list(fk_dict.values())
            
            # 3. Get unique constraints
            uq_query = """
                SELECT 
                    cons.constraint_name,
                    cols.column_name
                FROM 
                    all_constraints cons
                JOIN 
                    all_cons_columns cols ON cons.constraint_name = cols.constraint_name 
                    AND cons.owner = cols.owner
                WHERE 
                    cons.constraint_type = 'U'
                AND 
                    cons.table_name = :table_name
                AND 
                    cons.owner = :schema_name
                ORDER BY 
                    cons.constraint_name, cols.position
            """
            
            uq_results = self.fetch_all(uq_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Process UQ results to group by constraint name
            uq_dict = {}
            for row in uq_results:
                constraint_name = row.get('constraint_name')
                
                if constraint_name not in uq_dict:
                    uq_dict[constraint_name] = {
                        "name": constraint_name,
                        "columns": [],
                        "description": "Unique constraint"
                    }
                
                uq_dict[constraint_name]["columns"].append(row.get('column_name'))
            
            constraints["unique_constraints"] = list(uq_dict.values())
            
            # 4. Get check constraints
            chk_query = """
                SELECT 
                    cons.constraint_name,
                    cons.search_condition,
                    cols.column_name
                FROM 
                    all_constraints cons
                LEFT JOIN 
                    all_cons_columns cols ON cons.constraint_name = cols.constraint_name 
                    AND cons.owner = cols.owner
                WHERE 
                    cons.constraint_type = 'C'
                AND 
                    cons.table_name = :table_name
                AND 
                    cons.owner = :schema_name
                AND
                    NOT (cons.search_condition LIKE '%IS NOT NULL%' OR cons.search_condition LIKE '%IS NOT "NULL"%')
                ORDER BY 
                    cons.constraint_name, cols.position
            """
            
            chk_results = self.fetch_all(chk_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Process CHK results to group by constraint name
            chk_dict = {}
            for row in chk_results:
                constraint_name = row.get('constraint_name')
                
                if constraint_name not in chk_dict:
                    chk_dict[constraint_name] = {
                        "name": constraint_name,
                        "columns": [],
                        "definition": row.get('search_condition'),
                        "description": f"Check constraint: {row.get('search_condition')}"
                    }
                
                column_name = row.get('column_name')
                if column_name and column_name not in chk_dict[constraint_name]["columns"]:
                    chk_dict[constraint_name]["columns"].append(column_name)
            
            constraints["check_constraints"] = list(chk_dict.values())
            
            return constraints
            
        except Exception as e:
            logger.error(f"Error getting Oracle table constraints: {str(e)}")
            return constraints
    
    def get_table_schema(self, table_name: str, schema_name: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Get table schema information for Oracle
        
        Args:
            table_name: Table name
            schema_name: Schema/owner name (optional, defaults to current user schema)
            
        Returns:
            Dictionary with column details:
            {
                "COLUMN_NAME": {
                    "data_type": "VARCHAR2",
                    "full_data_type": "VARCHAR2(255)",
                    "nullable": True,
                    "default": "Default value",
                    "comment": "Column comment if available"
                },
                ...
            }
        """
        try:
            # If schema_name not provided, use current user schema
            if not schema_name:
                current_user_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS current_schema FROM DUAL"
                result = self.fetch_one(current_user_query)
                if result:
                    schema_name = result.get('current_schema')
                else:
                    logger.error("Unable to determine current Oracle schema")
                    return {}
            
            # Convert to uppercase for Oracle
            table_name = table_name.upper()
            schema_name = schema_name.upper()
            
            # Get column information
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale,
                    nullable,
                    data_default,
                    char_length
                FROM 
                    all_tab_columns
                WHERE 
                    table_name = :table_name
                AND 
                    owner = :schema_name
                ORDER BY 
                    column_id
            """
            
            columns_result = self.fetch_all(columns_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Get column comments
            comments_query = """
                SELECT 
                    column_name,
                    comments
                FROM 
                    all_col_comments
                WHERE 
                    table_name = :table_name
                AND 
                    owner = :schema_name
            """
            
            comments_result = self.fetch_all(comments_query, {
                "table_name": table_name,
                "schema_name": schema_name
            })
            
            # Build comments dictionary
            comments_dict = {}
            for comment_row in comments_result:
                column_name = comment_row.get('column_name')
                comments = comment_row.get('comments')
                if column_name and comments:
                    comments_dict[column_name] = comments
            
            # Build schema dictionary
            schema = {}
            for col in columns_result:
                column_name = col.get('column_name')
                data_type = col.get('data_type', '').upper()
                
                # Build full data type
                full_data_type = data_type
                if data_type in ('VARCHAR', 'VARCHAR2', 'CHAR', 'NCHAR', 'NVARCHAR2'):
                    char_length = col.get('char_length')
                    if char_length:
                        full_data_type = f"{data_type}({char_length})"
                elif data_type in ('NUMBER'):
                    precision = col.get('data_precision')
                    scale = col.get('data_scale')
                    if precision is not None:
                        if scale is not None and scale > 0:
                            full_data_type = f"{data_type}({precision},{scale})"
                        else:
                            full_data_type = f"{data_type}({precision})"
                
                schema[column_name] = {
                    "data_type": data_type,
                    "full_data_type": full_data_type,
                    "nullable": col.get('nullable') == 'Y',
                    "default": col.get('data_default'),
                    "comment": comments_dict.get(column_name, '')
                }
            
            return schema
            
        except Exception as e:
            logger.error(f"Error getting Oracle table schema: {str(e)}")
            return {}

    def get_row_count(self, table_name: str, schema_name: str = None, use_estimation: bool = True) -> Optional[int]:
        """
        Get the row count of a table in Oracle
        
        Args:
            table_name: Table name
            schema_name: Schema/owner name (optional, defaults to current user schema)
            use_estimation: Use statistics-based estimation instead of exact count
            
        Returns:
            Number of rows in the table or None if error
        """
        try:
            # If schema_name not provided, use current user schema
            if not schema_name:
                current_user_query = "SELECT SYS_CONTEXT('USERENV', 'CURRENT_SCHEMA') AS current_schema FROM DUAL"
                result = self.fetch_one(current_user_query)
                if result:
                    schema_name = result.get('current_schema')
                else:
                    logger.error("Unable to determine current Oracle schema")
                    return None
            
            # Convert to uppercase for Oracle
            table_name = table_name.upper()
            schema_name = schema_name.upper()
            
            if use_estimation:
                # Try to get estimated row count from statistics
                stats_query = """
                    SELECT 
                        num_rows 
                    FROM 
                        all_tables 
                    WHERE 
                        table_name = :table_name 
                    AND 
                        owner = :schema_name
                """
                
                stats_result = self.fetch_one(stats_query, {
                    "table_name": table_name,
                    "schema_name": schema_name
                })
                
                if stats_result and stats_result.get('num_rows') is not None:
                    return int(stats_result.get('num_rows'))
            
            # Fall back to exact count if estimation is not available or specified
            count_query = f"SELECT COUNT(*) as row_count FROM {schema_name}.{table_name}"
            count_result = self.fetch_one(count_query)
            
            if count_result:
                return int(count_result.get('row_count', 0))
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting Oracle table row count: {str(e)}")
            return None 