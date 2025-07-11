"""MCP Server implementation for metadata intelligence."""

import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from ..core.generate_table_metadata import generate_complete_table_metadata
from ..core.semantic_models import generate_lookml_model
from ..utils.database_handler import get_db_handler
from ..config.config import load_config

logger = logging.getLogger(__name__)


class MetadataMCPServer:
    """MCP Server for metadata intelligence and data context."""
    
    def __init__(self):
        self.server = Server("metadata-builder")
        self.config = load_config()
        self._setup_tools()
        self._setup_resources()
        
    def _setup_tools(self):
        """Register MCP tools for metadata operations."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """List available metadata tools."""
            return [
                types.Tool(
                    name="get_table_metadata",
                    description="Get comprehensive metadata for a database table including schema, statistics, business context, and data quality metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {"type": "string", "description": "Database name"},
                            "table": {"type": "string", "description": "Table name"},
                            "schema": {"type": "string", "description": "Schema name (optional)", "default": "public"},
                            "include_samples": {"type": "boolean", "description": "Include sample data", "default": True},
                            "include_quality": {"type": "boolean", "description": "Include data quality analysis", "default": True},
                            "include_relationships": {"type": "boolean", "description": "Include relationship analysis", "default": True}
                        },
                        "required": ["database", "table"]
                    }
                ),
                types.Tool(
                    name="search_tables",
                    description="Search for tables across databases based on name patterns or business context",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "query": {"type": "string", "description": "Search query (table name pattern or business term)"},
                            "database": {"type": "string", "description": "Specific database to search (optional)"},
                            "limit": {"type": "integer", "description": "Maximum results to return", "default": 20}
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="analyze_data_quality",
                    description="Analyze data quality metrics for tables or entire schemas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {"type": "string", "description": "Database name"},
                            "table": {"type": "string", "description": "Table name (optional - if not provided, analyzes entire database)"},
                            "schema": {"type": "string", "description": "Schema name (optional)", "default": "public"}
                        },
                        "required": ["database"]
                    }
                ),
                types.Tool(
                    name="get_schema_overview",
                    description="Get an overview of all tables in a database schema with basic metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {"type": "string", "description": "Database name"},
                            "schema": {"type": "string", "description": "Schema name (optional)", "default": "public"}
                        },
                        "required": ["database"]
                    }
                ),
                types.Tool(
                    name="generate_semantic_model",
                    description="Generate semantic models (LookML, dbt) for business intelligence and analytics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {"type": "string", "description": "Database name"},
                            "tables": {"type": "array", "items": {"type": "string"}, "description": "List of table names"},
                            "schema": {"type": "string", "description": "Schema name (optional)", "default": "public"},
                            "model_type": {"type": "string", "enum": ["lookml", "dbt"], "default": "lookml"},
                            "model_name": {"type": "string", "description": "Name for the generated model"}
                        },
                        "required": ["database", "tables", "model_name"]
                    }
                ),
                types.Tool(
                    name="explain_business_context",
                    description="Get business context and meaning for tables and columns using AI analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "database": {"type": "string", "description": "Database name"},
                            "table": {"type": "string", "description": "Table name"},
                            "column": {"type": "string", "description": "Column name (optional - if not provided, explains entire table)"},
                            "schema": {"type": "string", "description": "Schema name (optional)", "default": "public"}
                        },
                        "required": ["database", "table"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_table_metadata":
                    return await self._get_table_metadata(arguments)
                elif name == "search_tables":
                    return await self._search_tables(arguments)
                elif name == "analyze_data_quality":
                    return await self._analyze_data_quality(arguments)
                elif name == "get_schema_overview":
                    return await self._get_schema_overview(arguments)
                elif name == "generate_semantic_model":
                    return await self._generate_semantic_model(arguments)
                elif name == "explain_business_context":
                    return await self._explain_business_context(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [types.TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    def _setup_resources(self):
        """Register MCP resources for metadata access."""
        
        @self.server.list_resources()
        async def list_resources() -> List[types.Resource]:
            """List available metadata resources."""
            resources = []
            
            # Add database schemas as resources
            try:
                databases = self.config.get('databases', {})
                for db_name in databases.keys():
                    resources.append(types.Resource(
                        uri=f"metadata://databases/{db_name}/schema",
                        name=f"{db_name} Schema",
                        description=f"Complete schema information for {db_name} database",
                        mimeType="application/json"
                    ))
                    
                    resources.append(types.Resource(
                        uri=f"metadata://databases/{db_name}/quality-report",
                        name=f"{db_name} Quality Report",
                        description=f"Data quality assessment for {db_name} database",
                        mimeType="application/json"
                    ))
                    
            except Exception as e:
                logger.error(f"Error listing resources: {str(e)}")
                
            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read metadata resource content."""
            try:
                # Parse URI: metadata://databases/{db_name}/{resource_type}
                parts = uri.replace("metadata://databases/", "").split("/")
                if len(parts) != 2:
                    raise ValueError(f"Invalid resource URI: {uri}")
                    
                db_name, resource_type = parts
                
                if resource_type == "schema":
                    return await self._get_database_schema(db_name)
                elif resource_type == "quality-report":
                    return await self._get_quality_report(db_name)
                else:
                    raise ValueError(f"Unknown resource type: {resource_type}")
                    
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {str(e)}")
                return json.dumps({"error": str(e)})

    async def _get_table_metadata(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get comprehensive table metadata."""
        database = args["database"]
        table = args["table"]
        schema = args.get("schema", "public")
        include_samples = args.get("include_samples", True)
        include_quality = args.get("include_quality", True)
        include_relationships = args.get("include_relationships", True)
        
        # Generate comprehensive metadata
        metadata = generate_complete_table_metadata(
            db_name=database,
            table_name=table,
            schema_name=schema,
            sample_size=100 if include_samples else 0,
            num_samples=3 if include_samples else 0,
            include_data_quality=include_quality,
            include_relationships=include_relationships
        )
        
        # Format for AI consumption
        summary = self._format_metadata_for_ai(metadata)
        
        return [
            types.TextContent(
                type="text",
                text=f"Table Metadata for {database}.{schema}.{table}:\n\n{summary}"
            ),
            types.TextContent(
                type="text", 
                text=f"Full metadata (JSON):\n{json.dumps(metadata, indent=2)}"
            )
        ]

    async def _search_tables(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Search for tables across databases."""
        query = args["query"]
        database = args.get("database")
        limit = args.get("limit", 20)
        
        results = []
        databases_to_search = [database] if database else list(self.config.get('databases', {}).keys())
        
        for db_name in databases_to_search:
            try:
                db = get_db_handler(db_name)
                tables = db.get_all_tables()
                
                # Simple pattern matching for now
                matching_tables = [
                    table for table in tables 
                    if query.lower() in table.lower()
                ][:limit]
                
                for table in matching_tables:
                    results.append({
                        "database": db_name,
                        "table": table,
                        "match_reason": f"Name contains '{query}'"
                    })
                    
            except Exception as e:
                logger.error(f"Error searching database {db_name}: {str(e)}")
                
        search_summary = f"Found {len(results)} tables matching '{query}':\n\n"
        for result in results[:limit]:
            search_summary += f"• {result['database']}.{result['table']} - {result['match_reason']}\n"
            
        return [types.TextContent(type="text", text=search_summary)]

    async def _analyze_data_quality(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Analyze data quality for tables."""
        database = args["database"]
        table = args.get("table")
        schema = args.get("schema", "public")
        
        if table:
            # Analyze specific table
            metadata = generate_complete_table_metadata(
                db_name=database,
                table_name=table,
                schema_name=schema,
                include_data_quality=True
            )
            
            quality_metrics = metadata.get('data_quality_metrics', {})
            summary = f"Data Quality Analysis for {database}.{schema}.{table}:\n\n"
            
            for metric_name, metric_data in quality_metrics.items():
                summary += f"• {metric_name}: {metric_data}\n"
                
        else:
            # Analyze entire database/schema
            summary = f"Schema-wide quality analysis for {database}.{schema} - Feature coming soon!"
            
        return [types.TextContent(type="text", text=summary)]

    async def _get_schema_overview(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Get schema overview."""
        database = args["database"]
        schema = args.get("schema", "public")
        
        try:
            db = get_db_handler(database)
            tables = db.get_all_tables(schema)
            
            overview = f"Schema Overview for {database}.{schema}:\n\n"
            overview += f"Total Tables: {len(tables)}\n\n"
            
            for table in tables[:20]:  # Limit to first 20 tables
                try:
                    columns = db.get_table_schema(table, schema)
                    overview += f"• {table} ({len(columns)} columns)\n"
                except Exception as e:
                    overview += f"• {table} (error: {str(e)})\n"
                    
            if len(tables) > 20:
                overview += f"\n... and {len(tables) - 20} more tables"
                
        except Exception as e:
            overview = f"Error getting schema overview: {str(e)}"
            
        return [types.TextContent(type="text", text=overview)]

    async def _generate_semantic_model(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Generate semantic models."""
        database = args["database"]
        tables = args["tables"]
        schema = args.get("schema", "public")
        model_type = args.get("model_type", "lookml")
        model_name = args["model_name"]
        
        if model_type == "lookml":
            lookml_result = generate_lookml_model(
                db_name=database,
                schema_name=schema,
                table_names=tables,
                model_name=model_name
            )
            
            summary = f"Generated LookML model '{model_name}' for tables: {', '.join(tables)}\n\n"
            summary += f"Model includes:\n"
            
            if 'view_files' in lookml_result:
                summary += f"• {len(lookml_result['view_files'])} view files\n"
            if 'model_file' in lookml_result:
                summary += f"• 1 model file\n"
                
            return [
                types.TextContent(type="text", text=summary),
                types.TextContent(type="text", text=f"Full LookML:\n{json.dumps(lookml_result, indent=2)}")
            ]
        else:
            return [types.TextContent(type="text", text="dbt model generation coming soon!")]

    async def _explain_business_context(self, args: Dict[str, Any]) -> List[types.TextContent]:
        """Explain business context for tables/columns."""
        database = args["database"]
        table = args["table"]
        column = args.get("column")
        schema = args.get("schema", "public")
        
        # Get metadata with business context
        metadata = generate_complete_table_metadata(
            db_name=database,
            table_name=table,
            schema_name=schema,
            include_additional_insights=True
        )
        
        if column:
            # Explain specific column
            column_info = metadata.get('columns', {}).get(column, {})
            explanation = f"Business Context for {database}.{schema}.{table}.{column}:\n\n"
            explanation += f"Description: {column_info.get('description', 'No description available')}\n"
            explanation += f"Data Type: {column_info.get('data_type', 'Unknown')}\n"
            explanation += f"Business Name: {column_info.get('business_name', 'Not specified')}\n"
        else:
            # Explain entire table
            table_desc = metadata.get('table_description', {})
            explanation = f"Business Context for {database}.{schema}.{table}:\n\n"
            explanation += f"Purpose: {table_desc.get('purpose', 'No purpose description available')}\n"
            explanation += f"Business Domain: {table_desc.get('business_domain', 'Not specified')}\n"
            
        return [types.TextContent(type="text", text=explanation)]

    def _format_metadata_for_ai(self, metadata: Dict[str, Any]) -> str:
        """Format metadata in a way that's easy for AI to understand and use."""
        summary = []
        
        # Table overview
        table_desc = metadata.get('table_description', {})
        if table_desc:
            summary.append(f"PURPOSE: {table_desc.get('purpose', 'Unknown')}")
            summary.append(f"BUSINESS DOMAIN: {table_desc.get('business_domain', 'Unknown')}")
            
        # Column information
        columns = metadata.get('columns', {})
        if columns:
            summary.append(f"\nCOLUMNS ({len(columns)} total):")
            for col_name, col_info in columns.items():
                col_summary = f"  • {col_name} ({col_info.get('data_type', 'unknown')})"
                if col_info.get('description'):
                    col_summary += f" - {col_info['description']}"
                summary.append(col_summary)
                
        # Data quality
        quality_metrics = metadata.get('data_quality_metrics', {})
        if quality_metrics:
            summary.append(f"\nDATA QUALITY:")
            for metric, value in quality_metrics.items():
                summary.append(f"  • {metric}: {value}")
                
        return "\n".join(summary)

    async def _get_database_schema(self, db_name: str) -> str:
        """Get complete database schema information."""
        try:
            db = get_db_handler(db_name)
            tables = db.get_all_tables()
            
            schema_info = {
                "database": db_name,
                "tables": [],
                "generated_at": datetime.now().isoformat()
            }
            
            for table in tables:
                try:
                    columns = db.get_table_schema(table)
                    schema_info["tables"].append({
                        "name": table,
                        "columns": columns
                    })
                except Exception as e:
                    logger.error(f"Error getting schema for table {table}: {str(e)}")
                    
            return json.dumps(schema_info, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _get_quality_report(self, db_name: str) -> str:
        """Get data quality report for database."""
        # This would implement comprehensive quality analysis
        # For now, return a placeholder
        return json.dumps({
            "database": db_name,
            "quality_summary": "Quality analysis feature coming soon",
            "generated_at": datetime.now().isoformat()
        })

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Metadata MCP Server")
        async with stdio_server() as streams:
            await self.server.run(
                streams[0], streams[1],
                self.server.create_initialization_options()
            )


# CLI entry point for MCP server
async def main():
    """Main entry point for MCP server."""
    import asyncio
    server = MetadataMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 