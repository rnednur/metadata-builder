"""
Semantic model generation for various analytics platforms.
This module provides functions to generate semantic models for tools like dbt, LookML, Cube.js, etc.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from openai import OpenAI
from ..config.config import get_llm_api_config, get_db_handler
from ..utils.token_counter import TokenCounter
from .llm_service import LLMClient
from ..utils.metadata_utils import extract_constraints

logger = logging.getLogger(__name__)


def chunk_metadata_by_tokens(
    metadata: Dict[str, Any], 
    token_threshold: int, 
    token_counter: TokenCounter
) -> Dict[str, Any]:
    """
    Chunk metadata to stay within token limits.
    
    Args:
        metadata: Metadata dictionary to chunk
        token_threshold: Maximum tokens allowed
        token_counter: Token counter instance
        
    Returns:
        Chunked metadata dictionary
    """
    # Convert metadata to JSON string to count tokens
    metadata_str = json.dumps(metadata, indent=2)
    current_tokens = token_counter.count_tokens(metadata_str)
    
    if current_tokens <= token_threshold:
        return metadata
    
    # If over threshold, truncate sample data and other large fields
    chunked_metadata = metadata.copy()
    
    # Remove or reduce large fields
    if 'sample_data' in chunked_metadata:
        # Keep only first few rows of sample data
        sample_data = chunked_metadata['sample_data']
        if isinstance(sample_data, list) and len(sample_data) > 5:
            chunked_metadata['sample_data'] = sample_data[:5]
    
    # Truncate long text fields
    for table_key, table_data in chunked_metadata.items():
        if isinstance(table_data, dict):
            if 'columns' in table_data:
                for col_key, col_data in table_data['columns'].items():
                    if isinstance(col_data, dict):
                        for field, value in col_data.items():
                            if isinstance(value, str) and len(value) > 200:
                                col_data[field] = value[:200] + "..."
    
    return chunked_metadata


def call_llm_json(client: OpenAI, model: str, prompt: str) -> Dict[str, Any]:
    """
    Call LLM and get JSON response.
    
    Args:
        client: OpenAI client instance
        model: Model name to use
        prompt: Prompt to send
        
    Returns:
        Parsed JSON response
    """
    llm_client = LLMClient(model=model, client=client)
    return llm_client.call_llm_json(prompt)


def generate_lookml_model(
    db_name: str,
    schema_name: str,
    table_names: List[str],
    model_name: str,
    include_derived_tables: bool = False,
    include_explores: bool = True,
    metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    model: str = None,
    generation_type: str = "full",
    additional_prompt: Optional[str] = None,
    existing_lookml: Optional[str] = None,
    token_threshold: Optional[int] = 8000
) -> Dict[str, Any]:
    """
    Generates a LookML semantic model for the specified tables.
    If metadata is provided, it will be used instead of fetching from the database.

    Args:
        db_name: Database name
        schema_name: Schema name
        table_names: List of table names
        model_name: Name of the LookML model
        include_derived_tables: Whether to include derived table suggestions
        include_explores: Whether to include explore suggestions
        metadata: Optional metadata for tables
        model: Optional model name for LLM
        generation_type: Type of generation ('full' or 'append')
        additional_prompt: Additional instructions for LookML generation
        existing_lookml: Existing LookML content when appending
        token_threshold: Optional maximum token count for metadata
    """
    logger.info(f"Starting LookML generation for tables: {table_names}")
    start_time = time.time()
    token_counter = TokenCounter(model)

    # Get API config including model
    api_key, base_url, model_name = get_llm_api_config()
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    model = model or model_name
    logger.debug(f"Using model: {model}")

    # Use provided metadata or fetch from database
    tables_metadata = {}
    if metadata:
        logger.info("Using provided metadata")
        # If token threshold is set, chunk the metadata
        if token_threshold:
            logger.debug(f"Chunking metadata with token threshold: {token_threshold}")
            tables_metadata = chunk_metadata_by_tokens(metadata, token_threshold, token_counter)
                
            logger.debug(f"Chunked metadata to meet token threshold of {token_threshold}")
        else:
            tables_metadata = metadata
    else:
        logger.debug("Fetching metadata from database")
        # Get metadata for each table
        db = get_db_handler(db_name)
        try:
            for table_name in table_names:
                logger.debug(f"Processing metadata for table: {table_name}")
                # Get schema and constraints
                schema = db.get_table_schema(table_name)
                constraints = extract_constraints(table_name, db_name)

                table_metadata = {
                    'schema': schema,
                    'constraints': constraints
                }

                # Get catalog entry if available
                try:
                    # Note: get_catalog_entry function doesn't exist yet, so we'll skip this for now
                    # catalog_entry = get_catalog_entry(db_name, schema_name, table_name)
                    # if catalog_entry:
                    #     table_metadata['metadata'] = catalog_entry
                    #     logger.info(f"Retrieved catalog entry for {table_name}")
                    pass
                except Exception as e:
                    logger.warning(f"Could not get catalog entry for {table_name}: {e}")

                # Apply token threshold if set
                if token_threshold:
                    logger.info(f"Applying token threshold to {table_name} metadata")
                    table_metadata = chunk_metadata_by_tokens(table_metadata, token_threshold, token_counter)

                tables_metadata[table_name] = table_metadata
        finally:
            db.close()

    if generation_type == "append" and existing_lookml and additional_prompt:
        logger.info("Generating append-type LookML with additional measures")
        # Create prompt for appending new measures
        append_prompt = f"""Given this existing LookML model and additional requirements, generate new measures to add:

Existing LookML:
{existing_lookml}

Additional Requirements:
{additional_prompt}

Table Metadata:
{json.dumps(tables_metadata, indent=2)}

Generate ONLY new measures that:
1. Address the additional requirements
2. Don't duplicate existing measures
3. Use proper LookML syntax and best practices
4. Include clear descriptions
5. Use appropriate aggregation types and SQL definitions

Return the response in this JSON format:
{{
    "new_measures": [
        {{
            "view_name": "name of the view to add measure to",
            "measures": [
                {{
                    "name": "measure name",
                    "type": "measure type",
                    "sql": "SQL definition",
                    "description": "Clear description",
                    "value_format": "optional format string"
                }}
            ]
        }}
    ]
}}"""

        try:
            # Generate new measures
            logger.info("Calling LLM to generate new measures")
            measures_response = call_llm_json(client, model, append_prompt)
            logger.debug(f"Raw LLM response for measures: {measures_response}")

            if not measures_response:
                logger.error("Empty response received from LLM for measures generation")
                raise ValueError("Empty response from LLM")

            # Parse existing LookML to combine with new measures
            logger.info("Parsing existing LookML")
            import yaml
            existing_model = yaml.safe_load(existing_lookml)

            # Add new measures to existing views
            measures_added = 0
            if measures_response and 'new_measures' in measures_response:
                logger.info("Adding new measures to views")
                for new_measure_group in measures_response['new_measures']:
                    view_name = new_measure_group['view_name']
                    for view in existing_model.get('views', []):
                        if view['view_name'] == view_name:
                            view['measures'].extend(new_measure_group['measures'])
                            measures_added += len(new_measure_group['measures'])
                logger.info(f"Added {measures_added} new measures")
            else:
                logger.warning("No new measures found in LLM response")

            result = {
                'model_name': existing_model.get('model_name', model_name),
                'views': existing_model.get('views', []),
                'explores': existing_model.get('explores', []),
                'processing_stats': {
                    'total_time_seconds': round(time.time() - start_time, 2),
                    'total_tokens': token_counter.get_usage_stats()['total_tokens'],
                    'request_count': token_counter.get_usage_stats()['request_count'],
                    'average_tokens_per_request': round(token_counter.get_usage_stats()['average_tokens_per_request'], 2),
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'measures_added': measures_added
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error appending measures to LookML: {str(e)}", exc_info=True)
            raise

    # Create prompt for generating LookML views
    logger.info("Generating views prompt")
    views_prompt = f"""Generate LookML view definitions for these tables:

Table Metadata:
{json.dumps(tables_metadata, indent=2)}

{f'''Additional Requirements:
{additional_prompt}''' if additional_prompt else ''}

For each table, create a LookML view that:
1. Uses appropriate dimension types based on the column data types and usage
2. Includes clear descriptions for dimensions and measures
3. Sets primary keys and foreign keys correctly
4. Creates relevant measures based on the data type and business context
5. Uses proper LookML syntax and best practices

{f'''Also suggest derived tables where appropriate for:
- Common aggregations
- Useful combinations of data
- Performance optimization''' if include_derived_tables else ''}

Return the response in this JSON format:
{{
    "views": [
        {{
            "view_name": "name of the view",
            "sql_table_name": "{schema_name}.table_name",
            "dimensions": [
                {{
                    "name": "dimension name",
                    "type": "dimension type",
                    "sql": "SQL definition",
                    "description": "Clear description",
                    "primary_key": true/false,
                    "group_label": "optional grouping label",
                    "value_format": "optional format string"
                }}
            ],
            "measures": [
                {{
                    "name": "measure name",
                    "type": "measure type",
                    "sql": "SQL definition",
                    "description": "Clear description",
                    "value_format": "optional format string"
                }}
            ],
            "derived_tables": [
                {{
                    "name": "derived table name",
                    "sql": "SQL definition",
                    "dimensions": [],
                    "measures": []
                }}
            ],
            "suggestions": {{
                "indexes": ["suggested indexes"],
                "relationships": ["suggested relationships"],
                "drill_fields": ["suggested drill fields"]
            }}
        }}
    ]
}}"""

    try:
        # Generate views with token limit handling
        logger.info("Calling LLM to generate views")
        logger.info(f"Sending prompt for views:\n{views_prompt}")
        
        views_response = call_llm_json(client, model, views_prompt)
        logger.debug(f"Raw LLM response for views: {views_response}")

        if not views_response:
            logger.error("Empty response received from LLM for views generation")
            raise ValueError("Empty response from LLM")

        if 'views' not in views_response:
            logger.error(f"Invalid response format. Expected 'views' key but got: {list(views_response.keys())}")
            raise ValueError("Invalid response format from LLM")

        logger.info(f"Generated {len(views_response.get('views', []))} views")

        explores = []
        if include_explores:
            logger.info("Generating explores prompt")
            # Create prompt for generating explores
            explores_prompt = f"""Based on these LookML views and table metadata:

Views:
{json.dumps(views_response.get('views', []), indent=2)}

Table Metadata:
{json.dumps(tables_metadata, indent=2)}

Generate LookML explore definitions that:
1. Identify logical join relationships between views
2. Set appropriate join types and relationships
3. Include relevant fields in the joins
4. Group related explores together
5. Use proper LookML syntax and best practices
6. Consider foreign key relationships from metadata
7. Add appropriate labels and descriptions

Return the response in this JSON format:
{{
    "explores": [
        {{
            "name": "explore name",
            "view_name": "base view name",
            "label": "User-friendly label",
            "description": "Clear description",
            "fields": ["included fields"],
            "joins": [
                {{
                    "name": "joined view name",
                    "type": "join type",
                    "relationship": "one_to_many/many_to_one/etc",
                    "sql_on": "SQL join condition",
                    "fields": ["included fields from joined view"]
                }}
            ],
            "suggestions": {{
                "fields_to_consider": ["suggested fields to include"],
                "common_queries": ["example business questions"],
                "access_filters": ["suggested access filters"]
            }}
        }}
    ]
}}"""

            logger.info("Calling LLM to generate explores")
            
            explores_response = call_llm_json(client, model, explores_prompt)
            logger.debug(f"Raw LLM response for explores: {explores_response}")

            if not explores_response:
                logger.error("Empty response received from LLM for explores generation")
                raise ValueError("Empty response from LLM")

            explores = explores_response.get('explores', [])
            logger.info(f"Generated {len(explores)} explores")

        # Calculate processing stats
        total_time = time.time() - start_time
        token_stats = token_counter.get_usage_stats()

        result = {
            'model_name': model_name,
            'views': views_response.get('views', []),
            'explores': explores,
            'processing_stats': {
                'total_time_seconds': round(total_time, 2),
                'total_tokens': token_stats['total_tokens'],
                'request_count': token_stats['request_count'],
                'average_tokens_per_request': round(token_stats['average_tokens_per_request'], 2),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        logger.info(f"\nLookML Generation Stats:")
        logger.info(f"Total time: {total_time:.2f} seconds")
        logger.info(f"Total tokens: {token_stats['total_tokens']}")
        logger.info(f"Total requests: {token_stats['request_count']}")
        logger.info(f"Average tokens per request: {token_stats['average_tokens_per_request']:.2f}")

        return result

    except Exception as e:
        logger.error(f"Error generating LookML model: {str(e)}", exc_info=True)
        return {
            'model_name': model_name,
            'views': [],
            'explores': [],
            'processing_stats': {
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        } 