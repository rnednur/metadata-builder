import json
import logging
import re
from typing import Dict, Any, List, Tuple, Optional

from .database_handler import SQLAlchemyHandler
from ..config.config import get_db_connection_string, get_db_config

logger = logging.getLogger(__name__)

class PostgreSQLHandler(SQLAlchemyHandler):
    """PostgreSQL specific implementation of DatabaseHandler"""
    
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