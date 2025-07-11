import logging
import pandas as pd
import json
from typing import Dict, Any, List, Tuple, Optional
import random
import time
import concurrent.futures
from datetime import datetime, timedelta
import os
import re

from ..utils.database_handler import SQLAlchemyHandler
from ..config.config import get_llm_api_config, get_db_handler

# Import utility functions
from ..utils.metadata_utils import (
    extract_categorical_values,
    identify_column_types,
    compute_numerical_stats,
    compute_data_quality_metrics,
    extract_constraints,
    is_date_like,
    is_date_like_string
)

# LLM imports
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAIError
from .semantic_models import call_llm_json

logger = logging.getLogger(__name__)

# Global cost tracking
_llm_cost_tracker = {
    "total_tokens": 0,
    "total_cost_usd": 0.0,
    "request_count": 0,
    "max_cost_limit": float(os.environ.get('LLM_MAX_COST_USD', '10.0'))  # Default $10 limit
}

def estimate_llm_cost(prompt: str, model: str = None) -> float:
    """Estimate LLM API cost before making the call."""
    if not model:
        _, _, model = get_llm_api_config()
    
    # Rough token estimation (1 token ≈ 4 characters)
    estimated_tokens = len(prompt) // 4
    
    # Cost per 1K tokens (approximate pricing as of 2024)
    cost_per_1k = {
        'gpt-4': 0.03,
        'gpt-4-turbo': 0.01,
        'gpt-3.5-turbo': 0.002,
        'claude-3-opus': 0.015,
        'claude-3-sonnet': 0.003,
        'claude-3-haiku': 0.0025
    }
    
    # Find matching model price
    price = 0.002  # Default to GPT-3.5 pricing
    for model_name, model_price in cost_per_1k.items():
        if model_name in model.lower():
            price = model_price
            break
    
    return (estimated_tokens / 1000) * price

def check_cost_limit() -> bool:
    """Check if we're approaching cost limits."""
    return _llm_cost_tracker["total_cost_usd"] < _llm_cost_tracker["max_cost_limit"]

@retry(
    retry=retry_if_exception_type(OpenAIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_llm_api(prompt: str, system_message: str = None, temperature: float = 0.2) -> str:
    """
    Call OpenAI API with retry logic and cost tracking
    
    Args:
        prompt: The prompt to send to the API
        system_message: Optional system message
        temperature: Temperature for randomness (0.0 to 1.0)
        
    Returns:
        API response text
    """
    # Check cost limits before making the call
    if not check_cost_limit():
        raise ValueError(f"LLM cost limit exceeded: ${_llm_cost_tracker['total_cost_usd']:.2f} >= ${_llm_cost_tracker['max_cost_limit']:.2f}")
    
    try:
        api_key, base_url, model_name = get_llm_api_config()
        
        # Estimate cost
        estimated_cost = estimate_llm_cost(prompt, model_name)
        logger.info(f"Estimated LLM cost: ${estimated_cost:.4f}")
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=4000,
        )
        
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from LLM API")
        
        # Track actual usage if available
        if hasattr(response, 'usage'):
            actual_tokens = response.usage.total_tokens
            actual_cost = estimate_llm_cost("", model_name) * actual_tokens / 1000
            _llm_cost_tracker["total_tokens"] += actual_tokens
            _llm_cost_tracker["total_cost_usd"] += actual_cost
        else:
            # Fall back to estimate
            _llm_cost_tracker["total_cost_usd"] += estimated_cost
            
        _llm_cost_tracker["request_count"] += 1
        
        logger.info(f"LLM usage - Total cost: ${_llm_cost_tracker['total_cost_usd']:.4f}, Requests: {_llm_cost_tracker['request_count']}")
            
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {str(e)}")
        raise

def get_llm_cost_stats() -> Dict[str, Any]:
    """Get current LLM cost statistics."""
    return _llm_cost_tracker.copy()

def reset_llm_cost_tracker():
    """Reset LLM cost tracking."""
    global _llm_cost_tracker
    _llm_cost_tracker = {
        "total_tokens": 0,
        "total_cost_usd": 0.0,
        "request_count": 0,
        "max_cost_limit": float(os.environ.get('LLM_MAX_COST_USD', '10.0'))
    }

def get_table_info_with_better_sampling(
    table_name: str, 
    db_name: str, 
    schema_name: str = 'public',
    analysis_sql: Optional[str] = None,
    sample_size: int = 100,   # Reduced for faster metadata generation
    num_samples: int = 5,    # Reduced for faster metadata generation
    use_stratified_sampling: bool = True,
    connection_manager=None
) -> Tuple[Dict[str, str], pd.DataFrame]:
    """
    Get table schema and sample data with improved sampling strategies.
    
    Args:
        table_name: Name of the table
        db_name: Database name
        schema_name: Schema name
        analysis_sql: Optional custom SQL query
        sample_size: Size of each sample (increased default)
        num_samples: Number of samples to take (increased default)
        use_stratified_sampling: Use stratified sampling if possible
        connection_manager: Optional connection manager for user/system connections
        
    Returns:
        Tuple with schema dictionary
    """
    # Validate inputs to prevent SQL injection
    if not _validate_sql_identifier(table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    if not _validate_sql_identifier(schema_name):
        raise ValueError(f"Invalid schema name: {schema_name}")
    
    # Get database handler using connection manager if available
    if connection_manager and connection_manager.connection_exists(db_name):
        from ..utils.database_handlers import get_database_handler
        db = get_database_handler(db_name, connection_manager)
    else:
        db = get_db_handler(db_name)
    try:
        # Get schema using database handler
        # For BigQuery, try to get detailed info with column descriptions first
        from ..utils.bigquery_handler import BigQueryHandler
        if isinstance(db, BigQueryHandler):
            try:
                detailed_info = db.get_detailed_table_info(table_name, schema_name)
                schema = {col['name']: col['data_type'] for col in detailed_info.get('columns', [])}
                # Store column descriptions for later use
                column_descriptions = {col['name']: col['comment'] for col in detailed_info.get('columns', []) if col.get('comment')}
                # Store detailed column info for BigQuery-specific attributes
                column_details = {col['name']: col for col in detailed_info.get('columns', [])}
                if not hasattr(get_table_info_with_better_sampling, '_column_descriptions'):
                    get_table_info_with_better_sampling._column_descriptions = {}
                if not hasattr(get_table_info_with_better_sampling, '_column_details'):
                    get_table_info_with_better_sampling._column_details = {}
                get_table_info_with_better_sampling._column_descriptions[f"{db_name}.{table_name}"] = column_descriptions
                get_table_info_with_better_sampling._column_details[f"{db_name}.{table_name}"] = column_details
                logger.debug(f"schema with descriptions: {schema}, descriptions: {column_descriptions}")
            except Exception as e:
                logger.warning(f"Failed to get detailed table info, falling back to basic schema: {e}")
                schema = db.get_table_schema(table_name, schema_name)
                logger.debug(f"schema: {schema}")
        else:
            schema = db.get_table_schema(table_name, schema_name)
            logger.debug(f"schema: {schema}")

        if not schema:
            raise ValueError(f"Table {schema_name}.{table_name} not found or has no columns")

        # Get table indexes
        try:
            indexes = db.get_table_indexes(table_name, schema_name)
            logger.debug(f"indexes: {indexes}")
        except Exception as e:
            logger.warning(f"Could not get indexes: {e}")
            indexes = []

        # Store indexes in global context for later use
        if not hasattr(get_table_info, '_table_indexes'):
            get_table_info._table_indexes = {}
        get_table_info._table_indexes[f"{db_name}.{table_name}"] = indexes

        # Check if this is BigQuery and use partition-aware sampling
        from ..utils.bigquery_handler import BigQueryHandler
        if isinstance(db, BigQueryHandler):
            # Use BigQuery's partition-aware sampling
            sample_data_list = db.get_partition_aware_sample(
                table_name=table_name,
                schema_name=schema_name,
                sample_size=sample_size,
                num_samples=num_samples
            )
            df = pd.DataFrame(sample_data_list)
        else:
            # Improved sampling strategy
            df = _get_improved_sample_data(
                db=db,
                table_name=table_name,
                schema_name=schema_name,
                schema=schema,
                analysis_sql=analysis_sql,
                sample_size=sample_size,
                num_samples=num_samples,
                use_stratified_sampling=use_stratified_sampling
            )
        
        # Validate sample data quality
        if df.empty:
            logger.warning(f"No sample data retrieved for table {table_name}")
        elif len(df) < sample_size * 0.1:  # Less than 10% of expected
            logger.warning(f"Sample data smaller than expected: {len(df)} rows")
        
        return schema, df
    
    finally:
        # Don't close connection - let handler cache manage lifecycle
        # The handler will reuse connections for better performance
        pass

def _validate_sql_identifier(identifier: str) -> bool:
    """Validate SQL identifier to prevent injection attacks."""
    if not identifier or len(identifier) > 128:
        return False
    return re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier) is not None

def _get_improved_sample_data(
    db, 
    table_name: str, 
    schema_name: str, 
    schema: Dict[str, str],
    analysis_sql: Optional[str] = None,
    sample_size: int = 500,
    num_samples: int = 10,
    use_stratified_sampling: bool = True
) -> pd.DataFrame:
    """Get improved sample data with better strategies."""
    
    samples = []
    
    if analysis_sql:
        # Handle custom analysis SQL
        samples.append(_handle_analysis_sql(db, analysis_sql, sample_size, num_samples))
    else:
        # Get row count for sampling strategy
        row_count = db.get_row_count(table_name, schema_name)
        
        if not row_count or row_count == 0:
            logger.warning(f"Table {table_name} appears to be empty")
            return pd.DataFrame()
        
        if row_count <= sample_size * num_samples:
            # Small table - get everything
            table_ref = f'"{schema_name}"."{table_name}"' if schema_name != 'main' else f'"{table_name}"'
            query = f"SELECT * FROM {table_ref} LIMIT {row_count}"
            result = db.fetch_all(query)
            samples.append(pd.DataFrame(result))
        else:
            # Large table - use improved sampling
            if use_stratified_sampling:
                samples.extend(_stratified_sampling(db, table_name, schema_name, schema, sample_size, num_samples))
            else:
                samples.extend(_random_sampling(db, table_name, schema_name, sample_size, num_samples, row_count))
    
    # Combine all samples
    if samples:
        df = pd.concat([s for s in samples if not s.empty], ignore_index=True)
        
        # Handle drop_duplicates with JSON/dict columns that are unhashable
        try:
            return df.drop_duplicates()  # Remove any duplicates
        except TypeError as e:
            if "unhashable type" in str(e):
                logger.warning(f"Skipping duplicate removal due to unhashable column types (likely JSON/dict data): {e}")
                return df  # Return without deduplication
            else:
                raise e
    else:
        return pd.DataFrame()

def _stratified_sampling(db, table_name: str, schema_name: str, schema: Dict[str, str], sample_size: int, num_samples: int) -> List[pd.DataFrame]:
    """Attempt stratified sampling based on likely categorical columns."""
    samples = []
    
    try:
        # Find potential stratification columns (low cardinality)
        strat_columns = []
        for col_name, col_type in schema.items():
            if any(cat_type in col_type.lower() for cat_type in ['varchar', 'char', 'text', 'enum', 'boolean']):
                strat_columns.append(col_name)
        
        if strat_columns:
            # Try stratified sampling on the first categorical column
            strat_col = strat_columns[0]
            table_ref = f'"{schema_name}"."{table_name}"' if schema_name != 'main' else f'"{table_name}"'
            
            # Get distinct values for stratification
            distinct_query = f'SELECT DISTINCT "{strat_col}" FROM {table_ref} WHERE "{strat_col}" IS NOT NULL LIMIT 20'
            distinct_values = db.fetch_all(distinct_query)
            
            if len(distinct_values) <= 10:  # Good for stratification
                # Sample from each stratum
                per_stratum = max(1, sample_size // len(distinct_values))
                
                for value_row in distinct_values:
                    value = value_row[strat_col]
                    stratum_query = f'SELECT * FROM {table_ref} WHERE "{strat_col}" = :strat_value LIMIT {per_stratum}'
                    stratum_result = db.fetch_all(stratum_query, {"strat_value": value})
                    if stratum_result:
                        samples.append(pd.DataFrame(stratum_result))
                        
                logger.info(f"Used stratified sampling on column {strat_col}")
            else:
                # Fall back to random sampling
                samples.extend(_random_sampling(db, table_name, schema_name, sample_size, num_samples))
        else:
            # No good stratification columns - use random sampling
            samples.extend(_random_sampling(db, table_name, schema_name, sample_size, num_samples))
            
    except Exception as e:
        logger.warning(f"Stratified sampling failed: {e}, falling back to random sampling")
        samples.extend(_random_sampling(db, table_name, schema_name, sample_size, num_samples))
    
    return samples

def _random_sampling(db, table_name: str, schema_name: str, sample_size: int, num_samples: int, row_count: int = None) -> List[pd.DataFrame]:
    """Random sampling with multiple offsets."""
    samples = []
    
    if not row_count:
        row_count = db.get_row_count(table_name, schema_name)
    
    max_offset = max(0, row_count - sample_size)
    offsets = random.sample(range(max_offset), min(num_samples, max_offset)) if max_offset > 0 else [0]
    
    table_ref = f'"{schema_name}"."{table_name}"' if schema_name != 'main' else f'"{table_name}"'
    
    for offset in offsets:
        query = f"SELECT * FROM {table_ref} LIMIT {sample_size} OFFSET {offset}"
        result = db.fetch_all(query)
        if result:
            samples.append(pd.DataFrame(result))
    
    return samples

def _handle_analysis_sql(db, analysis_sql: str, sample_size: int, num_samples: int) -> pd.DataFrame:
    """Handle custom analysis SQL with safety checks."""
    # Check if analysis_sql already contains LIMIT
    has_limit = 'LIMIT' in analysis_sql.upper()
    
    if not has_limit and sample_size > 0 and num_samples > 0:
        logger.info(f"Applying sampling to analysis SQL: size={sample_size}, samples={num_samples}")
        
        # Check query cost before executing
        is_safe, reason = db.check_query_cost(analysis_sql, "", "")
        if not is_safe:
            logger.warning(f"Query cost analysis warning: {reason}")
            raise ValueError(f"Query would be too costly to execute: {reason}")
        
        # Get total count for offset calculation
        count_sql = f"SELECT COUNT(*) as count FROM ({analysis_sql}) AS analysis_query"
        count_result = db.fetch_one(count_sql)
        total_count = int(count_result['count']) if count_result else 0
        
        if total_count > 0:
            if total_count <= sample_size * num_samples:
                # If total count is small, just get everything
                query = f"{analysis_sql} LIMIT {total_count}"
                result = db.fetch_all(query)
                return pd.DataFrame(result)
            else:
                # Random sampling using different offsets
                max_offset = total_count - sample_size
                offsets = random.sample(range(max_offset), min(num_samples, max_offset))
                
                samples = []
                for offset in offsets:
                    query = f"{analysis_sql} LIMIT {sample_size} OFFSET {offset}"
                    result = db.fetch_all(query)
                    if result:
                        samples.append(pd.DataFrame(result))
                
                return pd.concat(samples, ignore_index=True) if samples else pd.DataFrame()
        else:
            return pd.DataFrame()
    else:
        # Analysis SQL already has LIMIT or sampling is disabled
        result = db.fetch_all(analysis_sql)
        return pd.DataFrame(result)

def is_self_explanatory_column(column_name: str, data_type: str) -> bool:
    """
    Determine if a column is self-explanatory and doesn't need enhanced description.
    
    Args:
        column_name: Name of the column
        data_type: Data type of the column
        
    Returns:
        True if column is self-explanatory, False otherwise
    """
    # Common self-explanatory patterns
    self_explanatory_patterns = [
        # Standard ID columns
        r'^id$', r'^.*_id$', r'^.*_key$', r'^key$',
        # Common timestamp columns
        r'^created_at$', r'^updated_at$', r'^deleted_at$', r'^timestamp$',
        r'^created_time$', r'^updated_time$', r'^modified_time$',
        # Common status/flag columns
        r'^status$', r'^is_.*$', r'^has_.*$', r'^flag$', r'^.*_flag$',
        # Common count/number columns
        r'^count$', r'^.*_count$', r'^num_.*$', r'^number$', r'^.*_number$',
        # Common name/title columns
        r'^name$', r'^title$', r'^description$', r'^.*_name$', r'^.*_title$',
        # Common date/time columns
        r'^date$', r'^time$', r'^.*_date$', r'^.*_time$',
        # Version/sequence columns
        r'^version$', r'^sequence$', r'^.*_version$', r'^.*_sequence$'
    ]
    
    import re
    column_lower = column_name.lower()
    
    for pattern in self_explanatory_patterns:
        if re.match(pattern, column_lower):
            return True
    
    return False

def needs_description_enhancement(column_name: str, existing_description: str = None) -> bool:
    """
    Determine if a column needs description enhancement based on existing description quality.
    
    Args:
        column_name: Name of the column
        existing_description: Existing description if available
        
    Returns:
        True if needs enhancement, False if existing description is sufficient
    """
    if not existing_description:
        return not is_self_explanatory_column(column_name, "")
    
    # Check if existing description is too generic or low quality
    generic_indicators = [
        'column', 'field', 'data', 'value', 'information',
        'stores', 'contains', 'holds', 'represents'
    ]
    
    description_lower = existing_description.lower()
    
    # If description is too short (likely auto-generated)
    if len(existing_description.strip()) < 20:
        return True
    
    # If description is mostly generic terms
    generic_count = sum(1 for term in generic_indicators if term in description_lower)
    if generic_count >= 2:
        return True
    
    # If description just repeats column name
    column_words = set(column_name.lower().replace('_', ' ').split())
    desc_words = set(description_lower.replace('_', ' ').split())
    if len(column_words.intersection(desc_words)) >= len(column_words):
        return True
    
    return False

def generate_column_definitions(
    schema: Dict[str, str],
    categorical_values: Dict[str, List[Any]],
    db_name: str,
    table_name: str,
    schema_name: str,
    numerical_stats: Dict[str, Dict[str, float]],
    constraints: Dict[str, Any],
    partition_info: Dict[str, Any] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Generate intelligent column definitions using LLM only when valuable.
    
    Args:
        schema: Dictionary mapping column names to data types
        categorical_values: Dictionary mapping column names to unique values
        db_name: Database name
        table_name: Table name
        schema_name: Schema name
        numerical_stats: Dictionary with numerical statistics
        constraints: Table constraints
        partition_info: Partition information
        
    Returns:
        Dictionary with column definitions
    """
    column_definitions = {}
    
    # Get existing column descriptions and detailed info if available (from BigQuery)
    column_descriptions = {}
    column_details = {}
    if hasattr(get_table_info_with_better_sampling, '_column_descriptions'):
        column_descriptions = get_table_info_with_better_sampling._column_descriptions.get(f"{db_name}.{table_name}", {})
    if hasattr(get_table_info_with_better_sampling, '_column_details'):
        column_details = get_table_info_with_better_sampling._column_details.get(f"{db_name}.{table_name}", {})
    
    # Get partition information
    partition_info = partition_info or {}
    partition_column = partition_info.get('partition_column')
    clustering_fields = partition_info.get('clustering_fields', [])
    
    # Categorize columns by processing need
    columns_to_enhance = []
    columns_use_as_is = []
    columns_basic_info = []
    
    for column_name, data_type in schema.items():
        existing_desc = column_descriptions.get(column_name, "")
        
        if existing_desc and not needs_description_enhancement(column_name, existing_desc):
            # Use BigQuery description as-is
            columns_use_as_is.append(column_name)
        elif is_self_explanatory_column(column_name, data_type):
            # Generate basic info only
            columns_basic_info.append(column_name)
        else:
            # Needs LLM enhancement
            columns_to_enhance.append(column_name)
    
    logger.info(f"Column processing strategy: {len(columns_use_as_is)} as-is, {len(columns_basic_info)} basic, {len(columns_to_enhance)} enhanced")
    
    # Process columns that use existing descriptions as-is
    for column_name in columns_use_as_is:
        existing_desc = column_descriptions[column_name]
        column_definitions[column_name] = {
            "definition": existing_desc,
            "business_name": column_name.replace('_', ' ').title(),
            "purpose": existing_desc,
            "format": "Standard format",
            "business_rules": [],
            "source": "bigquery_schema"
        }
    
    # Process self-explanatory columns with basic info
    for column_name in columns_basic_info:
        data_type = schema[column_name]
        
        # Generate basic description based on column name pattern
        if column_name.endswith('_id') or column_name == 'id':
            basic_desc = f"Unique identifier for {column_name.replace('_id', '').replace('_', ' ')}"
        elif column_name.startswith('is_') or column_name.startswith('has_'):
            basic_desc = f"Boolean flag indicating {column_name.replace('_', ' ')}"
        elif column_name.endswith('_date') or column_name.endswith('_time'):
            basic_desc = f"Date/time when {column_name.replace('_date', '').replace('_time', '').replace('_', ' ')}"
        elif column_name.endswith('_count') or column_name.startswith('num_'):
            basic_desc = f"Count of {column_name.replace('_count', '').replace('num_', '').replace('_', ' ')}"
        else:
            basic_desc = f"The {column_name.replace('_', ' ')} value"
        
        column_definitions[column_name] = {
            "definition": basic_desc,
            "business_name": column_name.replace('_', ' ').title(),
            "purpose": basic_desc,
            "format": "Standard format",
            "business_rules": [],
            "source": "pattern_based"
        }
    
    # Only call LLM for columns that need enhancement
    if columns_to_enhance:
        enhanced_definitions = generate_enhanced_column_definitions(
            columns_to_enhance, schema, categorical_values, db_name, table_name, 
            schema_name, numerical_stats, constraints, partition_info, 
            column_descriptions, column_details
        )
        column_definitions.update(enhanced_definitions)
    
    return column_definitions

def generate_enhanced_column_definitions(
    columns_to_enhance: List[str],
    schema: Dict[str, str],
    categorical_values: Dict[str, List[Any]],
    db_name: str,
    table_name: str,
    schema_name: str,
    numerical_stats: Dict[str, Dict[str, float]],
    constraints: Dict[str, Any],
    partition_info: Dict[str, Any],
    column_descriptions: Dict[str, str],
    column_details: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Generate enhanced column definitions using LLM for columns that need it.
    """
    if not columns_to_enhance:
        return {}
    
    # Get partition information
    partition_column = partition_info.get('partition_column')
    clustering_fields = partition_info.get('clustering_fields', [])
    
    # Build focused prompt for columns that need enhancement
    prompt = f"""### Task
Generate meaningful business definitions for specific columns that need enhancement.

### Database Context
Database: {db_name}
Schema: {schema_name}
Table: {table_name}

### Columns Requiring Enhancement
The following columns need meaningful business definitions:

"""

    # Add information only for columns that need enhancement
    for column_name in columns_to_enhance:
        data_type = schema[column_name]
        prompt += f"\n## Column: {column_name}\n"
        prompt += f"Data Type: {data_type}\n"
        
        # Add existing column description if available
        if column_name in column_descriptions and column_descriptions[column_name]:
            prompt += f"Existing Description: {column_descriptions[column_name]}\n"
        
        # Add BigQuery-specific column info if available
        if column_name in column_details:
            col_detail = column_details[column_name]
            is_nullable = col_detail.get('is_nullable', True)
            prompt += f"Column Mode: {'NULLABLE' if is_nullable else 'REQUIRED'}\n"
            if col_detail.get('numeric_precision'):
                prompt += f"Numeric Precision: {col_detail['numeric_precision']}\n"
            if col_detail.get('numeric_scale'):
                prompt += f"Numeric Scale: {col_detail['numeric_scale']}\n"
        
        # Add constraints information
        is_primary = column_name in constraints.get('primary_keys', [])
        prompt += f"Primary Key: {'Yes' if is_primary else 'No'}\n"
        
        # Add partition/clustering information
        if partition_column == column_name:
            prompt += f"Partition Column: Yes (Table is partitioned by this column)\n"
        if column_name in clustering_fields:
            prompt += f"Clustering Field: Yes (Table is clustered by this column)\n"
        
        # Add sample values for categorical columns
        if column_name in categorical_values:
            sample_vals = categorical_values[column_name]
            # Format sample values nicely
            sample_str = ", ".join([str(v) for v in sample_vals[:10]])
            if len(sample_vals) > 10:
                sample_str += f", ... (and {len(sample_vals) - 10} more values)"
            prompt += f"Sample Values: {sample_str}\n"
            
        # Add statistics for numerical columns
        if column_name in numerical_stats:
            stats = numerical_stats[column_name]
            if stats['min'] is not None:
                prompt += f"Min: {stats['min']}, Max: {stats['max']}, Mean: {stats['mean']}, Median: {stats['median']}\n"
    
    prompt += """
### Instructions
Focus on providing meaningful, value-added business definitions for these columns.

**Guidelines:**
1. If an "Existing Description" is provided and it's comprehensive, use it as-is by copying it to the "definition" field
2. Only enhance descriptions that are generic, incomplete, or lack business context
3. Provide concise, actionable business definitions that add real value
4. Avoid redundant information that's already obvious from the column name
5. Focus on business context, usage patterns, and domain-specific meaning

**For each column, provide:**
- **definition**: Clear business definition (enhance only if existing is insufficient)
- **purpose**: What the column is used for in business processes
- **format**: Expected format and value patterns
- **business_rules**: Important business rules or constraints
- **data_quality_checks**: Specific quality checks relevant to this column

Format your response as a structured JSON with column names as keys, like this:
{
  "column_name": {
    "definition": "Business definition here",
    "business_name": "Human-readable name (max 3 words)",
    "purpose": "Purpose here",
    "format": "Expected format",
    "business_rules": ["rule 1", "rule 2"],
    "data_quality_checks": ["check 1", "check 2"],
    "source": "llm_enhanced"
  },
  ...
}

Ensure the output is valid JSON that can be parsed programmatically.
"""

    # Call LLM API
    try:
        system_message = "You are an expert database analyst who specializes in creating clear and accurate metadata documentation. Focus on providing meaningful, value-added descriptions that enhance understanding without redundancy."
        response = call_llm_api(prompt, system_message)
        
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            json_str = response[json_start:json_end + 1]
            enhanced_definitions = json.loads(json_str)
            
            # Add source information
            for col_name, col_def in enhanced_definitions.items():
                col_def['source'] = 'llm_enhanced'
            
            return enhanced_definitions
        else:
            logger.error("Failed to extract JSON from LLM response")
            return {}
            
    except Exception as e:
        logger.error(f"Error generating enhanced column definitions: {str(e)}")
        return {}

def generate_smart_categorical_definitions(
    metadata: Dict[str, Any],
    categorical_values: Dict[str, List[Any]],
    max_unique_values: int = 20,
    min_value_length: int = 1,
    client: Any = None,
    model: str = None
) -> Dict[str, Dict[str, str]]:
    """
    Intelligently generates definitions for categorical values if they meet certain criteria.
    
    Args:
        metadata: Existing metadata dictionary
        categorical_values: Dictionary mapping column names to their unique values
        max_unique_values: Maximum number of unique values to consider for definition generation
        min_value_length: Minimum length of value string to consider for definition
        client: OpenAI client instance
        model: Model name to use
    
    Returns:
        Dictionary mapping column names to their value definitions
    """
    # Get API config if not provided
    if client is None or model is None:
        api_key, base_url, model_name = get_llm_api_config()
        model = model or model_name
        client = OpenAI(base_url=base_url, api_key=api_key)

    categorical_definitions = {}
    
    for column, values in categorical_values.items():
        # Skip if too many unique values
        if len(values) > max_unique_values:
            logger.info(f"Skipping {column}: too many unique values ({len(values)} > {max_unique_values})")
            continue
            
        # Filter values that are meaningful enough for definition
        meaningful_values = [
            str(val) for val in values 
            if isinstance(val, (str, int, float)) and 
            len(str(val)) >= min_value_length and
            not str(val).isdigit() and  # Skip pure numbers
            not any(c.isdigit() for c in str(val)) and  # Skip values containing numbers
            not is_date_like_string(str(val))  # Skip date-like values
        ]
        
        if not meaningful_values:
            logger.info(f"Skipping {column}: no meaningful values found")
            continue
            
        # Get column context from metadata
        column_info = metadata.get('columns', {}).get(column, {})
        column_description = column_info.get('description', '')
        
        # Create prompt for definition generation
        prompt = f"""Analyze these categorical values for the column '{column}' and provide concise definitions 
        only if the values represent meaningful categories or states that benefit from explanation.
        
        Column Name: {column}
        Column Description: {column_description}
        Values: {meaningful_values}
        
        Rules:
        1. Only define values that represent meaningful categories or states
        2. Skip obvious numerical or date values
        3. Keep definitions concise (max 15 words)
        4. Skip values that are self-explanatory
        5. Focus on business or domain-specific terminology
        
        Return the definitions in this JSON format:
        {{
            "{column}": {{
                "value1": "definition1",
                "value2": "definition2"
            }}
        }}
        
        Only include values that truly need definition. If no values need definition, return an empty object.
        """
        
        try:
            response = call_llm_json(client, model, prompt)
            
            if response and column in response and response[column]:
                categorical_definitions[column] = response[column]
                logger.info(f"Generated {len(response[column])} definitions for {column}")
            else:
                logger.info(f"No definitions generated for {column}")
                
        except Exception as e:
            logger.error(f"Error generating definitions for {column}: {e}")
            continue
    
    return categorical_definitions

def generate_categorical_definitions(
    categorical_values: Dict[str, List[Any]],
    column_definitions: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, str]]:
    """
    Generate definitions for categorical values using LLM
    
    Args:
        categorical_values: Dictionary mapping column names to unique values
        column_definitions: Dictionary with column definitions
        
    Returns:
        Dictionary with categorical value definitions
    """
    categorical_definitions = {}
    
    # Process each categorical column
    for column_name, values in categorical_values.items():
        # Skip if too many values or empty
        if len(values) > 20 or len(values) == 0:
            continue
            
        # Get column definition if available
        column_def = ""
        if column_name in column_definitions:
            column_def = column_definitions[column_name].get('definition', '')
            
        # Build the prompt
        prompt = f"""### Task
Generate accurate business definitions for each unique value in the categorical column.

### Column Information
Column Name: {column_name}
Column Definition: {column_def}
Unique Values: {', '.join([str(v) for v in values])}

### Instructions
For each unique value, provide a concise definition explaining what this value represents in business terms.
Format your response as a structured JSON with values as keys, like this:
{{
  "value1": "Definition of value1",
  "value2": "Definition of value2",
  ...
}}

Ensure the output is valid JSON that can be parsed programmatically.
"""

        # Call LLM API
        try:
            system_message = "You are an expert data analyst who specializes in creating clear and accurate metadata documentation."
            response = call_llm_api(prompt, system_message)
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end + 1]
                value_definitions = json.loads(json_str)
                categorical_definitions[column_name] = value_definitions
            else:
                logger.error(f"Failed to extract JSON from LLM response for column {column_name}")
                
        except Exception as e:
            logger.error(f"Error generating categorical definitions for {column_name}: {str(e)}")
            
    return categorical_definitions

def generate_enhanced_table_insights(
    db_name: str,
    schema_name: str,
    table_name: str,
    schema: Dict[str, str],
    sample_data: pd.DataFrame,
    constraints: Dict[str, Any],
    column_definitions: Dict[str, Dict[str, Any]],
    include_relationships: bool = True,
    include_business_rules: bool = True,
    include_additional_insights: bool = True,
    include_query_examples: bool = True,
    include_aggregation_rules: bool = True,
    include_query_rules: bool = True
) -> Dict[str, Any]:
    """
    Generate enhanced table-level insights using LLM with optional sections.
    
    Args:
        db_name: Database name
        schema_name: Schema name
        table_name: Table name
        schema: Dictionary mapping column names to data types
        sample_data: DataFrame with sample data
        constraints: Table constraints
        column_definitions: Dictionary with column definitions
        include_relationships: Whether to generate relationship analysis
        include_business_rules: Whether to generate business rules
        include_additional_insights: Whether to generate additional insights
        include_query_examples: Whether to generate example queries
        include_aggregation_rules: Whether to generate aggregation rules
        include_query_rules: Whether to generate query rules
        
    Returns:
        Dictionary with table insights
    """
    # Convert sample data to string representation
    sample_rows = sample_data.head(2).to_dict(orient='records')
    sample_data_str = json.dumps(sample_rows, indent=2, default=str)
    
    # Build the comprehensive prompt
    prompt = f"""### Task
Provide a comprehensive analysis of this database table including domain classification, business context, and operational insights.

### Database Context
Database: {db_name}
Schema: {schema_name}
Table: {table_name}

### Table Information
Columns:
{json.dumps(schema, indent=2)}

Primary Keys:
{', '.join(constraints.get('primary_keys', ['None']))}

Sample Data:
{sample_data_str}

### Column Definitions
{json.dumps(column_definitions, indent=2)}

### Instructions
Analyze the table comprehensively and provide structured insights covering business context, operational aspects, and technical recommendations.

Required sections:
1. Domain classification (e.g., "Geospatial & Location", "Data Analytics", "User Management", "Financial", "Product Catalog", etc.)
2. Category classification (e.g., "Master Data", "Transactional Data", "Reference Data", "Configuration Data", etc.)
3. Comprehensive description in Markdown format with business context and technical details
4. Clear business purpose statement
5. Common usage patterns and use cases
6. Data lifecycle considerations including update frequency, retention, and archival strategies
"""

    # Add optional sections to the prompt based on parameters
    optional_sections = []
    
    if include_relationships:
        optional_sections.append("7. Potential relationships with other tables")
    
    if include_business_rules:
        optional_sections.append("8. Recommended business rules and data quality validations")
    
    if include_aggregation_rules:
        optional_sections.append("9. Suggested aggregation rules for analytics and reporting")
    
    if include_query_rules:
        optional_sections.append("10. Query optimization rules and performance recommendations")
    
    if include_query_examples:
        optional_sections.append("11. Example SQL queries for common use cases")
    
    if include_additional_insights:
        optional_sections.append("12. Additional domain-specific insights and recommendations")
    
    # Add optional sections to prompt
    if optional_sections:
        prompt += "\n\nOptional sections (include if relevant):\n" + "\n".join(optional_sections)
    
    # Build the comprehensive JSON response format
    json_structure = {
        "table_insights": {
            "domain": "Domain of the table (e.g., 'Geospatial & Location', 'Data Analytics', 'User Management')",
            "category": "Category of the table ",
            "description": "high level description in Markdown format",
            "purpose": "Clear statement of the table's business purpose and function",
            "usage_patterns": [
                "Common usage pattern 1",
                "Common usage pattern 2",
                "Common usage pattern 3"
            ],
            "data_lifecycle": {
                "update_frequency": "How often the data is updated (e.g., 'Real-time', 'Daily', 'Weekly', 'On-demand')",
                "retention_policy": "Data retention policy and duration (e.g., '7 years', 'Indefinite', '90 days')",
                "archival_strategy": "Data archival strategy and considerations"
            }
        }
    }
    
    # Add optional sections to JSON structure
    if include_relationships:
        json_structure["potential_relationships"] = [
            {
                "column": "column_name",
                "relates_to": "likely related table",
                "relationship_type": "one-to-many/many-to-one/many-to-many",
                "description": "description of relationship and business logic"
            }
        ]
    
    if include_business_rules:
        json_structure["business_rules"] = {
            "data_quality_rules": [
                "Data quality rule 1",
                "Data quality rule 2"
            ],
            "business_constraints": [
                "Business constraint 1",
                "Business constraint 2"
            ],
            "validation_recommendations": [
                "Validation recommendation 1",
                "Validation recommendation 2"
            ]
        }
    
    if include_aggregation_rules:
        json_structure["aggregation_rules"] = [
            {
                "rule_name": "aggregation rule name",
                "description": "what this aggregation represents",
                "sql_pattern": "SQL pattern for aggregation",
                "use_case": "when to use this aggregation",
                "business_value": "business value provided"
            }
        ]
    
    if include_query_rules:
        json_structure["performance_optimization"] = {
            "indexing_recommendations": [
                "Index recommendation 1",
                "Index recommendation 2"
            ],
            "query_patterns": [
                "Optimal query pattern 1",
                "Optimal query pattern 2"
            ],
            "performance_considerations": [
                "Performance consideration 1",
                "Performance consideration 2"
            ]
        }
    
    if include_query_examples:
        json_structure["query_examples"] = [
            {
                "name": "example query name",
                "description": "what this query accomplishes",
                "sql": "SELECT example SQL query",
                "use_case": "business use case for this query",
                "frequency": "how often this query might be run"
            }
        ]
    
    if include_additional_insights:
        json_structure["additional_insights"] = {
            "data_patterns": "Observed data patterns and characteristics",
            "domain_specific_notes": "Domain-specific observations and recommendations",
            "integration_considerations": "Integration and interoperability considerations",
            "governance_notes": "Data governance and compliance considerations"
        }
    
    prompt += f"""

### Response Format
Provide your analysis as a structured JSON response following this exact format:

{json.dumps(json_structure, indent=2)}

### Important Guidelines
1. Ensure all text fields are properly formatted and professional
2. Use Markdown formatting in the description field for better readability
3. Be specific and actionable in recommendations
4. Consider the business context when classifying domain and category
5. Ensure the output is valid JSON that can be parsed programmatically
6. Base insights on the actual data structure and sample data provided

Ensure the output is valid JSON that can be parsed programmatically.
"""

    # Call LLM API
    try:
        system_message = "You are an expert data architect and business analyst who specializes in understanding database schemas, their business implications, and operational requirements. You provide comprehensive, actionable insights about data structures."
        response = call_llm_api(prompt, system_message)
        
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            json_str = response[json_start:json_end + 1]
            table_insights = json.loads(json_str)
            return table_insights
        else:
            logger.error("Failed to extract JSON from LLM response for enhanced table insights")
            return {}
            
    except Exception as e:
        logger.error(f"Error generating enhanced table insights: {str(e)}")
        # Return meaningful fallback with new structure
        return {
            "table_insights": {
                "domain": "Business Data",
                "category": "Data Table", 
                "description": f"**{table_name.replace('_', ' ').title()}**\n\nData storage table for {table_name.replace('_', ' ')} information in the {schema_name} schema.",
                "purpose": f"To store and manage {table_name.replace('_', ' ')} data for business operations.",
                "usage_patterns": [
                    "Data storage and retrieval",
                    "Analytics and reporting",
                    "Application data management"
                ],
                "data_lifecycle": {
                    "update_frequency": "Unknown",
                    "retention_policy": "Not specified",
                    "archival_strategy": "Not defined"
                }
            }
        }

def generate_table_insights(
    db_name: str,
    schema_name: str,
    table_name: str,
    schema: Dict[str, str],
    sample_data: pd.DataFrame,
    constraints: Dict[str, Any],
    column_definitions: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate table-level insights using LLM (original function for backward compatibility)
    
    Args:
        db_name: Database name
        schema_name: Schema name
        table_name: Table name
        schema: Dictionary mapping column names to data types
        sample_data: DataFrame with sample data
        constraints: Table constraints
        column_definitions: Dictionary with column definitions
        
    Returns:
        Dictionary with table insights
    """
    return generate_enhanced_table_insights(
        db_name=db_name,
        schema_name=schema_name,
        table_name=table_name,
        schema=schema,
        sample_data=sample_data,
        constraints=constraints,
        column_definitions=column_definitions,
        include_relationships=True,
        include_business_rules=True,
        include_additional_insights=True,
        include_query_examples=True,
        include_aggregation_rules=True,
        include_query_rules=True
    )

def generate_complete_table_metadata(
    db_name: str,
    table_name: str,
    schema_name: str = 'public',
    analysis_sql: Optional[str] = None,
    sample_size: int = 100,
    num_samples: int = 5,
    connection_manager=None,  # Add connection manager parameter
    # Optional sections - can be disabled to save time/cost
    include_relationships: bool = True,
    include_aggregation_rules: bool = True,
    include_query_rules: bool = True,
    include_data_quality: bool = True,
    include_query_examples: bool = True,
    include_additional_insights: bool = True,
    include_business_rules: bool = True,
    include_categorical_definitions: bool = True
) -> Dict[str, Any]:
    """
    Generate complete table metadata including column classifications, statistics,
    definitions, and insights.
    
    Args:
        db_name: Database name
        table_name: Table name
        schema_name: Schema name
        analysis_sql: Optional custom SQL query
        sample_size: Size of each sample
        num_samples: Number of samples to take
        connection_manager: Optional connection manager for user/system connections
        include_relationships: Whether to generate relationship analysis
        include_aggregation_rules: Whether to generate aggregation rules
        include_query_rules: Whether to generate query rules
        include_data_quality: Whether to compute data quality metrics
        include_query_examples: Whether to generate example queries
        include_additional_insights: Whether to generate additional insights
        include_business_rules: Whether to generate business rules
        include_categorical_definitions: Whether to generate categorical value definitions
        
    Returns:
        Dictionary with complete table metadata
    """
    start_time = time.time()
    processing_stats = {
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "optional_sections": {
            "relationships": include_relationships,
            "aggregation_rules": include_aggregation_rules,
            "query_rules": include_query_rules,
            "data_quality": include_data_quality,
            "query_examples": include_query_examples,
            "additional_insights": include_additional_insights,
            "business_rules": include_business_rules,
            "categorical_definitions": include_categorical_definitions
        }
    }
    
    try:
        # Step 1: Get table schema and sample data
        step_start = time.time()
        schema, sample_data = get_table_info_with_better_sampling(
            table_name=table_name,
            db_name=db_name,
            schema_name=schema_name,
            analysis_sql=analysis_sql,
            sample_size=sample_size,
            num_samples=num_samples,
            connection_manager=connection_manager
        )
        processing_stats["steps"].append({
            "step": "get_table_info",
            "duration_seconds": time.time() - step_start,
            "rows_processed": len(sample_data),
            "columns_processed": len(schema)
        })
        
        # Step 2: Identify column types (categorical vs numerical)
        step_start = time.time()
        categorical_columns, numerical_columns = identify_column_types(schema, sample_data)
        processing_stats["steps"].append({
            "step": "identify_column_types",
            "duration_seconds": time.time() - step_start,
            "categorical_columns": len(categorical_columns),
            "numerical_columns": len(numerical_columns)
        })
        
        # Create a list of tasks to run in parallel
        tasks = []
        
        # Step 3: Extract database constraints (always needed)
        tasks.append(("extract_constraints", lambda: extract_constraints(table_name, db_name, connection_manager=connection_manager)))
        
        # Step 4: Compute numerical statistics (always needed for basic metadata)
        tasks.append(("compute_numerical_stats", lambda: compute_numerical_stats(sample_data, numerical_columns)))
        
        # Step 5: Compute data quality metrics (optional)
        if include_data_quality:
            tasks.append(("compute_data_quality_metrics", lambda: compute_data_quality_metrics(sample_data, schema)))
        
        # Step 6: Extract categorical values (needed for categorical definitions)
        if include_categorical_definitions:
            tasks.append(("extract_categorical_values", lambda: extract_categorical_values(
                sample_data, categorical_columns, db_name, schema_name, table_name, connection_manager=connection_manager)))
        
        # Run tasks in parallel
        step_start = time.time()
        results = {}
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Submit all tasks and store futures with their names
                future_to_task = []
                for task_name, task_func in tasks:
                    future = executor.submit(task_func)
                    future_to_task.append((future, task_name))
                
                # Collect results as they complete
                for future, task_name in future_to_task:
                    try:
                        results[task_name] = future.result()
                    except Exception as e:
                        logger.error(f"Error in task {task_name}: {str(e)}")
                        results[task_name] = {}
        except Exception as e:
            logger.error(f"Error in parallel processing: {str(e)}")
            # Fall back to sequential processing
            for task_name, task_func in tasks:
                try:
                    results[task_name] = task_func()
                except Exception as e:
                    logger.error(f"Error in sequential task {task_name}: {str(e)}")
                    results[task_name] = {}
        
        # Extract results
        constraints = results.get("extract_constraints", {})
        numerical_stats = results.get("compute_numerical_stats", {})
        data_quality = results.get("compute_data_quality_metrics", {}) if include_data_quality else {}
        categorical_values = results.get("extract_categorical_values", {}) if include_categorical_definitions else {}
        
        processing_stats["steps"].append({
            "step": "parallel_processing",
            "duration_seconds": time.time() - step_start,
            "tasks_completed": len(results)
        })
        
        # Step 7: Generate column definitions using LLM
        step_start = time.time()
        try:
            column_definitions = generate_column_definitions(
                schema=schema,
                categorical_values=categorical_values,
                db_name=db_name,
                table_name=table_name,
                schema_name=schema_name,
                numerical_stats=numerical_stats,
                constraints=constraints,
                partition_info=partition_info
            )
        except Exception as e:
            logger.warning(f"Failed to generate column definitions via LLM: {str(e)}")
            # Create basic column definitions
            column_definitions = {
                col_name: {
                    "definition": f"Column {col_name} of type {data_type}",
                    "business_name": col_name.replace('_', ' ').title(),
                    "purpose": f"Data field for {col_name}",
                    "format": "Standard format",
                    "business_rules": [],
                    "source": "fallback"
                } for col_name, data_type in schema.items()
            }
        
        processing_stats["steps"].append({
            "step": "generate_column_definitions",
            "duration_seconds": time.time() - step_start,
            "columns_processed": len(column_definitions)
        })
        
        # Step 8: Generate categorical value definitions using LLM (optional)
        categorical_definitions = {}
        if include_categorical_definitions:
            step_start = time.time()
            categorical_definitions = generate_smart_categorical_definitions(
                metadata={
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "columns": column_definitions
                },
                categorical_values=categorical_values
            )
            logger.info(f"Categorical definitions: {categorical_definitions}")
            processing_stats["steps"].append({
                "step": "generate_categorical_definitions",
                "duration_seconds": time.time() - step_start,
                "columns_processed": len(categorical_definitions)
            })
        
        # Step 9: Generate table-level insights using LLM (always generate basic summary, optionally include advanced sections)
        step_start = time.time()
        try:
            table_insights = generate_enhanced_table_insights(
                db_name=db_name,
                schema_name=schema_name,
                table_name=table_name,
                schema=schema,
                sample_data=sample_data,
                constraints=constraints,
                column_definitions=column_definitions,
                include_relationships=include_relationships,
                include_business_rules=include_business_rules,
                include_additional_insights=include_additional_insights,
                include_query_examples=include_query_examples,
                include_aggregation_rules=include_aggregation_rules,
                include_query_rules=include_query_rules
            )
        except Exception as e:
            logger.warning(f"Failed to generate table insights via LLM: {str(e)}")
            # Create basic insights as fallback
            table_insights = {
                "table_insights": {
                    "domain": "Business Data",
                    "category": "Data Table", 
                    "description": f"**{table_name.replace('_', ' ').title()}**\n\nData storage table for {table_name.replace('_', ' ')} information in the {schema_name} schema.",
                    "purpose": f"To store and manage {table_name.replace('_', ' ')} data for business operations.",
                    "usage_patterns": [
                        "Data storage and retrieval",
                        "Analytics and reporting",
                        "Application data management"
                    ],
                    "data_lifecycle": {
                        "update_frequency": "Unknown",
                        "retention_policy": "Not specified",
                        "archival_strategy": "Not defined"
                    }
                }
            }
        
        processing_stats["steps"].append({
            "step": "generate_table_insights",
            "duration_seconds": time.time() - step_start
        })
        
        # Step 10: Assemble final metadata
        indexes = getattr(get_table_info_with_better_sampling, '_table_indexes', {}).get(f"{db_name}.{table_name}", [])
        
        # Get partition information for BigQuery tables
        partition_info = {}
        # Get database handler using connection manager if available
        if connection_manager and connection_manager.connection_exists(db_name):
            from ..utils.database_handlers import get_database_handler
            db_handler = get_database_handler(db_name, connection_manager)
        else:
            db_handler = get_db_handler(db_name)
        from ..utils.bigquery_handler import BigQueryHandler
        if isinstance(db_handler, BigQueryHandler):
            partition_info = db_handler.get_partition_info(table_name, schema_name)
        
        # Get existing column descriptions and detailed info if available (from BigQuery)
        column_descriptions = {}
        column_details = {}
        if hasattr(get_table_info_with_better_sampling, '_column_descriptions'):
            column_descriptions = get_table_info_with_better_sampling._column_descriptions.get(f"{db_name}.{table_name}", {})
        if hasattr(get_table_info_with_better_sampling, '_column_details'):
            column_details = get_table_info_with_better_sampling._column_details.get(f"{db_name}.{table_name}", {})
        
        # Build base metadata structure
        metadata = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "description": table_insights.get("table_insights", {}).get("description", ""),
            "columns": {
                col_name: {
                    "name": col_name,
                    "data_type": data_type,
                    "is_nullable": column_details.get(col_name, {}).get("is_nullable", True),  # Use actual BigQuery info
                    "description": column_definitions.get(col_name, {}).get("definition", ""),
                    "original_description": column_descriptions.get(col_name, ""),  # Add original BigQuery description
                    "business_name": column_definitions.get(col_name, {}).get("business_name", ""),
                    "purpose": column_definitions.get(col_name, {}).get("purpose", ""),
                    "format": column_definitions.get(col_name, {}).get("format", ""),
                    "constraints": column_definitions.get(col_name, {}).get("business_rules", []),
                    "is_categorical": col_name in categorical_columns,
                    "is_numerical": col_name in numerical_columns,
                    "statistics": numerical_stats.get(col_name, {}) if col_name in numerical_columns else {},
                    "data_quality": data_quality.get(col_name, {}) if include_data_quality else {},
                    # Add BigQuery-specific metadata
                    "bigquery_info": {
                        "mode": "REQUIRED" if not column_details.get(col_name, {}).get("is_nullable", True) else "NULLABLE",
                        "numeric_precision": column_details.get(col_name, {}).get("numeric_precision"),
                        "numeric_scale": column_details.get(col_name, {}).get("numeric_scale"),
                        "character_maximum_length": column_details.get(col_name, {}).get("character_maximum_length")
                    } if column_details.get(col_name) else {}
                } for col_name, data_type in schema.items()
            },
            "constraints": constraints,
            "table_description": {
                "purpose": table_insights.get("table_insights", {}).get("purpose", ""),
                "primary_entity": table_insights.get("table_insights", {}).get("primary_entity", "")
            },
            "indexes": indexes,
            # Note: sample_data removed - fetched dynamically by frontend when needed
            "processing_stats": processing_stats
        }
        
        # Add partition information for BigQuery tables
        if partition_info:
            metadata["partition_info"] = partition_info
        
        # Add optional sections based on parameters
        if include_relationships:
            metadata["relationships"] = table_insights.get("potential_relationships", [])
        
        if include_categorical_definitions:
            metadata["categorical_definitions"] = categorical_definitions
            
        if include_data_quality:
            metadata["data_quality"] = {
                "sample_analyzed": len(sample_data),  # Number of rows analyzed for quality
                "issues": [],
                "recommendations": table_insights.get("table_insights", {}).get("data_quality_recommendations", [])
            }
            
        if include_business_rules:
            metadata["business_rules"] = table_insights.get("business_rules", {})
            
        if include_additional_insights:
            metadata["additional_insights"] = table_insights.get("table_insights", {}).get("additional_insights", {})
            
        if include_aggregation_rules:
            metadata["aggregation_rules"] = table_insights.get("aggregation_rules", [])
            
        if include_query_rules:
            metadata["query_rules"] = table_insights.get("performance_optimization", {})
            
        if include_query_examples:
            metadata["query_examples"] = table_insights.get("query_examples", [])
        
        # Always include basic table description and business use cases if insights were generated
        if table_insights:
            metadata["table_description"].update({
                "business_use_cases": table_insights.get("table_insights", {}).get("usage_patterns", []),
                "special_handling": table_insights.get("table_insights", {}).get("special_handling", [])
            })
            
            # Add structured table_insights section for frontend compatibility
            metadata["table_insights"] = {
                "description": table_insights.get("table_insights", {}).get("description", ""),
                "purpose": table_insights.get("table_insights", {}).get("purpose", ""),
                "domain": table_insights.get("table_insights", {}).get("domain", "General"),
                "category": table_insights.get("table_insights", {}).get("category", "Data"),
                "usage_patterns": table_insights.get("table_insights", {}).get("usage_patterns", []),
                "data_lifecycle": table_insights.get("table_insights", {}).get("data_lifecycle", {}),
                "special_handling": table_insights.get("table_insights", {}).get("special_handling", []),
                "primary_entity": table_insights.get("table_insights", {}).get("primary_entity", ""),
                "additional_insights": table_insights.get("table_insights", {}).get("additional_insights", {}),
                "data_quality_recommendations": table_insights.get("table_insights", {}).get("data_quality_recommendations", [])
            }
        
        # Add final statistics
        processing_stats["end_time"] = datetime.now().isoformat()
        processing_stats["total_duration_seconds"] = time.time() - start_time
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error generating complete table metadata: {str(e)}")
        # Return partial metadata if available
        return {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "error": str(e),
            "processing_stats": processing_stats
        }

# Backward compatibility - keep old function name as an alias
def get_table_info(
    table_name: str, 
    db_name: str, 
    schema_name: str = 'public',
    analysis_sql: Optional[str] = None,
    sample_size: int = 100, 
    num_samples: int = 5
) -> Tuple[Dict[str, str], pd.DataFrame]:
    """
    Legacy function for backward compatibility.
    Use get_table_info_with_better_sampling for improved functionality.
    """
    logger.warning("Using legacy get_table_info function. Consider upgrading to get_table_info_with_better_sampling for better security and sampling.")
    return get_table_info_with_better_sampling(
        table_name=table_name,
        db_name=db_name,
        schema_name=schema_name,
        analysis_sql=analysis_sql,
        sample_size=sample_size,
        num_samples=num_samples,
        use_stratified_sampling=False
    )

if __name__ == "__main__":
    # Example usage
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Generate comprehensive table metadata")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--schema", default="public", help="Schema name")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--sql", help="Custom SQL for analysis")
    parser.add_argument("--sample-size", type=int, default=100, help="Sample size")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples")
    parser.add_argument("--output", help="Output file for metadata (JSON)")
    
    # Optional sections
    parser.add_argument("--no-relationships", action="store_true", 
                        help="Skip relationship analysis")
    parser.add_argument("--no-aggregation-rules", action="store_true", 
                        help="Skip aggregation rules generation")
    parser.add_argument("--no-query-rules", action="store_true", 
                        help="Skip query rules generation")
    parser.add_argument("--no-data-quality", action="store_true", 
                        help="Skip data quality metrics")
    parser.add_argument("--no-query-examples", action="store_true", 
                        help="Skip query examples generation")
    parser.add_argument("--no-additional-insights", action="store_true", 
                        help="Skip additional insights generation")
    parser.add_argument("--no-business-rules", action="store_true", 
                        help="Skip business rules generation")
    parser.add_argument("--no-categorical-definitions", action="store_true", 
                        help="Skip categorical value definitions")
    
    # Quick presets
    parser.add_argument("--minimal", action="store_true", 
                        help="Generate minimal metadata (only basic info)")
    parser.add_argument("--fast", action="store_true", 
                        help="Generate fast metadata (skip expensive LLM operations)")
    
    args = parser.parse_args()
    
    # Handle presets
    if args.minimal:
        include_relationships = False
        include_aggregation_rules = False
        include_query_rules = False
        include_data_quality = False
        include_query_examples = False
        include_additional_insights = False
        include_business_rules = False
        include_categorical_definitions = False
    elif args.fast:
        include_relationships = False
        include_aggregation_rules = False
        include_query_rules = False
        include_data_quality = True
        include_query_examples = False
        include_additional_insights = False
        include_business_rules = False
        include_categorical_definitions = False
    else:
        # Use individual flags
        include_relationships = not args.no_relationships
        include_aggregation_rules = not args.no_aggregation_rules
        include_query_rules = not args.no_query_rules
        include_data_quality = not args.no_data_quality
        include_query_examples = not args.no_query_examples
        include_additional_insights = not args.no_additional_insights
        include_business_rules = not args.no_business_rules
        include_categorical_definitions = not args.no_categorical_definitions
    
    metadata = generate_complete_table_metadata(
        table_name=args.table,
        db_name=args.db,
        schema_name=args.schema,
        analysis_sql=args.sql,
        sample_size=args.sample_size,
        num_samples=args.num_samples,
        include_relationships=include_relationships,
        include_aggregation_rules=include_aggregation_rules,
        include_query_rules=include_query_rules,
        include_data_quality=include_data_quality,
        include_query_examples=include_query_examples,
        include_additional_insights=include_additional_insights,
        include_business_rules=include_business_rules,
        include_categorical_definitions=include_categorical_definitions
    )
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {args.output}")
        
        # Print summary of what was included
        stats = metadata.get('processing_stats', {})
        optional_sections = stats.get('optional_sections', {})
        enabled_sections = [k for k, v in optional_sections.items() if v]
        disabled_sections = [k for k, v in optional_sections.items() if not v]
        
        print(f"\nGenerated sections: {', '.join(enabled_sections)}")
        if disabled_sections:
            print(f"Skipped sections: {', '.join(disabled_sections)}")
            
        total_time = stats.get('total_duration_seconds', 0)
        print(f"Total processing time: {total_time:.2f} seconds")
    else:
        print(json.dumps(metadata, indent=2)) 