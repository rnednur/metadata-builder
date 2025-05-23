"""
Database router for connection management and schema inspection.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException, Depends
from ..models import (
    DatabaseConnectionRequest,
    DatabaseConnectionResponse,
    DatabaseSchemaResponse,
    TableListResponse,
    TableInfo,
    SchemaInfo,
    ConnectionTestResponse,
    ErrorResponse
)
from ..dependencies import get_connection_manager, ConnectionManager
from ...utils.database_handler import SQLAlchemyHandler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/database", tags=["database"])


@router.post("/connections", response_model=DatabaseConnectionResponse)
async def create_connection(
    connection: DatabaseConnectionRequest,
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> DatabaseConnectionResponse:
    """
    Create a new database connection.
    """
    try:
        # Check if connection already exists
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
            "database": connection.database
        }
        
        # Add database-specific fields
        if connection.service_name:
            config["service_name"] = connection.service_name
        if connection.sid:
            config["sid"] = connection.sid
        if connection.tns_name:
            config["tns_name"] = connection.tns_name
        if connection.project_id:
            config["project_id"] = connection.project_id
        if connection.credentials_path:
            config["credentials_path"] = connection.credentials_path
        
        # Save connection
        conn_manager.add_connection(connection.name, config)
        
        return DatabaseConnectionResponse(
            name=connection.name,
            type=connection.type.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            created_at=datetime.now(),
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Failed to create connection '{connection.name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections", response_model=List[DatabaseConnectionResponse])
async def list_connections(
    conn_manager: ConnectionManager = Depends(get_connection_manager)
) -> List[DatabaseConnectionResponse]:
    """
    List all database connections.
    """
    try:
        connections = []
        for name, config in conn_manager.get_all_connections().items():
            connections.append(DatabaseConnectionResponse(
                name=name,
                type=config.get("type", "unknown"),
                host=config.get("host"),
                port=config.get("port"),
                database=config.get("database"),
                created_at=datetime.now(),  # Note: we don't store creation time in config
                status="active"
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
    Delete a database connection.
    """
    try:
        if not conn_manager.connection_exists(connection_name):
            raise HTTPException(
                status_code=404,
                detail=f"Connection '{connection_name}' not found"
            )
        
        conn_manager.remove_connection(connection_name)
        
        return {"message": f"Connection '{connection_name}' deleted successfully"}
        
    except HTTPException:
        raise
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
        
        # Test the connection
        db = SQLAlchemyHandler(connection_name)
        try:
            # Try a simple query to test the connection
            result = db.fetch_one("SELECT 1 as test")
            if result and result.get('test') == 1:
                response_time = (time.time() - start_time) * 1000
                return ConnectionTestResponse(
                    connection_name=connection_name,
                    status="success",
                    message="Connection successful",
                    response_time_ms=response_time
                )
            else:
                raise Exception("Invalid response from database")
                
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Connection test failed for '{connection_name}': {str(e)}")
        
        return ConnectionTestResponse(
            connection_name=connection_name,
            status="failed",
            message="Connection failed",
            response_time_ms=response_time,
            error_details=str(e)
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
        
        db = SQLAlchemyHandler(connection_name)
        try:
            schemas_info = []
            total_tables = 0
            
            # Get all schemas
            schemas = db.get_schemas()
            
            for schema_name in schemas:
                try:
                    # Get tables for this schema
                    tables = db.get_tables(schema_name)
                    table_names = [table for table in tables if table]
                    
                    schemas_info.append(SchemaInfo(
                        schema_name=schema_name,
                        table_count=len(table_names),
                        tables=table_names
                    ))
                    
                    total_tables += len(table_names)
                    
                except Exception as e:
                    logger.warning(f"Failed to get tables for schema '{schema_name}': {str(e)}")
                    # Continue with other schemas
                    continue
            
            return DatabaseSchemaResponse(
                database_name=connection_name,
                schemas=schemas_info,
                total_tables=total_tables
            )
            
        finally:
            db.close()
            
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
        
        db = SQLAlchemyHandler(connection_name)
        try:
            tables_info = []
            
            # Get tables for the schema
            table_names = db.get_tables(schema_name)
            
            for table_name in table_names:
                if not table_name:
                    continue
                    
                try:
                    # Get table schema (columns)
                    table_schema = db.get_table_schema(table_name)
                    
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
            db.close()
            
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
        
        db = SQLAlchemyHandler(connection_name)
        try:
            # Get table schema (columns)
            table_schema = db.get_table_schema(table_name)
            
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
                columns=table_schema
            )
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table info for '{connection_name}.{schema_name}.{table_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 