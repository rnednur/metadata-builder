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

logger = logging.getLogger(__name__)

class BigQueryHandler(DatabaseHandler):
    """BigQuery-specific implementation with partition awareness"""
    
    def __init__(self, db_name: str = None):
        super().__init__(db_name)
        self.client = None
        self.project_id = None
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
            
            self.project_id = self.config.get('project_id')
            credentials_path = self.config.get('credentials_path')
            
            if not self.project_id:
                raise ValueError("BigQuery project_id is required")
            
            # Initialize BigQuery client
            if credentials_path:
                self.client = bigquery.Client.from_service_account_json(
                    credentials_path, project=self.project_id
                )
            else:
                # Use default credentials (e.g., from environment)
                self.client = bigquery.Client(project=self.project_id)
            
            logger.info(f"Successfully connected to BigQuery project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to BigQuery {self.db_name}: {str(e)}")
            raise
    
    def get_partition_info(self, table_name: str, schema_name: str = None) -> Dict[str, Any]:
        """
        Get partition information for a BigQuery table.
        
        Returns:
            Dictionary with partition information including type, column, and available partitions
        """
        try:
            dataset_id = schema_name or 'public'
            table_ref = f"{self.project_id}.{dataset_id}.{table_name}"
            
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
                    FROM `{self.project_id}.{dataset_id}.INFORMATION_SCHEMA.PARTITIONS`
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
            dataset_id = schema_name or 'public'
            table_ref = f"{self.project_id}.{dataset_id}.{table_name}"
            
            # Get partition information
            partition_info = self.get_partition_info(table_name, schema_name)
            
            if not partition_info["is_partitioned"]:
                # Non-partitioned table - use standard sampling
                query = f"""
                    SELECT * FROM `{table_ref}`
                    TABLESAMPLE SYSTEM ({sample_size * num_samples} PERCENT)
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
            job_config = QueryJobConfig(dry_run=True)
            dry_run_job = self.client.query(query, job_config=job_config)
            
            # Check estimated cost
            bytes_processed = dry_run_job.total_bytes_processed
            estimated_cost_usd = (bytes_processed / (1024**4)) * 5  # Rough estimate: $5 per TB
            
            if bytes_processed > 1024**3:  # > 1GB
                logger.warning(f"Query will process {bytes_processed / (1024**3):.2f} GB, "
                             f"estimated cost: ${estimated_cost_usd:.4f}")
            
            # Execute actual query
            query_job = self.client.query(query)
            results = query_job.result()
            
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
        """Get BigQuery table schema"""
        try:
            dataset_id = schema_name or 'public'
            table_ref = f"{self.project_id}.{dataset_id}.{table_name}"
            
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
    
    def get_database_schemas(self) -> List[str]:
        """Get all datasets in the BigQuery project"""
        try:
            datasets = list(self.client.list_datasets())
            return [dataset.dataset_id for dataset in datasets]
        except Exception as e:
            logger.error(f"Error getting BigQuery datasets: {str(e)}")
            return []
    
    def get_database_tables(self, schema_name: str = None) -> List[str]:
        """Get all tables in the specified dataset"""
        try:
            dataset_id = schema_name or 'public'
            dataset_ref = self.client.dataset(dataset_id)
            tables = list(self.client.list_tables(dataset_ref))
            return [table.table_id for table in tables]
        except Exception as e:
            logger.error(f"Error getting BigQuery tables: {str(e)}")
            return []
    
    def get_row_count(self, table_name: str, schema_name: str = None, use_estimation: bool = True) -> Optional[int]:
        """Get row count for BigQuery table with partition awareness"""
        try:
            dataset_id = schema_name or 'public'
            table_ref = f"{self.project_id}.{dataset_id}.{table_name}"
            
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
            dry_run_job = self.client.query(query, job_config=job_config)
            
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
        """Close BigQuery connection"""
        if self.client:
            self.client.close()
            logger.info(f"Closed BigQuery connection to project: {self.project_id}") 