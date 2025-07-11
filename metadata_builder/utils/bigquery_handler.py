"""
BigQuery-specific database handler with partition awareness.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.cloud.bigquery import Client, QueryJobConfig
from .database_handler import DatabaseHandler
from ..config.config import get_db_config
from google.oauth2 import service_account
import json

logger = logging.getLogger(__name__)

class BigQueryHandler(DatabaseHandler):
    """BigQuery-specific implementation with partition awareness"""
    
    def __init__(self, db_name: str = None):
        super().__init__(db_name)
        self.client = None
        self.project_id = None
        self.job_project_id = None
        self._dataset_project_cache = {}  # Cache for dataset -> project mapping
        self._table_cache = {}  # Cache for dataset -> tables mapping
        if db_name:
            self.connect(db_name)
    
    def connect(self, db_name: str = None) -> None:
        """Establish BigQuery connection"""
        try:
            if db_name:
                self.db_name = db_name
                self.config = get_db_config(db_name)
            
            if not self.config:
                raise ValueError(f"No configuration found for database: {self.db_name}")
            
            self._connect_with_bigquery_config(self.config)
            
        except Exception as e:
            logger.error(f"Error connecting to BigQuery {self.db_name}: {str(e)}")
            raise
    
    def connect_with_config(self, db_config: Dict[str, Any]) -> None:
        """
        Connect to BigQuery using provided configuration.
        This is used when connection info comes from ConnectionManager.
        """
        try:
            self.config = db_config
            self._connect_with_bigquery_config(db_config)
            
        except Exception as e:
            logger.error(f"Error connecting to BigQuery {self.db_name} with config: {str(e)}")
            raise
    
    def _connect_with_bigquery_config(self, config: Dict[str, Any]) -> None:
        """Internal method to connect with BigQuery configuration."""
        self.project_id = config.get('project_id') or config.get('connection_params', {}).get('project_id')
        
        # Credentials can be provided as:
        # 1. Path to service-account JSON file
        # 2. Raw JSON string pasted via UI (stored as credentials_path)
        # 3. Stored inside connection_params under the same key
        credentials_path = (
            config.get('credentials_path') or
            config.get('connection_params', {}).get('credentials_path')
        )
        
        if not self.project_id:
            raise ValueError("BigQuery project_id is required")
        
        # Initialize BigQuery client
        if credentials_path:
            # Detect whether we received raw JSON content instead of a file path
            if credentials_path.strip().startswith('{'):
                try:
                    credentials_info = json.loads(credentials_path)
                    credentials = service_account.Credentials.from_service_account_info(credentials_info)
                    # For service accounts, use the project from the JSON for job execution
                    self.job_project_id = credentials_info.get('project_id', self.project_id)
                except Exception as e:
                    raise ValueError(f"Invalid credentials JSON: {e}")
            else:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                # For file-based credentials, use data project for jobs
                self.job_project_id = self.project_id

            self.client = bigquery.Client(project=self.job_project_id, credentials=credentials)
        else:
            # Check if credentials are required (when not using default environment credentials)
            self.job_project_id = self.project_id
            try:
                # Try to use default credentials (e.g., from environment)
                self.client = bigquery.Client(project=self.project_id)
                # Test the connection by listing datasets instead of running a query
                list(self.client.list_datasets(max_results=1))
            except Exception as e:
                if "does not have bigquery.jobs.create permission" in str(e):
                    # For public datasets, we need a different approach
                    logger.warning(f"No job creation permission in {self.project_id}. Using read-only access.")
                    self.client = bigquery.Client(project=self.project_id)
                else:
                    raise ValueError(f"BigQuery credentials are required. Please provide service account credentials. Error: {str(e)}")
        
        logger.info(f"Successfully connected to BigQuery project: {self.project_id}")
    
    def get_partition_info(self, table_name: str, schema_name: str = None) -> Dict[str, Any]:
        """
        Get partition information for a BigQuery table.
        
        Returns:
            Dictionary with partition information including type, column, and available partitions
        """
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            # Get table metadata
            table = self.client.get_table(table_ref)
            
            partition_info = {
                "is_partitioned": False,
                "partition_type": None,
                "partition_column": None,
                "clustering_fields": [],
                "available_partitions": []
            }
            
            # Check if table is partitioned
            if table.time_partitioning:
                partition_info["is_partitioned"] = True
                partition_info["partition_type"] = table.time_partitioning.type_
                partition_info["partition_column"] = table.time_partitioning.field
                
                # Get available partitions from INFORMATION_SCHEMA
                partitions_query = f"""
                    SELECT partition_id, total_rows, total_logical_bytes
                    FROM `{resolved_project}.{dataset_id}.INFORMATION_SCHEMA.PARTITIONS`
                    WHERE table_name = '{table_name}'
                    AND partition_id IS NOT NULL
                    AND partition_id != '__NULL__'
                    ORDER BY partition_id DESC
                    LIMIT 100
                """
                
                query_job = self.client.query(partitions_query)
                results = query_job.result()
                
                partition_info["available_partitions"] = [
                    {
                        "partition_id": row.partition_id,
                        "total_rows": row.total_rows,
                        "total_logical_bytes": row.total_logical_bytes
                    }
                    for row in results
                ]
            
            # Get clustering information
            if table.clustering_fields:
                partition_info["clustering_fields"] = table.clustering_fields
            
            return partition_info
            
        except Exception as e:
            logger.error(f"Error getting partition info for {table_name}: {str(e)}")
            return {"is_partitioned": False}
    
    def get_partition_aware_sample(
        self, 
        table_name: str, 
        schema_name: str = None,
        sample_size: int = 100,
        num_samples: int = 5,
        max_partitions: int = 10
    ) -> List[Dict]:
        """
        Get sample data from partitioned table with partition pruning.
        
        Args:
            table_name: Name of the table
            schema_name: Dataset name in BigQuery
            sample_size: Size of each sample
            num_samples: Number of samples to take
            max_partitions: Maximum number of partitions to sample from
            
        Returns:
            List of sample records
        """
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            # Get partition information
            partition_info = self.get_partition_info(table_name, schema_name)
            
            if not partition_info["is_partitioned"]:
                # Non-partitioned table - use standard sampling
                # Use a reasonable sample percentage (1-10%) or fallback to LIMIT
                sample_percentage = min(10, max(1, sample_size * num_samples / 1000))
                
                query = f"""
                    SELECT * FROM `{table_ref}`
                    TABLESAMPLE SYSTEM ({sample_percentage} PERCENT)
                    LIMIT {sample_size * num_samples}
                """
            else:
                # Partitioned table - sample from recent partitions
                available_partitions = partition_info["available_partitions"]
                
                if not available_partitions:
                    logger.warning(f"No partitions found for {table_name}")
                    return []
                
                # Select recent partitions with data
                recent_partitions = [
                    p for p in available_partitions[:max_partitions]
                    if p.get("total_rows", 0) > 0
                ]
                
                if not recent_partitions:
                    logger.warning(f"No partitions with data found for {table_name}")
                    return []
                
                # Build partition-aware query
                partition_column = partition_info["partition_column"]
                if partition_column:
                    # Use partition column for filtering
                    partition_filters = []
                    for partition in recent_partitions[:num_samples]:
                        partition_id = partition["partition_id"]
                        if partition_id.isdigit() and len(partition_id) == 8:
                            # Date partition (YYYYMMDD)
                            date_str = f"{partition_id[:4]}-{partition_id[4:6]}-{partition_id[6:8]}"
                            partition_filters.append(f"DATE({partition_column}) = '{date_str}'")
                        else:
                            # Other partition types
                            partition_filters.append(f"{partition_column} = '{partition_id}'")
                    
                    where_clause = " OR ".join(partition_filters)
                    query = f"""
                        SELECT * FROM `{table_ref}`
                        WHERE {where_clause}
                        LIMIT {sample_size * num_samples}
                    """
                else:
                    # Use table decorators for specific partitions
                    partition_queries = []
                    for partition in recent_partitions[:num_samples]:
                        partition_id = partition["partition_id"]
                        partition_queries.append(f"""
                            SELECT * FROM `{table_ref}${partition_id}`
                            LIMIT {sample_size}
                        """)
                    
                    query = " UNION ALL ".join(partition_queries)
            
            # Execute query with cost estimation
            try:
                job_config = QueryJobConfig(dry_run=True)
                dry_run_job = self.client.query(query, job_config=job_config)
                
                # Check estimated cost
                bytes_processed = dry_run_job.total_bytes_processed
                estimated_cost_usd = (bytes_processed / (1024**4)) * 5  # Rough estimate: $5 per TB
                
                if bytes_processed > 10 * (1024**3):  # > 10GB
                    logger.warning(f"Skipping query - too expensive: {bytes_processed / (1024**3):.2f} GB, "
                                 f"estimated cost: ${estimated_cost_usd:.4f}")
                    return []
                elif bytes_processed > 1024**3:  # > 1GB
                    logger.warning(f"Query will process {bytes_processed / (1024**3):.2f} GB, "
                                 f"estimated cost: ${estimated_cost_usd:.4f}")
                
                logger.info(f"Executing BigQuery sample query for {table_name}, estimated cost: ${estimated_cost_usd:.4f}")
                
            except Exception as e:
                logger.warning(f"Could not estimate query cost for {table_name}: {str(e)}, proceeding anyway")
            
            # Execute actual query
            try:
                query_job = self.client.query(query)
                results = query_job.result()
            except Exception as e:
                if "does not have bigquery.jobs.create permission" in str(e):
                    logger.warning(f"Cannot retrieve sample data from {table_name}: No permission to create jobs in project {self.project_id}. For public datasets, you need to provide your own project for running queries.")
                    return []
                else:
                    raise
            
            # Convert to list of dictionaries
            sample_data = []
            for row in results:
                sample_data.append(dict(row))
            
            logger.info(f"Retrieved {len(sample_data)} sample records from {table_name}")
            return sample_data
            
        except Exception as e:
            logger.error(f"Error getting partition-aware sample from {table_name}: {str(e)}")
            return []
    
    def get_table_schema(self, table_name: str, schema_name: str = None) -> Dict[str, str]:
        """Get BigQuery table schema - returns simple dict for backward compatibility"""
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            table = self.client.get_table(table_ref)
            
            schema = {}
            for field in table.schema:
                # Map BigQuery types to standard types
                bq_type = field.field_type
                if bq_type in ['STRING', 'BYTES']:
                    data_type = 'TEXT'
                elif bq_type in ['INTEGER', 'INT64']:
                    data_type = 'BIGINT'
                elif bq_type in ['FLOAT', 'FLOAT64']:
                    data_type = 'DOUBLE'
                elif bq_type == 'BOOLEAN':
                    data_type = 'BOOLEAN'
                elif bq_type in ['DATE', 'DATETIME', 'TIMESTAMP']:
                    data_type = bq_type
                elif bq_type == 'NUMERIC':
                    data_type = 'DECIMAL'
                else:
                    data_type = bq_type
                
                schema[field.name] = data_type
            
            return schema
            
        except Exception as e:
            logger.error(f"Error getting BigQuery table schema: {str(e)}")
            return {}
    
    def get_detailed_table_info(self, table_name: str, schema_name: str = None) -> Dict[str, Any]:
        """Get detailed BigQuery table information in ColumnInfo format"""
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            table = self.client.get_table(table_ref)
            
            columns = []
            for field in table.schema:
                # Map BigQuery types to standard types
                bq_type = field.field_type
                if bq_type in ['STRING', 'BYTES']:
                    data_type = 'TEXT'
                elif bq_type in ['INTEGER', 'INT64']:
                    data_type = 'BIGINT'
                elif bq_type in ['FLOAT', 'FLOAT64']:
                    data_type = 'DOUBLE'
                elif bq_type == 'BOOLEAN':
                    data_type = 'BOOLEAN'
                elif bq_type in ['DATE', 'DATETIME', 'TIMESTAMP']:
                    data_type = bq_type
                elif bq_type == 'NUMERIC':
                    data_type = 'DECIMAL'
                else:
                    data_type = bq_type
                
                # Create detailed column info
                column_info = {
                    "name": field.name,
                    "data_type": data_type,
                    "is_nullable": field.mode != "REQUIRED",
                    "default_value": None,  # BigQuery doesn't have traditional defaults
                    "is_primary_key": False,  # BigQuery doesn't have primary keys
                    "is_foreign_key": False,  # BigQuery doesn't have foreign keys
                    "foreign_key_table": None,
                    "foreign_key_column": None,
                    "is_unique": False,  # BigQuery doesn't enforce uniqueness
                    "character_maximum_length": None,
                    "numeric_precision": field.precision if hasattr(field, 'precision') else None,
                    "numeric_scale": field.scale if hasattr(field, 'scale') else None,
                    "comment": field.description or None
                }
                columns.append(column_info)
            
            return {
                "columns": columns,
                "indexes": [],  # BigQuery doesn't have traditional indexes
                "table_type": "BASE TABLE",
                "comment": table.description or None
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed BigQuery table info: {str(e)}")
            return {"columns": [], "indexes": [], "table_type": "BASE TABLE", "comment": None}
    
    def get_database_schemas(self) -> List[str]:
        """Get all datasets in the BigQuery project"""
        try:
            datasets = list(self.client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            error_msg = str(e)
            if "Access Denied" in error_msg:
                logger.warning(f"Access denied listing datasets in project '{self.project_id}': {error_msg}")
            else:
                logger.error(f"Error getting BigQuery datasets: {error_msg}")
            return []
    
    def _resolve_dataset_project(self, dataset_id: str) -> str:
        """
        Resolve which project contains the specified dataset.
        Returns the project ID where the dataset was found.
        Uses caching to avoid repeated lookups.
        """
        # Check cache first
        if dataset_id in self._dataset_project_cache:
            return self._dataset_project_cache[dataset_id]
        
        # First try the current project
        try:
            dataset_ref = self.client.dataset(dataset_id, project=self.project_id)
            # Test if dataset exists by listing with max_results=1
            list(self.client.list_tables(dataset_ref, max_results=1))
            self._dataset_project_cache[dataset_id] = self.project_id
            return self.project_id
        except Exception:
            pass
        
        # Try public data projects
        public_projects = ["bigquery-public-data", "bigquery-samples"]
        for public_project in public_projects:
            try:
                dataset_ref = self.client.dataset(dataset_id, project=public_project)
                # Test if dataset exists by listing with max_results=1
                list(self.client.list_tables(dataset_ref, max_results=1))
                self._dataset_project_cache[dataset_id] = public_project
                return public_project
            except Exception:
                continue
        
        # Default to current project if not found anywhere
        self._dataset_project_cache[dataset_id] = self.project_id
        return self.project_id
    
    def get_database_tables(self, schema_name: str = None, max_tables: int = 1000) -> List[str]:
        """Get all tables in the specified dataset with caching and pagination"""
        try:
            if not schema_name:
                # Return empty list if no dataset specified - BigQuery requires explicit dataset
                logger.warning("BigQuery requires dataset name to list tables")
                return []
            
            dataset_id = schema_name
            
            # Check cache first
            cache_key = f"{dataset_id}_tables"
            if cache_key in self._table_cache:
                logger.info(f"Returning cached tables for dataset '{dataset_id}'")
                return self._table_cache[cache_key]
            
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            
            try:
                dataset_ref = self.client.dataset(dataset_id, project=resolved_project)
                
                # Use pagination and limit for large datasets
                tables = []
                page_token = None
                total_fetched = 0
                
                while total_fetched < max_tables:
                    # Fetch a page of tables
                    page_size = min(100, max_tables - total_fetched)  # Max 100 per page
                    table_list = self.client.list_tables(
                        dataset_ref, 
                        max_results=page_size,
                        page_token=page_token
                    )
                    
                    page_tables = list(table_list)
                    if not page_tables:
                        break
                        
                    tables.extend(page_tables)
                    total_fetched += len(page_tables)
                    
                    # Get next page token
                    page_token = table_list.next_page_token
                    if not page_token:
                        break
                
                table_names = [table.table_id for table in tables]
                
                # Cache the results
                self._table_cache[cache_key] = table_names
                
                if resolved_project != self.project_id:
                    logger.info(f"Found {len(table_names)} tables in dataset '{dataset_id}' in public project '{resolved_project}' (max: {max_tables})")
                else:
                    logger.info(f"Found {len(table_names)} tables in dataset '{dataset_id}' in current project '{resolved_project}' (max: {max_tables})")
                    
                return table_names
            except Exception as e:
                logger.error(f"Error getting BigQuery tables for dataset '{schema_name}': {e}")
                return []
            
        except Exception as e:
            error_msg = str(e)
            if "is unlinked" in error_msg:
                logger.warning(f"Dataset '{schema_name}' is currently unlinked or unavailable: {error_msg}")
            elif "Access Denied" in error_msg:
                logger.warning(f"Access denied to dataset '{schema_name}': {error_msg}")
            else:
                logger.error(f"Error getting BigQuery tables for dataset '{schema_name}': {error_msg}")
            return []
    
    def get_row_count(self, table_name: str, schema_name: str = None, use_estimation: bool = True) -> Optional[int]:
        """Get row count for BigQuery table with partition awareness"""
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            if use_estimation:
                # Use table metadata for fast estimation
                table = self.client.get_table(table_ref)
                return table.num_rows
            else:
                # Exact count (expensive for large tables)
                query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
                query_job = self.client.query(query)
                result = list(query_job.result())[0]
                return result.count
                
        except Exception as e:
            logger.error(f"Error getting row count for {table_name}: {str(e)}")
            return None
    
    def check_query_cost(self, query: str, table_name: str, schema_name: str = None) -> Tuple[bool, str]:
        """Check BigQuery query cost before execution"""
        try:
            # Dry run to estimate cost
            job_config = QueryJobConfig(dry_run=True)
            try:
                dry_run_job = self.client.query(query, job_config=job_config)
            except Exception as e:
                if "does not have bigquery.jobs.create permission" in str(e):
                    logger.warning(f"Cannot estimate query cost: No permission to create jobs in project {self.project_id}")
                    return True, "Cannot estimate cost for public datasets"
                else:
                    raise
            
            bytes_processed = dry_run_job.total_bytes_processed
            estimated_cost_usd = (bytes_processed / (1024**4)) * 5  # $5 per TB
            
            # Set cost thresholds
            if bytes_processed > 10 * (1024**3):  # > 10GB
                return False, f"Query would process {bytes_processed / (1024**3):.2f} GB (estimated cost: ${estimated_cost_usd:.4f})"
            elif bytes_processed > 1024**3:  # > 1GB
                return True, f"Query will process {bytes_processed / (1024**3):.2f} GB (estimated cost: ${estimated_cost_usd:.4f})"
            else:
                return True, "Query appears to be safe"
                
        except Exception as e:
            logger.warning(f"Error analyzing BigQuery query cost: {str(e)}")
            return True, "Could not analyze query cost"
    
    def fetch_all(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute BigQuery query and return all results"""
        try:
            if params:
                # Handle parameterized queries
                for key, value in params.items():
                    query = query.replace(f":{key}", f"'{value}'")
            
            query_job = self.client.query(query)
            results = query_job.result()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error executing BigQuery query: {str(e)}")
            raise
    
    def fetch_one(self, query: str, params: Dict = None) -> Optional[Dict]:
        """Execute BigQuery query and return first result"""
        try:
            results = self.fetch_all(query, params)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error executing BigQuery query: {str(e)}")
            raise
    
    def close(self):
        """Close BigQuery connection - Modified for connection pooling"""
        # Only close if explicitly requested, not for temporary operations
        # BigQuery clients are designed to be reused and closed only when truly done
        if hasattr(self, '_force_close') and self._force_close and self.client:
            self.client.close()
            logger.info(f"Closed BigQuery connection to project: {self.project_id}")
        else:
            # Just log that we're keeping the connection alive for reuse
            logger.debug(f"Keeping BigQuery connection alive for project: {self.project_id}")
    
    def force_close(self):
        """Force close the BigQuery connection"""
        self._force_close = True
        self.close()
    
    def get_table_indexes(self, table_name: str, schema_name: str = None) -> List[Dict[str, Any]]:
        """
        Get table indexes for BigQuery. 
        BigQuery doesn't have traditional indexes, but returns clustering information.
        """
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            table = self.client.get_table(table_ref)
            
            indexes = []
            
            # Add clustering information as a pseudo-index
            if table.clustering_fields:
                indexes.append({
                    "name": f"{table_name}_clustering",
                    "columns": table.clustering_fields,
                    "type": "CLUSTERING",
                    "unique": False,
                    "primary": False
                })
            
            # Add partition information as a pseudo-index
            if table.time_partitioning and table.time_partitioning.field:
                indexes.append({
                    "name": f"{table_name}_partition",
                    "columns": [table.time_partitioning.field],
                    "type": "PARTITION",
                    "unique": False,
                    "primary": False
                })
            
            return indexes
            
        except Exception as e:
            logger.error(f"Error getting BigQuery table indexes: {str(e)}")
            return []
    
    def get_sample_data(self, table_name: str, schema_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get sample data from BigQuery table with cost-aware sampling.
        """
        try:
            if not schema_name:
                raise ValueError("BigQuery requires dataset name (schema_name parameter)")
            
            dataset_id = schema_name
            # Resolve which project contains this dataset
            resolved_project = self._resolve_dataset_project(dataset_id)
            table_ref = f"{resolved_project}.{dataset_id}.{table_name}"
            
            # Get table info to check if it's partitioned
            partition_info = self.get_partition_info(table_name, schema_name)
            
            if partition_info.get("is_partitioned"):
                # Use partition-aware sampling
                return self.get_partition_aware_sample(table_name, schema_name, limit, 1)
            else:
                # Use regular sampling for non-partitioned tables
                # Use a reasonable sample percentage
                sample_percentage = min(10, max(1, limit / 1000))
                
                query = f"""
                    SELECT * FROM `{table_ref}`
                    TABLESAMPLE SYSTEM ({sample_percentage} PERCENT)
                    LIMIT {limit}
                """
                
                # Check query cost first
                safe, message = self.check_query_cost(query, table_name, schema_name)
                if not safe:
                    logger.warning(f"Skipping sample data due to cost: {message}")
                    return []
                
                # Execute query
                try:
                    query_job = self.client.query(query)
                    results = query_job.result()
                except Exception as e:
                    if "does not have bigquery.jobs.create permission" in str(e):
                        logger.warning(f"Cannot retrieve sample data from {table_name}: No permission to create jobs in project {self.project_id}. For public datasets, you need to provide your own project for running queries.")
                        return []
                    else:
                        raise
                
                sample_data = []
                for row in results:
                    sample_data.append(dict(row))
                
                logger.info(f"Retrieved {len(sample_data)} sample records from {table_name}")
                return sample_data
                
        except Exception as e:
            logger.error(f"Error getting sample data from {table_name}: {str(e)}")
            return [] 