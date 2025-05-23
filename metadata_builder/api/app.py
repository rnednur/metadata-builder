"""
Main FastAPI application for the Metadata Builder API.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .models import HealthResponse, ErrorResponse
from .routers import database, metadata
from .dependencies import get_connection_manager, get_job_manager
from ..config.config import get_llm_api_config

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI app
    app = FastAPI(
        title="Metadata Builder API",
        description="""
        A comprehensive REST API for generating structured metadata from database tables 
        with LLM-enhanced capabilities.
        
        ## Features
        
        * **Database Connections**: Manage connections to various database types
        * **Schema Inspection**: Explore database schemas and tables
        * **Metadata Generation**: Generate rich table metadata with LLM analysis
        * **LookML Generation**: Create LookML semantic models automatically
        * **Background Jobs**: Long-running operations with status tracking
        * **Connection Testing**: Validate database connections
        
        ## Supported Databases
        
        * PostgreSQL
        * MySQL  
        * SQLite
        * Oracle
        * BigQuery
        * Kinetica
        * DuckDB
        
        ## Authentication
        
        API key authentication is required for LLM operations. Set your OpenAI API key
        in the environment variables or configuration.
        """,
        version="1.0.0",
        contact={
            "name": "Metadata Builder",
            "url": "https://github.com/rnednur/metadata-builder",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure this for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(database.router, prefix="/api/v1")
    app.include_router(metadata.router, prefix="/api/v1")
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.error(f"Unhandled exception in {request.url}: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                message="An unexpected error occurred",
                details={"exception": str(exc)} if app.debug else None
            ).dict()
        )
    
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint - redirect to docs."""
        return {
            "message": "Metadata Builder API",
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_url": "/health"
        }
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        try:
            # Check database connections
            conn_manager = get_connection_manager()
            connection_count = len(conn_manager.get_all_connections())
            
            # Check LLM API status
            llm_status = "not_configured"
            try:
                llm_config = get_llm_api_config()
                if llm_config.get('api_key'):
                    llm_status = "configured"
                else:
                    llm_status = "missing_api_key"
            except Exception as e:
                llm_status = f"error: {str(e)}"
            
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now(),
                version="1.0.0",
                database_connections=connection_count,
                llm_api_status=llm_status
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return HealthResponse(
                status="unhealthy",
                timestamp=datetime.now(),
                version="1.0.0",
                database_connections=0,
                llm_api_status=f"error: {str(e)}"
            )
    
    @app.get("/api/v1/info")
    async def api_info():
        """API information endpoint."""
        return {
            "name": "Metadata Builder API",
            "version": "1.0.0",
            "description": "REST API for database metadata generation and analysis",
            "supported_databases": [
                "postgresql",
                "mysql", 
                "sqlite",
                "oracle",
                "bigquery",
                "kinetica",
                "duckdb"
            ],
            "features": [
                "Database connection management",
                "Schema inspection",
                "Table metadata generation",
                "LookML semantic model generation",
                "Background job processing",
                "LLM-enhanced analysis"
            ],
            "endpoints": {
                "database_connections": "/api/v1/database/connections",
                "metadata_generation": "/api/v1/metadata/generate",
                "lookml_generation": "/api/v1/metadata/lookml/generate",
                "job_status": "/api/v1/metadata/jobs/{job_id}",
                "health": "/health",
                "docs": "/docs"
            }
        }
    
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        logger.info("Starting Metadata Builder API")
        
        # Initialize managers
        conn_manager = get_connection_manager()
        job_manager = get_job_manager()
        
        logger.info(f"Loaded {len(conn_manager.get_all_connections())} database connections")
        logger.info("Metadata Builder API started successfully")
    
    @app.on_event("shutdown") 
    async def shutdown_event():
        """Application shutdown event."""
        logger.info("Shutting down Metadata Builder API")
        
        # Clean up resources
        job_manager = get_job_manager()
        job_manager.cleanup_old_jobs()
        
        logger.info("Metadata Builder API shut down successfully")
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title="Metadata Builder API",
            version="1.0.0",
            description=app.description,
            routes=app.routes,
        )
        
        # Add custom schema elements
        openapi_schema["info"]["x-logo"] = {
            "url": "https://raw.githubusercontent.com/rnednur/metadata-builder/main/docs/logo.png"
        }
        
        # Add server information
        openapi_schema["servers"] = [
            {"url": "/", "description": "Current server"}
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Create the app instance
app = create_app() 