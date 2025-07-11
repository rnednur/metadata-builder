"""
Database router for connection management and schema inspection.
"""

import logging
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..models import (
    DatabaseConnectionRequest,
    DatabaseConnectionResponse,
    DatabaseSchemaResponse,
    TableListResponse,
    TableInfo,
    SchemaInfo,
    SchemaTableFilter,
    PredefinedSchemasRequest,
    ConnectionTestResponse,
    ErrorResponse,
    DatabaseType
)
from ..dependencies import get_connection_manager, ConnectionManager
from ...utils.database_handlers import get_database_handler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database", tags=["database"])


class CredentialRequest(BaseModel):
    """Request model for providing connection credentials."""
    password: str = None
    credentials_json: str = None


class CredentialStatusResponse(BaseModel):
    """Response model for credential status."""
    connection_name: str
    has_credentials: bool
    credential_type: str  # "password", "json", or "none"
    message: str


def filter_tables_by_config(table_names: List[str], filter_config: Dict[str, Any]) -> List[str]:
    """
    Filter table names based on schema table filter configuration.
    
    Args:
        table_names: List of all table names in the schema
        filter_config: Schema filter configuration dict
        
    Returns:
        Filtered list of table names
    """
    if not filter_config.get("enabled", True):
        return []
    
    filtered_tables = table_names.copy()
    
    # Step 1: If specific tables are listed, use only those
    specific_tables = filter_config.get("tables", [])
    if specific_tables:
        filtered_tables = [t for t in filtered_tables if t in specific_tables]
    
    # Step 2: Apply inclusion patterns
    inclusion_patterns = filter_config.get("table_patterns", [])
    if inclusion_patterns:
        pattern_matched_tables = []
        for table in filtered_tables:
            for pattern in inclusion_patterns:
                try:
                    if re.match(pattern, table):
                        pattern_matched_tables.append(table)
                        break
                except re.error:
                    logger.warning(f"Invalid regex pattern: {pattern}")
        filtered_tables = pattern_matched_tables
    
    # Step 3: Remove excluded tables
    excluded_tables = filter_config.get("excluded_tables", [])
    if excluded_tables:
        filtered_tables = [t for t in filtered_tables if t not in excluded_tables]
    
    # Step 4: Apply exclusion patterns
    exclusion_patterns = filter_config.get("excluded_patterns", [])
    if exclusion_patterns:
        for pattern in exclusion_patterns:
            try:
                filtered_tables = [t for t in filtered_tables if not re.match(pattern, t)]
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
    
    return filtered_tables


@router.post("/connections", response_model=DatabaseConnectionResponse)
async def create_connection(
    connection: DatabaseConnectionRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> DatabaseConnectionResponse:
    """
    Create a new user database connection.
    """
    try:
        # Check if connection already exists for this user
        if conn_manager.connection_exists(connection.name):
            raise HTTPException(
                status_code=400,
                detail=f"Connection '{connection.name}' already exists"
            )
        
        # Create connection configuration
        config = {
            "type": connection.type.value,
            "host": connection.host,
            "port": connection.port,
            "username": connection.username,
            "password": connection.password,
            "database": connection.database,
            "password_strategy": "session"  # Default to session strategy
        }
        
        # Add database-specific fields
        if connection.service_name:
            config["service_name"] = connection.service_name
        if connection.sid:
            config["sid"] = connection.sid
        if connection.tns_name:
            config["tns_name"] = connection.tns_name
        # BigQuery specific handling
        if connection.type == DatabaseType.BIGQUERY:
            # Ensure required project_id
            if not connection.project_id:
                raise HTTPException(status_code=400, detail="project_id is required for BigQuery connections")

            # Provide defaults for columns that are NOT NULL in the schema
            # These will not actually be used to connect but satisfy the constraint.
            config["host"] = connection.host or "bigquery.google.com"
            config["port"] = connection.port or 443
            config["username"] = connection.username or "service-account"

            # Store BQ-specific fields in connection_params so they persist
            config["connection_params"] = {
                "project_id": connection.project_id,
            }
            if connection.credentials_path:
                config["connection_params"]["credentials_path"] = connection.credentials_path
            if connection.predefined_schemas:
                config["connection_params"]["predefined_schemas"] = connection.predefined_schemas
        else:
            # Generic extras
            if connection.project_id:
                config["project_id"] = connection.project_id
            if connection.credentials_path:
                config["credentials_path"] = connection.credentials_path
            if connection.predefined_schemas:
                config["predefined_schemas"] = connection.predefined_schemas
        
        # Save as user connection to database
        connection_id = conn_manager.add_user_connection(connection.name, config)
        
        return DatabaseConnectionResponse(
            name=connection.name,
            type=connection.type.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            created_at=datetime.now(),
            status="active"
        )
        
    except ValueError as e:
        logger.error(f"Validation error creating connection '{connection.name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create connection '{connection.name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=List[DatabaseConnectionResponse])
async def list_connections(
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> List[DatabaseConnectionResponse]:
    """
    List all accessible database connections (user + system + config).
    """
    try:
        connections = []
        for name, config in conn_manager.get_all_connections().items():
            # Add connection source information
            connection_source = config.get("connection_source", "unknown")
            description = config.get("description", "")
            if connection_source != "config":
                description = f"[{connection_source.upper()}] {description}".strip()
            
            connections.append(DatabaseConnectionResponse(
                name=name,
                type=config.get("type", "unknown"),
                host=config.get("host"),
                port=config.get("port"),
                database=config.get("database", config.get("database_name")),
                created_at=datetime.now(),  # TODO: Use actual creation time from database
                status="active",
                description=description
            ))
        
        return connections
        
    except Exception as e:
        logger.error(f"Failed to list connections: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_name}", response_model=DatabaseConnectionResponse)
async def get_connection(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> DatabaseConnectionResponse:
    """
    Get details of a specific database connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        config = conn_manager.get_connection(connection_name)
        
        return DatabaseConnectionResponse(
            name=connection_name,
            type=config.get("type", "unknown"),
            host=config.get("host"),
            port=config.get("port"),
            database=config.get("database"),
            created_at=datetime.now(),
            status="active"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_name}")
async def delete_connection(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, str]:
    """
    Delete a user database connection (only user connections can be deleted).
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Check if it's a user connection (only these can be deleted)
        user_connections = conn_manager.get_user_connections()
        if connection_name not in user_connections:
            raise HTTPException(
                status_code=403,
                detail=f"Connection '{connection_name}' cannot be deleted (not a user connection)"
            )
        
        conn_manager.remove_connection(connection_name)
        
        return {"message": f"Connection '{connection_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error deleting connection '{connection_name}': {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete connection '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_name}/test", response_model=ConnectionTestResponse)
async def test_connection(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> ConnectionTestResponse:
    """
    Test a database connection.
    """
    start_time = time.time()
    
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Get connection configuration with cached credentials
        config = conn_manager.get_connection_with_credentials(connection_name)
        
        # Build connection testing logic based on DB type
        db_type = config.get("type")
        if db_type == "postgresql":
            connection_string = (
                f"postgresql://{config.get('username')}:{config.get('password')}@"
                f"{config.get('host')}:{config.get('port', 5432)}/{config.get('database')}"
            )

            # Test the connection via SQLAlchemy
            from sqlalchemy import create_engine, text
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()

                if not (row and row[0] == 1):
                    raise Exception("Invalid response from database")

            engine.dispose()

        elif db_type == "bigquery":
            # BigQuery connection test: run a simple query using the BigQuery client
            from google.cloud import bigquery
            from google.oauth2 import service_account
            import json

            project_id = config.get("project_id") or config.get("connection_params", {}).get("project_id")
            credentials_path = (
                config.get("credentials_path") or
                config.get("connection_params", {}).get("credentials_path")
            )

            if not project_id:
                raise Exception("BigQuery project_id is required for testing")
            
            if not credentials_path:
                raise Exception("BigQuery service account credentials are required. Please provide credentials first using the credentials endpoint.")

            if credentials_path:
                if credentials_path.strip().startswith("{"):
                    # Raw JSON content
                    credentials_info = json.loads(credentials_path)
                    credentials = service_account.Credentials.from_service_account_info(credentials_info)
                else:
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)

                client = bigquery.Client(project=project_id, credentials=credentials)
            else:
                # Attempt to use default credentials (e.g., Application Default Credentials)
                client = bigquery.Client(project=project_id)

            # For connection testing, try to list datasets instead of running a query
            # This avoids needing bigquery.jobs.create permission
            try:
                datasets = list(client.list_datasets(max_results=1))
                # If we can list datasets, the connection is working
            except Exception as list_error:
                # If listing datasets fails, try a simple query as fallback
                # This will work for projects where you have job creation permissions
                if "does not have bigquery.jobs.create permission" in str(list_error):
                    # For public datasets or read-only access, we can't run queries
                    # but if we got this far, the authentication is working
                    logger.info(f"BigQuery connection verified via authentication (read-only access to {project_id})")
                else:
                    # Try a query for projects where we have permissions
                    query_job = client.query("SELECT 1 AS test")
                    row = next(iter(query_job.result()))
                    if row[0] != 1:
                        raise Exception("Invalid response from BigQuery")

        else:
            raise Exception(f"Database type {db_type} not supported for testing yet")

        # If we reach here without exception, test succeeded
        response_time = (time.time() - start_time) * 1000
        return ConnectionTestResponse(
            connection_name=connection_name,
            status="success",
            message="Connection successful",
            response_time_ms=response_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Connection test failed for '{connection_name}': {str(e)}")
        
        return ConnectionTestResponse(
            connection_name=connection_name,
            status="failed",
            message=f"Connection failed: {str(e)}",
            response_time_ms=response_time
        )


@router.get("/connections/{connection_name}/schemas", response_model=DatabaseSchemaResponse)
async def get_database_schemas(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> DatabaseSchemaResponse:
    """
    Get all schemas and tables for a database connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Use unified database handler for schemas/tables
        from ...utils.database_handlers import get_database_handler

        handler = get_database_handler(connection_name, conn_manager)

        schemas_info = []
        total_tables = 0

        try:
            # Check for predefined schemas configuration
            config = conn_manager.get_connection(connection_name)
            predefined_schemas_config = config.get("predefined_schemas", {})
            
            # Support legacy comma-separated format for backward compatibility
            legacy_predefined_schemas = (
                config.get("connection_params", {}).get("predefined_schemas")
            )
            
            schemas_to_process = []
            
            if predefined_schemas_config and isinstance(predefined_schemas_config, dict):
                # New advanced filtering system
                for schema_name, filter_config in predefined_schemas_config.items():
                    if filter_config.get("enabled", True):
                        schemas_to_process.append(schema_name)
                logger.info(f"Using advanced predefined schemas for '{connection_name}': {schemas_to_process}")
                uses_predefined = True
                schema_source = "advanced_predefined"
                
            elif legacy_predefined_schemas:
                # Legacy comma-separated format
                schemas_to_process = [schema.strip() for schema in legacy_predefined_schemas.split(",") if schema.strip()]
                logger.info(f"Using legacy predefined schemas for '{connection_name}': {schemas_to_process}")
                uses_predefined = True
                schema_source = "legacy_predefined"
                
            else:
                # Auto-discovery fallback
                schemas_to_process = handler.get_database_schemas()
                logger.info(f"Using auto-discovered schemas for '{connection_name}': {schemas_to_process}")
                uses_predefined = False
                schema_source = "auto_discovery"

            for schema_name in schemas_to_process:
                try:
                    # Get all tables for the schema
                    all_table_names = handler.get_database_tables(schema_name)
                    
                    # Apply filtering if advanced predefined config exists
                    if predefined_schemas_config and isinstance(predefined_schemas_config, dict):
                        filter_config = predefined_schemas_config.get(schema_name, {})
                        filtered_table_names = filter_tables_by_config(all_table_names, filter_config)
                        is_predefined = True
                        filter_config_obj = filter_config
                    else:
                        # No filtering, use all tables
                        filtered_table_names = all_table_names
                        is_predefined = bool(legacy_predefined_schemas)
                        filter_config_obj = None
                    
                except Exception as e:
                    logger.warning(
                        f"Failed to get tables for schema '{schema_name}' in '{connection_name}': {str(e)}"
                    )
                    filtered_table_names = []
                    is_predefined = bool(predefined_schemas_config or legacy_predefined_schemas)
                    filter_config_obj = None

                schemas_info.append(
                    SchemaInfo(
                        schema_name=schema_name,
                        table_count=len(filtered_table_names),
                        tables=filtered_table_names,
                        is_predefined=is_predefined,
                        filter_config=SchemaTableFilter(**filter_config_obj) if filter_config_obj else None
                    )
                )
                total_tables += len(filtered_table_names)

            return DatabaseSchemaResponse(
                database_name=connection_name,
                schemas=schemas_info,
                total_tables=total_tables,
                uses_predefined_schemas=uses_predefined,
                schema_source=schema_source
            )

        finally:
            # Don't close connection - let handler cache manage lifecycle
            # The handler will reuse connections for better performance
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schemas for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_name}/schemas/{schema_name}/tables", response_model=TableListResponse)
async def get_schema_tables(
    connection_name: str,
    schema_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> TableListResponse:
    """
    Get detailed information about tables in a specific schema.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        db = get_database_handler(connection_name, conn_manager)
        try:
            tables_info = []
            
            # Get tables for the schema
            table_names = db.get_database_tables(schema_name)
            
            for table_name in table_names:
                if not table_name:
                    continue
                    
                try:
                    # Get table schema (columns)
                    table_schema = db.get_table_schema(table_name, schema_name)
                    
                    # Get row count (optional, might be slow for large tables)
                    row_count = None
                    try:
                        row_count = db.get_row_count(table_name, schema_name)
                    except Exception as e:
                        logger.warning(f"Could not get row count for {table_name}: {str(e)}")
                    
                    tables_info.append(TableInfo(
                        table_name=table_name,
                        schema_name=schema_name,
                        column_count=len(table_schema),
                        row_count=row_count,
                        columns=table_schema
                    ))
                    
                except Exception as e:
                    logger.warning(f"Failed to get info for table '{table_name}': {str(e)}")
                    # Continue with other tables
                    continue
            
            return TableListResponse(
                database_name=connection_name,
                schema_name=schema_name,
                tables=tables_info,
                total_count=len(tables_info)
            )
            
        finally:
            # Don't close connection - let handler cache manage lifecycle
            # The handler will reuse connections for better performance
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tables for '{connection_name}.{schema_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_name}/schemas/{schema_name}/tables/{table_name}", response_model=TableInfo)
async def get_table_info(
    connection_name: str,
    schema_name: str,
    table_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> TableInfo:
    """
    Get detailed information about a specific table.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        db = get_database_handler(connection_name, conn_manager)
        try:
            # Check if database handler supports detailed info (PostgreSQL)
            if hasattr(db, 'get_detailed_table_info'):
                # Use the new detailed method for PostgreSQL
                detailed_info = db.get_detailed_table_info(table_name, schema_name)
                
                if not detailed_info['columns']:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Table '{schema_name}.{table_name}' not found"
                    )
                
                # Get row count
                row_count = None
                try:
                    row_count = db.get_row_count(table_name, schema_name)
                except Exception as e:
                    logger.warning(f"Could not get row count for {table_name}: {str(e)}")
                
                return TableInfo(
                    table_name=table_name,
                    schema_name=schema_name,
                    column_count=len(detailed_info['columns']),
                    row_count=row_count,
                    columns=detailed_info['columns'],  # List of ColumnInfo objects
                    indexes=detailed_info['indexes'],   # List of IndexInfo objects
                    table_type=detailed_info['table_type'],
                    comment=detailed_info['comment']
                )
            else:
                # Fallback to old method for other databases  
                table_schema = db.get_table_schema(table_name, schema_name)
                
                if not table_schema:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Table '{schema_name}.{table_name}' not found"
                    )
                
                # Get row count
                row_count = None
                try:
                    row_count = db.get_row_count(table_name, schema_name)
                except Exception as e:
                    logger.warning(f"Could not get row count for {table_name}: {str(e)}")
                
                return TableInfo(
                    table_name=table_name,
                    schema_name=schema_name,
                    column_count=len(table_schema),
                    row_count=row_count,
                    columns=table_schema  # Dict[str, str] for backward compatibility
                )
            
        finally:
            # Don't close connection - let handler cache manage lifecycle
            # The handler will reuse connections for better performance
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table info for '{connection_name}.{schema_name}.{table_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_name}/credentials", response_model=CredentialStatusResponse)
async def get_credential_status(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> CredentialStatusResponse:
    """
    Check if a connection has cached credentials.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        config = conn_manager.get_connection(connection_name)
        db_type = config.get("type", "unknown")
        has_creds = conn_manager.has_cached_credentials(connection_name)
        
        if has_creds:
            cached_creds = conn_manager.get_cached_credentials(connection_name)
            if "password" in cached_creds:
                cred_type = "password"
                message = "Password is cached"
            elif "credentials_path" in cached_creds:
                cred_type = "json"
                message = "Service account credentials are cached"
            else:
                cred_type = "other"
                message = "Credentials are cached"
        else:
            if db_type == "bigquery":
                cred_type = "json"
                message = "BigQuery service account credentials required"
            else:
                cred_type = "password"
                message = "Database password required"
        
        return CredentialStatusResponse(
            connection_name=connection_name,
            has_credentials=has_creds,
            credential_type=cred_type,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credential status for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_name}/credentials", response_model=CredentialStatusResponse)
async def provide_credentials(
    connection_name: str,
    credentials: CredentialRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> CredentialStatusResponse:
    """
    Provide credentials for a connection and cache them temporarily.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        config = conn_manager.get_connection(connection_name)
        db_type = config.get("type", "unknown")
        
        # Prepare credentials to cache
        creds_to_cache = {}
        
        if db_type == "bigquery":
            if not credentials.credentials_json:
                raise HTTPException(
                    status_code=400,
                    detail="BigQuery requires service account credentials JSON"
                )
            
            # Validate JSON format
            try:
                json.loads(credentials.credentials_json)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid JSON format for service account credentials"
                )
            
            creds_to_cache["credentials_path"] = credentials.credentials_json
            cred_type = "json"
            message = "BigQuery service account credentials cached successfully"
            
        else:
            if not credentials.password:
                raise HTTPException(
                    status_code=400,
                    detail="Database password is required"
                )
            
            creds_to_cache["password"] = credentials.password
            cred_type = "password"
            message = "Database password cached successfully"
        
        # Cache the credentials
        conn_manager.cache_credentials(connection_name, creds_to_cache)
        
        return CredentialStatusResponse(
            connection_name=connection_name,
            has_credentials=True,
            credential_type=cred_type,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cache credentials for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_name}/credentials")
async def clear_credentials(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, str]:
    """
    Clear cached credentials for a connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        conn_manager.clear_cached_credentials(connection_name)
        
        return {"message": f"Credentials cleared for connection '{connection_name}'"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear credentials for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{connection_name}/predefined-schemas")
async def get_predefined_schemas(
    connection_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, Any]:
    """
    Get predefined schemas configuration for a connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        config = conn_manager.get_connection(connection_name)
        predefined_schemas = config.get("predefined_schemas", {})
        
        # Also get available schemas from the database for reference
        try:
            from ...utils.database_handlers import get_database_handler
            handler = get_database_handler(connection_name, conn_manager)
            available_schemas = handler.get_database_schemas()
        except Exception as e:
            logger.warning(f"Could not get available schemas: {e}")
            available_schemas = []
        
        return {
            "connection_name": connection_name,
            "predefined_schemas": predefined_schemas,
            "available_schemas": available_schemas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get predefined schemas for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/connections/{connection_name}/predefined-schemas")
async def update_predefined_schemas(
    connection_name: str,
    request: PredefinedSchemasRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, Any]:
    """
    Update predefined schemas configuration for a connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Get current connection to check if it's user or system connection
        config = conn_manager.get_connection(connection_name)
        connection_type = config.get("connection_type")
        
        if connection_type == "user":
            # Update user connection
            from ...auth.database import get_session
            from ...auth.models import UserConnection
            from sqlalchemy.orm import Session
            
            session: Session = next(get_session())
            try:
                user_conn = session.query(UserConnection).filter(
                    UserConnection.connection_name == connection_name,
                    UserConnection.user_id == config.get("user_id")
                ).first()
                
                if not user_conn:
                    raise HTTPException(status_code=404, detail="User connection not found")
                
                # Convert Pydantic models to dict for JSON storage
                predefined_schemas_dict = {}
                for schema_name, filter_config in request.predefined_schemas.items():
                    predefined_schemas_dict[schema_name] = filter_config.dict()
                
                user_conn.predefined_schemas = predefined_schemas_dict
                session.commit()
                
                # Update connection manager cache
                conn_manager.invalidate_connection_cache(connection_name)
                
                return {
                    "message": "Predefined schemas updated successfully",
                    "connection_name": connection_name,
                    "predefined_schemas": predefined_schemas_dict
                }
                
            finally:
                session.close()
                
        elif connection_type == "system":
            # Update system connection (admin only)
            from ...auth.database import get_session
            from ...auth.models import SystemConnection
            from sqlalchemy.orm import Session
            
            session: Session = next(get_session())
            try:
                system_conn = session.query(SystemConnection).filter(
                    SystemConnection.connection_name == connection_name
                ).first()
                
                if not system_conn:
                    raise HTTPException(status_code=404, detail="System connection not found")
                
                # Convert Pydantic models to dict for JSON storage
                predefined_schemas_dict = {}
                for schema_name, filter_config in request.predefined_schemas.items():
                    predefined_schemas_dict[schema_name] = filter_config.dict()
                
                system_conn.predefined_schemas = predefined_schemas_dict
                session.commit()
                
                # Update connection manager cache
                conn_manager.invalidate_connection_cache(connection_name)
                
                return {
                    "message": "Predefined schemas updated successfully",
                    "connection_name": connection_name,
                    "predefined_schemas": predefined_schemas_dict
                }
                
            finally:
                session.close()
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot update predefined schemas for config-based connections"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update predefined schemas for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/{connection_name}/predefined-schemas/{schema_name}")
async def add_schema_to_predefined(
    connection_name: str,
    schema_name: str,
    filter_config: SchemaTableFilter,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, Any]:
    """
    Add or update a specific schema in predefined schemas configuration.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Get current predefined schemas
        config = conn_manager.get_connection(connection_name)
        current_predefined = config.get("predefined_schemas", {})
        
        # Add/update the schema
        current_predefined[schema_name] = filter_config.dict()
        
        # Update using the existing endpoint logic
        request = PredefinedSchemasRequest(predefined_schemas={
            k: SchemaTableFilter(**v) if isinstance(v, dict) else v 
            for k, v in current_predefined.items()
        })
        
        return await update_predefined_schemas(connection_name, request, conn_manager)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add schema '{schema_name}' to predefined for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/connections/{connection_name}/predefined-schemas/{schema_name}")
async def remove_schema_from_predefined(
    connection_name: str,
    schema_name: str,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> Dict[str, Any]:
    """
    Remove a specific schema from predefined schemas configuration.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        # Get current predefined schemas
        config = conn_manager.get_connection(connection_name)
        current_predefined = config.get("predefined_schemas", {})
        
        if schema_name not in current_predefined:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{schema_name}' not found in predefined schemas"
            )
        
        # Remove the schema
        del current_predefined[schema_name]
        
        # Update using the existing endpoint logic
        request = PredefinedSchemasRequest(predefined_schemas={
            k: SchemaTableFilter(**v) if isinstance(v, dict) else v 
            for k, v in current_predefined.items()
        })
        
        result = await update_predefined_schemas(connection_name, request, conn_manager)
        result["message"] = f"Schema '{schema_name}' removed from predefined schemas"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove schema '{schema_name}' from predefined for '{connection_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 