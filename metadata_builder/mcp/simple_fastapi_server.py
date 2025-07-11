"""Simple FastAPI-based MCP-compatible server for Python 3.9 compatibility."""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# Use absolute imports for better compatibility
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from metadata_builder.core.generate_table_metadata import generate_complete_table_metadata
from metadata_builder.core.semantic_models import generate_lookml_model
from metadata_builder.config.config import load_config, get_db_handler

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Metadata Intelligence Server",
    description="MCP-compatible server for metadata operations using FastAPI",
    version="1.0.0"
)

# Pydantic models for type safety
class TableMetadataRequest(BaseModel):
    """Request model for table metadata."""
    database: str = Field(..., description="Database name to query")
    table: str = Field(..., description="Table name to analyze")
    schema: str = Field("public", description="Schema name (defaults to 'public')")
    include_samples: bool = Field(True, description="Include sample data in analysis")
    include_quality: bool = Field(True, description="Include data quality metrics")
    include_relationships: bool = Field(True, description="Include relationship analysis")

class TableSearchRequest(BaseModel):
    """Request model for table search operations."""
    query: str = Field(..., description="Search query (table name pattern or business term)")
    database: Optional[str] = Field(None, description="Specific database to search (optional)")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return (1-100)")

class MCPResponse(BaseModel):
    """Standard MCP response format."""
    content: List[Dict[str, Any]]
    isError: bool = False

# Global config
config = None

def get_config():
    """Get configuration singleton."""
    global config
    if config is None:
        try:
            config = load_config()
        except Exception:
            config = {"databases": {}}
    return config

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "Metadata Intelligence Server",
        "version": "1.0.0",
        "status": "running",
        "description": "FastAPI-based MCP-compatible server for metadata operations",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "tools": "/tools",
            "table_metadata": "/tools/get_table_metadata",
            "search_tables": "/tools/search_tables"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "python_version": "3.9+",
        "server_type": "FastAPI-MCP"
    }

@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    return {
        "tools": [
            {
                "name": "get_table_metadata",
                "description": "Get comprehensive metadata for a database table",
                "parameters": ["database", "table", "schema", "include_samples", "include_quality", "include_relationships"]
            },
            {
                "name": "search_tables", 
                "description": "Search for tables across databases using patterns",
                "parameters": ["query", "database", "limit"]
            },
            {
                "name": "get_schema_overview",
                "description": "Get overview of database schema structure",
                "parameters": ["database", "schema"]
            }
        ]
    }

@app.post("/tools/get_table_metadata", response_model=MCPResponse)
async def get_table_metadata(request: TableMetadataRequest):
    """
    Get comprehensive metadata for a database table.
    
    MCP-compatible endpoint that provides detailed information including:
    - Table schema and column definitions
    - Business context and descriptions  
    - Data quality metrics and statistics
    - Sample data and value distributions
    - Relationship analysis with other tables
    
    Perfect for AI agents that need to understand data structures
    before generating queries or performing analysis.
    """
    try:
        # Generate comprehensive metadata
        metadata = generate_complete_table_metadata(
            db_name=request.database,
            table_name=request.table,
            schema_name=request.schema,
            sample_size=100 if request.include_samples else 0,
            num_samples=3 if request.include_samples else 0,
            include_data_quality=request.include_quality,
            include_relationships=request.include_relationships
        )
        
        # Format for AI consumption
        summary = _format_metadata_for_ai(metadata)
        
        result_text = f"""Table Metadata for {request.database}.{request.schema}.{request.table}:

{summary}

Full metadata available in JSON format:
{json.dumps(metadata, indent=2, default=str)}"""
        
        return MCPResponse(
            content=[{
                "type": "text",
                "text": result_text
            }],
            isError=False
        )
        
    except Exception as e:
        logger.error(f"Error getting table metadata: {str(e)}")
        return MCPResponse(
            content=[{
                "type": "text", 
                "text": f"Error retrieving metadata for {request.database}.{request.table}: {str(e)}"
            }],
            isError=True
        )

@app.post("/tools/search_tables", response_model=MCPResponse)
async def search_tables(request: TableSearchRequest):
    """
    Search for tables across databases using patterns or business terms.
    
    MCP-compatible endpoint that helps AI agents discover relevant data sources by:
    - Searching table names with pattern matching
    - Finding tables related to business concepts
    - Providing contextual information about matches
    
    Returns a ranked list of matching tables with metadata.
    """
    try:
        config = get_config()
        results = []
        databases_to_search = [request.database] if request.database else list(config.get('databases', {}).keys())
        
        for db_name in databases_to_search:
            try:
                db = get_db_handler(db_name)
                tables = db.get_all_tables()
                
                # Pattern matching - could be enhanced with semantic search
                matching_tables = [
                    table for table in tables 
                    if request.query.lower() in table.lower()
                ][:request.limit]
                
                for table in matching_tables:
                    # Get basic metadata for context
                    try:
                        columns = db.get_table_schema(table)
                        results.append({
                            "database": db_name,
                            "table": table,
                            "columns": len(columns),
                            "match_reason": f"Name contains '{request.query}'",
                            "sample_columns": list(columns.keys())[:5]
                        })
                    except Exception:
                        results.append({
                            "database": db_name,
                            "table": table,
                            "match_reason": f"Name contains '{request.query}'"
                        })
                        
            except Exception as e:
                logger.error(f"Error searching database {db_name}: {str(e)}")
                
        # Format results
        if not results:
            result_text = f"No tables found matching '{request.query}'"
        else:
            result_text = f"Found {len(results)} tables matching '{request.query}':\n\n"
            for result in results[:request.limit]:
                result_text += f"📊 {result['database']}.{result['table']}"
                if 'columns' in result:
                    result_text += f" ({result['columns']} columns)"
                result_text += f"\n   Match: {result['match_reason']}\n"
                if 'sample_columns' in result:
                    result_text += f"   Columns: {', '.join(result['sample_columns'])}\n"
                result_text += "\n"
        
        return MCPResponse(
            content=[{
                "type": "text",
                "text": result_text
            }],
            isError=False
        )
        
    except Exception as e:
        logger.error(f"Error in table search: {str(e)}")
        return MCPResponse(
            content=[{
                "type": "text",
                "text": f"Error searching for tables: {str(e)}"
            }],
            isError=True
        )

@app.get("/tools/get_schema_overview")
async def get_schema_overview(database: str, schema: str = "public"):
    """
    Get a comprehensive overview of database schema structure.
    
    MCP-compatible endpoint that provides high-level information about:
    - All tables in the schema
    - Table sizes and column counts
    - Basic metadata for quick understanding
    - Relationships between tables (if detectable)
    
    Perfect for AI agents getting familiar with a new database.
    """
    try:
        db = get_db_handler(database)
        tables = db.get_all_tables(schema)
        
        overview = f"🗄️ Schema Overview for {database}.{schema}:\n\n"
        overview += f"📊 Total Tables: {len(tables)}\n\n"
        
        if not tables:
            overview += "No tables found in this schema."
        else:
            overview += "📋 Tables Summary:\n"
            
            table_details = []
            for table in tables[:50]:  # Limit to avoid overwhelming output
                try:
                    columns = db.get_table_schema(table, schema)
                    # Try to get row count (if supported)
                    try:
                        row_count_query = f"SELECT COUNT(*) as count FROM {schema}.{table}" if schema != "public" else f"SELECT COUNT(*) as count FROM {table}"
                        result = db.fetch_all(row_count_query)
                        row_count = result[0]['count'] if result else "Unknown"
                    except:
                        row_count = "Unknown"
                        
                    table_details.append({
                        "name": table,
                        "columns": len(columns),
                        "rows": row_count
                    })
                    
                except Exception as e:
                    table_details.append({
                        "name": table,
                        "error": str(e)
                    })
            
            # Sort by column count (most complex first)
            table_details.sort(key=lambda x: x.get('columns', 0), reverse=True)
            
            for detail in table_details:
                if 'error' in detail:
                    overview += f"  ❌ {detail['name']} (error: {detail['error']})\n"
                else:
                    overview += f"  📊 {detail['name']} - {detail['columns']} columns"
                    if detail['rows'] != "Unknown":
                        overview += f", {detail['rows']:,} rows"
                    overview += "\n"
                    
            if len(tables) > 50:
                overview += f"\n... and {len(tables) - 50} more tables (showing top 50 by complexity)"
        
        return MCPResponse(
            content=[{
                "type": "text",
                "text": overview
            }],
            isError=False
        )
        
    except Exception as e:
        logger.error(f"Error getting schema overview: {str(e)}")
        return MCPResponse(
            content=[{
                "type": "text",
                "text": f"Error retrieving schema overview: {str(e)}"
            }],
            isError=True
        )

def _format_metadata_for_ai(metadata: Dict[str, Any]) -> str:
    """Format metadata in a way that's optimized for AI understanding."""
    summary = []
    
    # Table overview
    table_desc = metadata.get('table_description', {})
    if table_desc:
        summary.append(f"🎯 PURPOSE: {table_desc.get('purpose', 'Unknown')}")
        summary.append(f"🏢 BUSINESS DOMAIN: {table_desc.get('business_domain', 'Unknown')}")
        
    # Column information
    columns = metadata.get('columns', {})
    if columns:
        summary.append(f"\n📊 COLUMNS ({len(columns)} total):")
        for col_name, col_info in list(columns.items())[:15]:  # Show top 15
            col_summary = f"  • **{col_name}** ({col_info.get('data_type', 'unknown')})"
            if col_info.get('description'):
                col_summary += f" - {col_info['description']}"
            if col_info.get('is_primary_key'):
                col_summary += " [PRIMARY KEY]"
            if col_info.get('is_foreign_key'):
                col_summary += " [FOREIGN KEY]"
            summary.append(col_summary)
        
        if len(columns) > 15:
            summary.append(f"  ... and {len(columns) - 15} more columns")
            
    # Data quality highlights
    quality_metrics = metadata.get('data_quality_metrics', {})
    if quality_metrics:
        summary.append(f"\n📊 DATA QUALITY HIGHLIGHTS:")
        for metric, value in list(quality_metrics.items())[:5]:
            summary.append(f"  • {metric}: {value}")
            
    # Key relationships
    relationships = metadata.get('relationships', {})
    if relationships:
        summary.append(f"\n🔗 KEY RELATIONSHIPS:")
        for rel_type, rel_info in relationships.items():
            if rel_info:
                summary.append(f"  • {rel_type}: {rel_info}")
            
    return "\n".join(summary)

# Entry point for running the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 