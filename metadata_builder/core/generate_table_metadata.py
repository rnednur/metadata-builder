import logging
import pandas as pd
import json
from typing import Dict, Any, List, Tuple, Optional
import random
import time
import concurrent.futures
from datetime import datetime, timedelta

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

def get_table_info(
    table_name: str, 
    db_name: str, 
    schema_name: str = 'public',
    analysis_sql: Optional[str] = None,
    sample_size: int = 100, 
    num_samples: int = 5
) -> Tuple[Dict[str, str], pd.DataFrame]:
    """
    Get table schema and sample data
    
    Args:
        table_name: Name of the table
        db_name: Database name
        schema_name: Schema name
        analysis_sql: Optional custom SQL query
        sample_size: Size of each sample
        num_samples: Number of samples to take
        
    Returns:
        Tuple with schema dictionary and sample DataFrame
    """
    db = get_db_handler(db_name)
    try:
        # Get schema using database handler
        schema = db.get_table_schema(table_name, schema_name)
        logger.debug(f"schema: {schema}")

        # Get table indexes
        indexes = db.get_table_indexes(table_name, schema_name)
        logger.debug(f"indexes: {indexes}")

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
            # Retrieve sample data using standard method
            if analysis_sql:
                # Check if analysis_sql already contains LIMIT
                has_limit = 'LIMIT' in analysis_sql.upper()
                
                if not has_limit and sample_size > 0 and num_samples > 0:
                    logger.info(f"Applying sampling to analysis SQL: size={sample_size}, samples={num_samples}")
                    
                    # Check query cost before executing
                    is_safe, reason = db.check_query_cost(analysis_sql, table_name, schema_name)
                    if not is_safe:
                        logger.warning(f"Query cost analysis warning: {reason}")
                        raise ValueError(f"Query would be too costly to execute: {reason}")
                    
                    samples = []
                    # Get total count for offset calculation
                    count_sql = f"SELECT COUNT(*) as count FROM ({analysis_sql}) AS analysis_query"
                    count_result = db.fetch_one(count_sql)
                    total_count = int(count_result['count']) if count_result else 0
                    
                    if total_count > 0:
                        # Calculate offsets for random sampling
                        if total_count <= sample_size * num_samples:
                            # If total count is small, just get everything
                            query = f"{analysis_sql} LIMIT {total_count}"
                            result = db.fetch_all(query)
                            samples.append(pd.DataFrame(result))
                        else:
                            # Random sampling using different offsets
                            max_offset = total_count - sample_size
                            offsets = random.sample(range(max_offset), min(num_samples, max_offset))
                            
                            for offset in offsets:
                                query = f"{analysis_sql} LIMIT {sample_size} OFFSET {offset}"
                                result = db.fetch_all(query)
                                if result:
                                    samples.append(pd.DataFrame(result))
                    
                    # Combine all samples
                    if samples:
                        df = pd.concat(samples, ignore_index=True)
                    else:
                        df = pd.DataFrame()
                else:
                    # Analysis SQL already has LIMIT or sampling is disabled
                    result = db.fetch_all(analysis_sql)
                    df = pd.DataFrame(result)
            else:
                # Default sampling from table
                samples = []
                
                # Get table row count
                row_count = db.get_row_count(table_name, schema_name)
                if row_count and row_count > 0:
                    if row_count <= sample_size * num_samples:
                        # Small table, get everything
                        table_ref = f"{schema_name}.{table_name}" if schema_name else table_name
                        query = f"SELECT * FROM {table_ref} LIMIT {row_count}"
                        result = db.fetch_all(query)
                        samples.append(pd.DataFrame(result))
                    else:
                        # Random sampling with different offsets
                        max_offset = row_count - sample_size
                        offsets = random.sample(range(max_offset), min(num_samples, max_offset))
                        
                        table_ref = f"{schema_name}.{table_name}" if schema_name else table_name
                        for offset in offsets:
                            query = f"SELECT * FROM {table_ref} LIMIT {sample_size} OFFSET {offset}"
                            result = db.fetch_all(query)
                            if result:
                                samples.append(pd.DataFrame(result))
                
                # Combine all samples
                if samples:
                    df = pd.concat(samples, ignore_index=True)
                else:
                    df = pd.DataFrame()
        
        return schema, df
    
    finally:
        db.close()

@retry(
    retry=retry_if_exception_type(OpenAIError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_llm_api(prompt: str, system_message: str = None, temperature: float = 0.2) -> str:
    """
    Call OpenAI API with retry logic
    
    Args:
        prompt: The prompt to send to the API
        system_message: Optional system message
        temperature: Temperature for randomness (0.0 to 1.0)
        
    Returns:
        API response text
    """
    try:
        api_config = get_llm_api_config()
        
        client = OpenAI(
            api_key=api_config.get('api_key'),
            base_url=api_config.get('base_url', 'https://api.openai.com/v1'),
        )
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=api_config.get('model', 'gpt-4-turbo-preview'),
            messages=messages,
            temperature=temperature,
            max_tokens=api_config.get('max_tokens', 4000),
        )
        
        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response from LLM API")
            
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error calling LLM API: {str(e)}")
        raise

def generate_column_definitions(
    schema: Dict[str, str],
    categorical_values: Dict[str, List[Any]],
    db_name: str,
    table_name: str,
    schema_name: str,
    numerical_stats: Dict[str, Dict[str, float]],
    constraints: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """
    Generate column definitions using LLM
    
    Args:
        schema: Dictionary mapping column names to data types
        categorical_values: Dictionary mapping column names to unique values
        db_name: Database name
        table_name: Table name
        schema_name: Schema name
        numerical_stats: Dictionary with numerical statistics
        constraints: Table constraints
        
    Returns:
        Dictionary with column definitions
    """
    column_definitions = {}
    
    # Build the prompt for all columns
    prompt = f"""### Task
Generate accurate and detailed business definitions for each column in the database table.

### Database Context
Database: {db_name}
Schema: {schema_name}
Table: {table_name}

### Table Information
The following information is known about each column:

"""

    # Add information for each column
    for column_name, data_type in schema.items():
        prompt += f"\n## Column: {column_name}\n"
        prompt += f"Data Type: {data_type}\n"
        
        # Add constraints information
        is_primary = column_name in constraints.get('primary_keys', [])
        prompt += f"Primary Key: {'Yes' if is_primary else 'No'}\n"
        
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
For each column, provide:
1. A concise business definition (1-2 sentences explaining what this column represents in business terms)
2. The column's purpose (what it is used for)
3. Expected format and values
4. Any business rules associated with this column
5. Potential data quality concerns

Format your response as a structured JSON with column names as keys, like this:
{
  "column_name": {
    "definition": "Business definition here",
    "purpose": "Purpose here",
    "format": "Expected format",
    "business_rules": ["rule 1", "rule 2"],
    "data_quality_checks": ["check 1", "check 2"]
  },
  ...
}

Ensure the output is valid JSON that can be parsed programmatically.
"""

    # Call LLM API
    try:
        system_message = "You are an expert database analyst who specializes in creating clear and accurate metadata documentation."
        response = call_llm_api(prompt, system_message)
        
        # Extract JSON from response
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            json_str = response[json_start:json_end + 1]
            column_definitions = json.loads(json_str)
        else:
            logger.error("Failed to extract JSON from LLM response")
            
    except Exception as e:
        logger.error(f"Error generating column definitions: {str(e)}")
        
    return column_definitions

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
        api_config = get_llm_api_config()
        api_key = api_config.get('api_key')
        base_url = api_config.get('base_url', 'https://api.openai.com/v1')
        model = model or api_config.get('model', 'gpt-4-turbo-preview')
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
    sample_rows = sample_data.head(5).to_dict(orient='records')
    sample_data_str = json.dumps(sample_rows, indent=2, default=str)
    
    # Build the base prompt
    prompt = f"""### Task
Generate comprehensive insights about this database table.

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
Based on the provided information, generate the following insights:

1. Table purpose (what this table is used for in the business)
2. Primary entity (the main business entity this table represents)
3. Business use cases for this table
4. Special handling considerations
"""

    # Add optional sections to the prompt based on parameters
    optional_sections = []
    
    if include_relationships:
        optional_sections.append("5. Potential relationships with other tables")
    
    if include_business_rules:
        optional_sections.append("6. Recommended business rules and validations")
    
    if include_aggregation_rules:
        optional_sections.append("7. Suggested aggregation rules for analytics")
    
    if include_query_rules:
        optional_sections.append("8. Query optimization rules and recommendations")
    
    if include_query_examples:
        optional_sections.append("9. Example SQL queries for common use cases")
    
    if include_additional_insights:
        optional_sections.append("10. Additional domain-specific insights")
    
    # Add optional sections to prompt
    if optional_sections:
        prompt += "\n" + "\n".join(optional_sections)
    
    # Build the JSON response format based on what's requested
    json_structure = {
        "table_purpose": "Description of what this table stores and its business function",
        "primary_entity": "The main business entity this table represents",
        "business_use_cases": [
            "Use case 1 description",
            "Use case 2 description"
        ],
        "special_handling": [
            "Special handling consideration 1",
            "Special handling consideration 2"
        ]
    }
    
    if include_relationships:
        json_structure["potential_relationships"] = [
            {
                "column": "column_name",
                "relates_to": "likely related table",
                "relationship_type": "one-to-many/many-to-one/etc",
                "description": "description of relationship"
            }
        ]
    
    if include_business_rules:
        json_structure["recommended_rules"] = [
            "Rule 1 description",
            "Rule 2 description"
        ]
        json_structure["data_quality_recommendations"] = [
            "Recommendation 1",
            "Recommendation 2"
        ]
    
    if include_aggregation_rules:
        json_structure["aggregation_rules"] = [
            {
                "rule_name": "aggregation rule name",
                "description": "what this aggregation represents",
                "sql_pattern": "SQL pattern for aggregation",
                "use_case": "when to use this aggregation"
            }
        ]
    
    if include_query_rules:
        json_structure["query_rules"] = [
            {
                "rule_name": "query rule name",
                "description": "query optimization rule",
                "recommendation": "specific recommendation",
                "impact": "performance impact"
            }
        ]
    
    if include_query_examples:
        json_structure["query_examples"] = [
            {
                "name": "example query name",
                "description": "what this query does",
                "sql": "SELECT example SQL query",
                "use_case": "when to use this query"
            }
        ]
    
    if include_additional_insights:
        json_structure["additional_insights"] = {
            "domain_specific": "Domain-specific observations",
            "patterns": "Data patterns observed",
            "recommendations": "Additional recommendations"
        }
    
    prompt += f"""

Format your response as a structured JSON like this:
{json.dumps(json_structure, indent=2)}

Ensure the output is valid JSON that can be parsed programmatically.
"""

    # Call LLM API
    try:
        system_message = "You are an expert data architect who specializes in understanding database schemas and their business implications."
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
        return {}

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
        schema, sample_data = get_table_info(
            table_name=table_name,
            db_name=db_name,
            schema_name=schema_name,
            analysis_sql=analysis_sql,
            sample_size=sample_size,
            num_samples=num_samples
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
        tasks.append(("extract_constraints", lambda: extract_constraints(table_name, db_name)))
        
        # Step 4: Compute numerical statistics (always needed for basic metadata)
        tasks.append(("compute_numerical_stats", lambda: compute_numerical_stats(sample_data, numerical_columns)))
        
        # Step 5: Compute data quality metrics (optional)
        if include_data_quality:
            tasks.append(("compute_data_quality_metrics", lambda: compute_data_quality_metrics(sample_data, schema)))
        
        # Step 6: Extract categorical values (needed for categorical definitions)
        if include_categorical_definitions:
            tasks.append(("extract_categorical_values", lambda: extract_categorical_values(
                sample_data, categorical_columns, db_name, schema_name, table_name)))
        
        # Run tasks in parallel
        step_start = time.time()
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_task = {executor.submit(task_func): task_name for task_name, task_func in tasks}
            for future in concurrent.futures.as_completed(future_to_task):
                task_name = future_to_task[future]
                try:
                    results[task_name] = future.result()
                except Exception as e:
                    logger.error(f"Error in task {task_name}: {str(e)}")
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
        column_definitions = generate_column_definitions(
            schema=schema,
            categorical_values=categorical_values,
            db_name=db_name,
            table_name=table_name,
            schema_name=schema_name,
            numerical_stats=numerical_stats,
            constraints=constraints
        )
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
            processing_stats["steps"].append({
                "step": "generate_categorical_definitions",
                "duration_seconds": time.time() - step_start,
                "columns_processed": len(categorical_definitions)
            })
        
        # Step 9: Generate table-level insights using LLM (conditional based on what's needed)
        table_insights = {}
        if any([include_relationships, include_business_rules, include_additional_insights, include_query_examples]):
            step_start = time.time()
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
            processing_stats["steps"].append({
                "step": "generate_table_insights",
                "duration_seconds": time.time() - step_start
            })
        
        # Step 10: Assemble final metadata
        indexes = getattr(get_table_info, '_table_indexes', {}).get(f"{db_name}.{table_name}", [])
        
        # Get partition information for BigQuery tables
        partition_info = {}
        db_handler = get_db_handler(db_name)
        from ..utils.bigquery_handler import BigQueryHandler
        if isinstance(db_handler, BigQueryHandler):
            partition_info = db_handler.get_partition_info(table_name, schema_name)
        
        # Build base metadata structure
        metadata = {
            "database_name": db_name,
            "schema_name": schema_name,
            "table_name": table_name,
            "description": table_insights.get("table_purpose", ""),
            "columns": {
                col_name: {
                    "name": col_name,
                    "data_type": data_type,
                    "is_nullable": True,  # Default, would need actual DB info
                    "description": column_definitions.get(col_name, {}).get("definition", ""),
                    "business_name": column_definitions.get(col_name, {}).get("business_name", ""),
                    "purpose": column_definitions.get(col_name, {}).get("purpose", ""),
                    "format": column_definitions.get(col_name, {}).get("format", ""),
                    "constraints": column_definitions.get(col_name, {}).get("business_rules", []),
                    "is_categorical": col_name in categorical_columns,
                    "is_numerical": col_name in numerical_columns,
                    "statistics": numerical_stats.get(col_name, {}) if col_name in numerical_columns else {},
                    "data_quality": data_quality.get(col_name, {}) if include_data_quality else {}
                } for col_name, data_type in schema.items()
            },
            "constraints": constraints,
            "table_description": {
                "purpose": table_insights.get("table_purpose", ""),
                "primary_entity": table_insights.get("primary_entity", "")
            },
            "indexes": indexes,
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
                "row_count": len(sample_data),
                "issues": [],
                "recommendations": table_insights.get("data_quality_recommendations", [])
            }
            
        if include_business_rules:
            metadata["business_rules"] = table_insights.get("recommended_rules", [])
            
        if include_additional_insights:
            metadata["additional_insights"] = table_insights.get("additional_insights", {})
            
        if include_aggregation_rules:
            metadata["aggregation_rules"] = table_insights.get("aggregation_rules", [])
            
        if include_query_rules:
            metadata["query_rules"] = table_insights.get("query_rules", [])
            
        if include_query_examples:
            metadata["query_examples"] = table_insights.get("query_examples", [])
        
        # Always include basic table description and business use cases if insights were generated
        if table_insights:
            metadata["table_description"].update({
                "business_use_cases": table_insights.get("business_use_cases", []),
                "special_handling": table_insights.get("special_handling", [])
            })
        
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