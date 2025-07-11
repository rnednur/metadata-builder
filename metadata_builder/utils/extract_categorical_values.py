import logging
import pandas as pd
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

def _validate_identifier(identifier: str) -> bool:
    """Validate SQL identifier to prevent injection."""
    # Only allow alphanumeric, underscore, and basic characters
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier) is not None

def extract_categorical_values(df: pd.DataFrame, categorical_columns: List[str], db_name: str, schema_name: str, table_name: str) -> Dict[str, List[Any]]:
    """
    Extract unique values for categorical columns, using direct SQL for smaller tables.
    
    Args:
        df: Sample DataFrame
        categorical_columns: List of categorical column names
        db_name: Database name
        schema_name: Schema name
        table_name: Table name
        
    Returns:
        Dictionary mapping column names to their unique values
    """
    from .database_handler import SQLAlchemyHandler  # Import here to avoid circular imports
    
    # Validate identifiers to prevent SQL injection
    if not _validate_identifier(schema_name):
        raise ValueError(f"Invalid schema name: {schema_name}")
    if not _validate_identifier(table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    
    db = SQLAlchemyHandler(db_name)
    categorical_values = {}

    max_unique_values = 20
    min_unique_values = 2
    try:
        # Get total row count using parameterized query
        if db.engine.dialect.name == 'sqlite':
            count_sql = f"SELECT COUNT(*) as count FROM {table_name}"
        else:
            count_sql = """
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = :schema_name AND table_name = :table_name
            """
        
        result = db.fetch_one(count_sql, {"schema_name": schema_name, "table_name": table_name})
        row_count = result['count'] if result and 'count' in result else 0
        
        # Get actual row count if table exists
        if row_count > 0:
            if db.engine.dialect.name == 'sqlite':
                actual_count_sql = f"SELECT COUNT(*) as count FROM {table_name}"
                result = db.fetch_one(actual_count_sql)
            else:
                actual_count_sql = f"SELECT COUNT(*) as count FROM {schema_name}.{table_name}"
                result = db.fetch_one(actual_count_sql)
            row_count = result['count'] if result else 0
        
        for col in categorical_columns:
            # Validate column name
            if not _validate_identifier(col):
                logger.warning(f"Skipping invalid column name: {col}")
                continue
                
            try:
                if row_count <= 10000:
                    # For smaller tables, use SELECT DISTINCT with proper quoting
                    if db.engine.dialect.name == 'sqlite':
                        distinct_sql = f"""
                            SELECT DISTINCT "{col}" 
                            FROM {table_name} 
                            WHERE "{col}" IS NOT NULL 
                            ORDER BY "{col}"
                            LIMIT 30
                        """
                        results = db.fetch_all(distinct_sql)
                    else:
                        distinct_sql = f"""
                            SELECT DISTINCT "{col}" 
                            FROM {schema_name}.{table_name} 
                            WHERE "{col}" IS NOT NULL 
                            ORDER BY "{col}"
                            LIMIT 30
                        """
                        results = db.fetch_all(distinct_sql)
                    unique_vals = [row[col] for row in results]
                else:
                    # For larger tables, use the sample data
                    unique_vals = df[col].dropna().apply(
                        lambda x: x if not isinstance(x, list) else str(x)
                    ).unique().tolist()
                
                # Skip if too many unique values
                if len(unique_vals) > max_unique_values:
                    logger.info(f"Skipping {col}: too many unique values ({len(unique_vals)} > {max_unique_values})")
                    continue
                    
                # Filter values that are meaningful enough for definition
                meaningful_values = [
                    str(val) for val in unique_vals 
                    if isinstance(val, (str, int, float)) and
                    not is_date_like(str(val))  # Skip date-like values
                ]
                
                if not meaningful_values:
                    logger.info(f"Skipping {col}: no meaningful values found")
                    continue

                
                categorical_values[col] = unique_vals
                logger.info(f"Extracted {len(unique_vals)} unique values for column {col}")
                
            except Exception as e:
                logger.warning(f"Error extracting categorical values for column {col}: {str(e)}")
                # Fall back to sample data if SQL fails
                unique_vals = df[col].dropna().apply(
                    lambda x: x if not isinstance(x, list) else str(x)
                ).unique().tolist()
                categorical_values[col] = unique_vals
    
    finally:
        db.close()
        
    return categorical_values

def is_date_like(value: str) -> bool:
    """Check if a string looks like a date."""
    import re
    # Common date patterns
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
        r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
        r'\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}'  # DD Month YYYY
    ]
    return any(re.match(pattern, value, re.IGNORECASE) for pattern in date_patterns) 