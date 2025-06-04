"""
Pydantic models for the Metadata Builder API.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class DatabaseType(str, Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    BIGQUERY = "bigquery"
    KINETICA = "kinetica"
    DUCKDB = "duckdb"


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    YAML = "yaml"


class DatabaseConnectionRequest(BaseModel):
    """Request model for creating a database connection."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "production_db",
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "user",
                "password": "password",
                "database": "mydb"
            }
        }
    }
    
    name: str = Field(..., description="Unique name for the database connection")
    type: DatabaseType = Field(..., description="Type of database")
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    username: Optional[str] = Field(None, description="Database username")
    password: Optional[str] = Field(None, description="Database password")
    database: Optional[str] = Field(None, description="Database name")
    service_name: Optional[str] = Field(None, description="Oracle service name")
    sid: Optional[str] = Field(None, description="Oracle SID")
    tns_name: Optional[str] = Field(None, description="Oracle TNS name")
    project_id: Optional[str] = Field(None, description="BigQuery project ID")
    credentials_path: Optional[str] = Field(None, description="Path to credentials file")


class DatabaseConnectionResponse(BaseModel):
    """Response model for database connection operations."""
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    created_at: datetime
    status: str = "active"


class MetadataGenerationRequest(BaseModel):
    """Request model for generating table metadata."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "db_name": "production_db",
                "table_name": "users",
                "schema_name": "public",
                "sample_size": 100,
                "num_samples": 5,
                "max_partitions": 10
            }
        }
    }
    
    db_name: str = Field(..., description="Database connection name")
    table_name: str = Field(..., description="Name of the table to analyze")
    schema_name: str = Field("public", description="Schema name")
    analysis_sql: Optional[str] = Field(None, description="Custom SQL query for analysis")
    sample_size: int = Field(100, description="Sample size for each sample", ge=1, le=10000)
    num_samples: int = Field(5, description="Number of samples to take", ge=1, le=20)
    
    # BigQuery partition-specific options
    max_partitions: int = Field(10, description="Maximum number of partitions to sample from (BigQuery)", ge=1, le=100)
    
    # Optional sections - can be disabled to save time/cost
    include_relationships: bool = Field(True, description="Include relationship analysis")
    include_aggregation_rules: bool = Field(True, description="Include aggregation rules")
    include_query_rules: bool = Field(True, description="Include query rules")
    include_data_quality: bool = Field(True, description="Include data quality metrics")
    include_query_examples: bool = Field(True, description="Include query examples")
    include_additional_insights: bool = Field(True, description="Include additional insights")
    include_business_rules: bool = Field(True, description="Include business rules")
    include_categorical_definitions: bool = Field(True, description="Include categorical definitions")


class LookMLGenerationRequest(BaseModel):
    """Request model for generating LookML semantic models."""
    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "db_name": "production_db",
                "schema_name": "public",
                "table_names": ["users", "orders"],
                "model_name": "user_analytics_model",
                "include_explores": True
            }
        }
    }
    
    db_name: str = Field(..., description="Database connection name")
    schema_name: str = Field("public", description="Schema name")
    table_names: List[str] = Field(..., description="List of table names to include")
    model_name: str = Field(..., description="Name for the LookML model")
    include_derived_tables: bool = Field(False, description="Include derived table suggestions")
    include_explores: bool = Field(True, description="Include explore definitions")
    additional_prompt: Optional[str] = Field(None, description="Additional requirements for generation")
    generation_type: str = Field("full", description="Type of generation ('full' or 'append')")
    existing_lookml: Optional[str] = Field(None, description="Existing LookML when appending")
    token_threshold: Optional[int] = Field(8000, description="Maximum token count for metadata")


class SchemaInfo(BaseModel):
    """Schema information model."""
    schema_name: str
    table_count: int
    tables: List[str]


class TableInfo(BaseModel):
    """Table information model."""
    table_name: str
    schema_name: str
    column_count: int
    row_count: Optional[int] = None
    columns: Dict[str, str]  # column_name -> column_type


class DatabaseSchemaResponse(BaseModel):
    """Response model for database schema information."""
    database_name: str
    schemas: List[SchemaInfo]
    total_tables: int


class ProcessingStats(BaseModel):
    """Processing statistics model."""
    total_duration_seconds: float
    start_time: datetime
    end_time: datetime
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None


class MetadataResponse(BaseModel):
    """Response model for generated metadata."""
    database_name: str
    schema_name: str
    table_name: str
    metadata: Dict[str, Any]
    processing_stats: ProcessingStats
    format: OutputFormat = OutputFormat.JSON


class LookMLResponse(BaseModel):
    """Response model for generated LookML."""
    model_config = {"protected_namespaces": ()}
    
    model_name: str
    database_name: str
    schema_name: str
    table_names: List[str]
    lookml_content: Dict[str, Any]
    processing_stats: ProcessingStats


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    database_connections: int
    llm_api_status: str


class TableListResponse(BaseModel):
    """Response model for listing tables."""
    database_name: str
    schema_name: str
    tables: List[TableInfo]
    total_count: int


class ConnectionTestResponse(BaseModel):
    """Response model for testing database connections."""
    connection_name: str
    status: str
    message: str
    response_time_ms: Optional[float] = None
    error_details: Optional[str] = None


class BackgroundJobResponse(BaseModel):
    """Response model for background job status."""
    job_id: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    updated_at: datetime
    progress: Optional[float] = None  # 0.0 to 1.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobStatusRequest(BaseModel):
    """Request model for job status queries."""
    job_id: str 