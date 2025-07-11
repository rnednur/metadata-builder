import pandas as pd
import logging
import re
from typing import Dict, List, Tuple, Any, Optional, Set
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def identify_column_types(schema: Dict[str, str], df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Identify categorical and numerical columns
    
    Args:
        schema: Dictionary mapping column names to their data types
        df: DataFrame with sample data
        
    Returns:
        Tuple with lists of categorical and numerical column names
    """
    categorical = []
    numerical = []
    
    for column, dtype in schema.items():
        try:
            # First check if it's explicitly a numeric type in the schema
            if any(num_type in dtype.lower() for num_type in ['int', 'float', 'double', 'decimal', 'numeric']):
                numerical.append(column)
                continue
                
            # Skip if column is not in the DataFrame
            if column not in df.columns:
                continue
                
            # Check if it's a timestamp or date
            if any(date_type in dtype.lower() for date_type in ['timestamp', 'date', 'datetime']):
                categorical.append(column)  # Timestamps are treated as categorical for metadata purposes
                continue
                
            # Check if it's a boolean
            if any(bool_type in dtype.lower() for bool_type in ['bool', 'boolean']):
                categorical.append(column)
                continue
                
            # Check column name for hints
            col_lower = column.lower()
            
            # Common ID patterns suggest categorical
            if col_lower.endswith('_id') or col_lower == 'id' or '_code' in col_lower:
                categorical.append(column)
                continue
                
            # Common patterns for dates and times
            if any(pattern in col_lower for pattern in ['_at', '_date', '_time']):
                categorical.append(column)
                continue
                
            # String/text types are usually categorical
            if any(str_type in dtype.lower() for str_type in ['char', 'text', 'string', 'varchar']):
                # Check cardinality for long string columns
                if df[column].dtype == 'object':
                    # Only sample values for large DataFrames
                    if len(df) > 1000:
                        sample = df[column].sample(1000)
                        unique_ratio = sample.nunique() / len(sample.dropna())
                    else:
                        unique_ratio = df[column].nunique() / len(df[column].dropna()) if len(df[column].dropna()) > 0 else 0
                    
                    # If almost all values are unique and average length is high, it might be a text field, not categorical
                    if unique_ratio > 0.9:
                        avg_length = df[column].astype(str).str.len().mean()
                        if avg_length > 100:  # This is a long text field, not categorical
                            continue
                    
                    categorical.append(column)
                    continue
            
            # Try to convert to numeric and see if it succeeds
            numeric_series = pd.to_numeric(df[column], errors='coerce')
            
            # If most values converted successfully, it's likely numeric
            if numeric_series.notna().mean() > 0.8:
                numerical.append(column)
            else:
                # Otherwise, assume categorical
                categorical.append(column)
                
        except Exception as e:
            logger.warning(f"Error while identifying column type for {column}: {str(e)}")
            # Default to categorical as the safer choice
            categorical.append(column)
            
    return categorical, numerical

def extract_categorical_values(df: pd.DataFrame, categorical_columns: List[str], db_name: str, schema_name: str, table_name: str, connection_manager=None) -> Dict[str, List[Any]]:
    """
    Extract unique values for categorical columns, using direct SQL for smaller tables.
    
    Args:
        df: Sample DataFrame
        categorical_columns: List of categorical column names
        db_name: Database name
        schema_name: Schema name
        table_name: Table name
        connection_manager: Optional connection manager for user/system connections
        
    Returns:
        Dictionary mapping column names to their unique values
    """
    # Get database handler using connection manager if available
    if connection_manager and connection_manager.connection_exists(db_name):
        from .database_handlers import get_database_handler
        db = get_database_handler(db_name, connection_manager)
    else:
        from .database_handler import SQLAlchemyHandler  # Import here to avoid circular imports
        db = SQLAlchemyHandler(db_name)
    result = {}
    
    try:
        # Get total row count to determine if we should use SQL or DataFrame
        row_count = db.get_row_count(table_name, schema_name, use_estimation=True)
        
        for column in categorical_columns:
            try:
                logger.info(f'Extracting categorical values for {column}')
                if column not in df.columns:
                    result[column] = []
                    continue
                    
                # For smaller tables or date-like columns, use direct SQL for better accuracy
                if (row_count and row_count < 100000) or is_date_like(df[column]) or df[column].dtype.name == 'category':
                    # Use SQL to get unique values
                    query = f"""
                        SELECT DISTINCT "{column}" 
                        FROM {schema_name}.{table_name}
                        WHERE "{column}" IS NOT NULL
                        LIMIT 100
                    """
                    
                    try:
                        unique_values = db.fetch_all(query)
                        values = [row[column] for row in unique_values if row.get(column) is not None]
                        
                        # Handle datetime objects
                        processed_values = []
                        for val in values:
                            if isinstance(val, datetime):
                                processed_values.append(val.isoformat())
                            else:
                                processed_values.append(val)
                                
                        result[column] = processed_values[:100]  # Limit to 100 values
                    except Exception as sql_error:
                        logger.warning(f"SQL error for {column}, falling back to DataFrame: {str(sql_error)}")
                        # Fall back to DataFrame if SQL fails
                        result[column] = df[column].dropna().unique().tolist()[:100]
                else:
                    # For larger tables, use the DataFrame sample
                    if df[column].dtype == 'object':
                        # If strings, limit to reasonable length 
                        values = [str(x)[:100] for x in df[column].dropna().unique().tolist()[:100]]
                    else:
                        values = df[column].dropna().unique().tolist()[:100]
                        
                    # Handle datetime objects
                    processed_values = []
                    for val in values:
                        if isinstance(val, datetime):
                            processed_values.append(val.isoformat())
                        else:
                            processed_values.append(val)
                            
                    result[column] = processed_values
                    
            except Exception as e:
                logger.warning(f"Error extracting categorical values for {column}: {str(e)}")
                result[column] = []
    
    finally:
        db.close()
        
    return result

def is_date_like(series: pd.Series) -> bool:
    """
    Check if a series contains date-like values.
    
    Args:
        series: Series to check
        
    Returns:
        True if the series contains date-like values
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
        
    if series.dtype == 'object':
        # Check a sample of non-null values
        sample = series.dropna().head(100)
        if len(sample) == 0:
            return False
            
        # Common date patterns
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',                     # YYYY-MM-DD
            r'^\d{4}/\d{2}/\d{2}$',                     # YYYY/MM/DD
            r'^\d{2}-\d{2}-\d{4}$',                     # MM-DD-YYYY
            r'^\d{2}/\d{2}/\d{4}$',                     # MM/DD/YYYY
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',   # YYYY-MM-DD HH:MM:SS
            r'^\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}$'    # YYYY/MM/DD HH:MM:SS
        ]
        
        match_count = 0
        for val in sample:
            str_val = str(val)
            if any(re.match(pattern, str_val) for pattern in date_patterns):
                match_count += 1
                
        # If more than 90% of values match date patterns, consider it a date column
        return match_count / len(sample) > 0.9
        
    return False

def is_date_like_string(value: str) -> bool:
    """Check if a string looks like a date."""
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

def compute_numerical_stats(df: pd.DataFrame, numerical_columns: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Compute statistical metrics for numerical columns.
    
    Args:
        df: DataFrame with the data
        numerical_columns: List of numerical column names
        
    Returns:
        Dictionary mapping column names to their statistics
    """
    stats = {}
    for col in numerical_columns:
        logger.info(f'Identifying numerical range for {col}')
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame")
            stats[col] = {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std": None,
                "percentiles": {}
            }
            continue
        try:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            
            # Only compute statistics if we have enough non-null values
            if numeric_series.count() < 2:
                stats[col] = {
                    "min": None,
                    "max": None,
                    "mean": None,
                    "median": None,
                    "std": None,
                    "percentiles": {}
                }
                continue
                
            # Basic statistics
            col_stats = {
                "min": float(numeric_series.min()),
                "max": float(numeric_series.max()),
                "mean": float(numeric_series.mean()),
                "median": float(numeric_series.median()),
                "std": float(numeric_series.std())
            }
            
            # Percentiles
            percentiles = [0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
            percentile_values = numeric_series.quantile(percentiles)
            col_stats["percentiles"] = {f"p{int(p*100)}": float(percentile_values[p]) for p in percentiles}
            
            stats[col] = col_stats
        except Exception as e:
            logger.warning(f"Error computing numerical stats for {col}: {str(e)}")
            stats[col] = {
                "min": None,
                "max": None,
                "mean": None,
                "median": None,
                "std": None,
                "percentiles": {}
            }
    
    return stats

def compute_data_quality_metrics(df: pd.DataFrame, schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Compute simplified data quality metrics for a table.
    
    Args:
        df: DataFrame containing the data
        schema: Dictionary mapping column names to their data types
        
    Returns:
        Dictionary with data quality metrics for each column
    """
    metrics = {}
    total_rows = len(df)
    
    for col, dtype in schema.items():
        # Skip if column is not in DataFrame
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame")
            metrics[col] = {
                "completeness": 0,
                "uniqueness": 0,
                "common_issues": ["Column not found in sample data"],
                "recommendations": ["Verify column exists in table"],
                "data_type": dtype
            }
            continue
            
        metrics[col] = {
            "completeness": round(df[col].notnull().mean() * 100, 2),
            "uniqueness": round((df[col].nunique() / total_rows * 100), 2),
            "common_issues": [],
            "recommendations": [],
            "data_type": dtype
        }
            
        # Check for common issues
        try:
            # Missing values check
            null_percent = round((1 - df[col].notnull().mean()) * 100, 2)
            if null_percent > 5:
                metrics[col]["common_issues"].append(f"High missing values ({null_percent}%)")
                metrics[col]["recommendations"].append("Investigate source of missing values")
                
            # Unique values check (potential primary key)
            unique_percent = metrics[col]["uniqueness"]
            if unique_percent == 100:
                metrics[col]["common_issues"].append("Potential primary key (100% unique values)")
                
            # Low cardinality check
            if df[col].nunique() <= 5 and total_rows > 100:
                values_str = str(sorted(df[col].dropna().unique().tolist()[:10]))
                metrics[col]["common_issues"].append(f"Low cardinality column with values: {values_str}")
                
            # Detect incorrect data types
            if 'int' in dtype.lower() or 'float' in dtype.lower() or 'double' in dtype.lower() or 'numeric' in dtype.lower():
                # Check if numeric column has string values
                if df[col].dtype == 'object':
                    metrics[col]["common_issues"].append("Potential data type mismatch: numeric column contains non-numeric values")
                    
            # Check for highly skewed distributions in numeric columns
            if df[col].dtype.kind in 'ifc':  # Integer, float, complex
                try:
                    if df[col].dropna().count() > 0:
                        skew = df[col].skew()
                        if abs(skew) > 3:
                            metrics[col]["common_issues"].append(f"Highly skewed distribution (skew={skew:.2f})")
                            metrics[col]["recommendations"].append("Consider transformation for analysis")
                except Exception:
                    pass
                
        except Exception as e:
            logger.warning(f"Error computing data quality metrics for {col}: {str(e)}")
    
    return metrics

def extract_constraints(table_name: str, db_name: str, connection_manager=None) -> Dict[str, Any]:
    """
    Extract database constraints for a table.
    
    Args:
        table_name: Name of the table
        db_name: Database name
        connection_manager: Optional connection manager for user/system connections
        
    Returns:
        Dictionary with constraint information
    """
    # Get database handler using connection manager if available
    if connection_manager and connection_manager.connection_exists(db_name):
        from .database_handlers import get_database_handler
        db = get_database_handler(db_name, connection_manager)
    else:
        from .database_handler import SQLAlchemyHandler  # Import here to avoid circular imports
        db = SQLAlchemyHandler(db_name)
    
    try:
        constraints = {
            'primary_keys': db.get_primary_keys(table_name),
            'foreign_keys': [],  # This will be populated based on database handler capabilities
            'unique_constraints': []  # This will be populated based on database handler capabilities
        }

        # Additional constraint extraction can be added here based on the database type
        
        return constraints
    finally:
        db.close()

# Export functions for use in other modules
__all__ = [
    'identify_column_types',
    'extract_categorical_values',
    'is_date_like',
    'is_date_like_string',
    'compute_numerical_stats',
    'compute_data_quality_metrics',
    'extract_constraints'
] 