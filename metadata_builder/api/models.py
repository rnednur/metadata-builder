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
    predefined_schemas: Optional[Dict[str, Any]] = Field(
        None, 
        description="Advanced schema and table filtering configuration"
    )
    legacy_predefined_schemas: Optional[str] = Field(
        None, 
        description="Legacy comma-separated list of schemas (deprecated, use predefined_schemas instead)",
        alias="predefined_schemas_legacy"
    )


class DatabaseConnectionResponse(BaseModel):
    """Response model for database connection operations."""
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    created_at: datetime
    status: str = "active"
    description: Optional[str] = None


class MetadataGenerationRequest(BaseModel):
    """Request model for generating table metadata.
    
    Note: Sample data is retrieved minimally for LLM processing during metadata generation.
    Full sample data is available through the dedicated sample data endpoint.
    """
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
    sample_size: int = Field(20, description="Sample size for each sample (minimal for LLM processing)", ge=1, le=10000)
    num_samples: int = Field(5, description="Number of samples to take (minimal for LLM processing)", ge=1, le=20)
    
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


class SchemaTableFilter(BaseModel):
    """Schema and table filtering configuration."""
    enabled: bool = Field(True, description="Whether this schema is enabled for metadata generation")
    tables: List[str] = Field(default_factory=list, description="Specific tables to include (empty means all tables)")
    excluded_tables: List[str] = Field(default_factory=list, description="Tables to exclude")
    table_patterns: List[str] = Field(default_factory=list, description="Regex patterns for table inclusion")
    excluded_patterns: List[str] = Field(default_factory=list, description="Regex patterns for table exclusion")
    description: Optional[str] = Field(None, description="Description of this schema configuration")


class PredefinedSchemasRequest(BaseModel):
    """Request model for updating predefined schemas configuration."""
    predefined_schemas: Dict[str, SchemaTableFilter] = Field(
        ..., 
        description="Schema filtering configuration",
        example={
            "public": {
                "enabled": True,
                "tables": ["users", "orders"],
                "excluded_tables": ["temp_table"],
                "table_patterns": ["user_.*", "order_.*"],
                "excluded_patterns": [".*_temp", ".*_backup"],
                "description": "Main application tables"
            },
            "analytics": {
                "enabled": True,
                "tables": [],
                "excluded_tables": [],
                "table_patterns": [],
                "excluded_patterns": [],
                "description": "Analytics and reporting tables"
            }
        }
    )


class SchemaInfo(BaseModel):
    """Schema information model."""
    schema_name: str
    table_count: int
    tables: List[str]
    is_predefined: bool = Field(False, description="Whether this schema is in predefined configuration")
    filter_config: Optional[SchemaTableFilter] = Field(None, description="Filtering configuration for this schema")


class ColumnInfo(BaseModel):
    """Detailed column information model."""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_table: Optional[str] = None
    foreign_key_column: Optional[str] = None
    is_unique: bool = False
    character_maximum_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None
    comment: Optional[str] = None


class IndexInfo(BaseModel):
    """Database index information model."""
    name: str
    columns: List[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: Optional[str] = None


class TableInfo(BaseModel):
    """Table information model."""
    table_name: str
    schema_name: str
    column_count: int
    row_count: Optional[int] = None
    columns: Union[Dict[str, str], List[ColumnInfo]]  # Support both old and new format
    indexes: Optional[List[IndexInfo]] = []
    table_type: Optional[str] = "table"  # table, view, materialized view
    comment: Optional[str] = None


class DatabaseSchemaResponse(BaseModel):
    """Response model for database schema information."""
    database_name: str
    schemas: List[SchemaInfo]
    total_tables: int
    uses_predefined_schemas: bool = False
    schema_source: str = "auto-discovery"  # "predefined" or "auto-discovery"


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


class MetadataUpdateRequest(BaseModel):
    """Request model for updating table metadata."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "db_name": "production_db",
                "table_name": "users",
                "schema_name": "public",
                "table_metadata": {
                    "description": "Updated description",
                    "domain": "Customer Data",
                    "category": "Transactional"
                },
                "column_metadata": {
                    "user_id": {
                        "description": "Unique identifier for users",
                        "business_name": "User ID"
                    }
                }
            }
        }
    }
    
    db_name: str = Field(..., description="Database connection name")
    table_name: str = Field(..., description="Name of the table")
    schema_name: str = Field("public", description="Schema name")
    table_metadata: Dict[str, Any] = Field({}, description="Table-level metadata updates")
    column_metadata: Dict[str, Dict[str, Any]] = Field({}, description="Column-level metadata updates")
    user_feedback: Optional[str] = Field(None, description="User feedback for AI-powered updates")


class MetadataUpdateResponse(BaseModel):
    """Response model for metadata updates."""
    database_name: str
    schema_name: str
    table_name: str
    updated_fields: List[str]
    success: bool
    message: str
    updated_at: datetime = Field(default_factory=datetime.now)


class AIMetadataUpdateRequest(BaseModel):
    """Request model for AI-powered metadata updates."""
    model_config = {
        "json_schema_extra": {
            "example": {
                "db_name": "production_db",
                "table_name": "users",
                "schema_name": "public",
                "current_metadata": {
                    "description": "User information table",
                    "domain": "Customer Data"
                },
                "user_feedback": "This table actually contains employee data, not customer data. Please update the description and domain accordingly.",
                "update_scope": "table_level"
            }
        }
    }
    
    db_name: str = Field(..., description="Database connection name")
    table_name: str = Field(..., description="Name of the table")
    schema_name: str = Field("public", description="Schema name")
    current_metadata: Dict[str, Any] = Field(..., description="Current metadata state")
    user_feedback: str = Field(..., description="User feedback for AI to process")
    update_scope: str = Field("table_level", description="Scope of update: 'table_level', 'column_level', or 'both'")
    target_column: Optional[str] = Field(None, description="Specific column to update (for column_level scope)")


class AIMetadataUpdateResponse(BaseModel):
    """Response model for AI-powered metadata updates."""
    database_name: str
    schema_name: str
    table_name: str
    suggested_updates: Dict[str, Any]
    explanation: str
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in the suggested updates")
    reasoning: str
    updated_at: datetime = Field(default_factory=datetime.now)


class StoredMetadata(BaseModel):
    """Model for stored metadata."""
    database_name: str
    schema_name: str
    table_name: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    created_by: Optional[str] = None
    updated_by: Optional[str] = None 