"""FastMCP Server implementation for metadata intelligence - Superior to traditional MCP."""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from ..core.generate_table_metadata import generate_complete_table_metadata
from ..core.semantic_models import generate_lookml_model
from ..utils.database_handler import get_db_handler
from ..config.config import load_config

logger = logging.getLogger(__name__)

# Pydantic models for type safety and auto-documentation
class TableMetadataRequest(BaseModel):
    """Request model for table metadata with validation and documentation."""
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

class QualityAnalysisRequest(BaseModel):
    """Request model for data quality analysis."""
    database: str = Field(..., description="Database name to analyze")
    table: Optional[str] = Field(None, description="Table name (optional - analyzes entire database if not provided)")
    schema: str = Field("public", description="Schema name")

class SchemaOverviewRequest(BaseModel):
    """Request model for schema overview."""
    database: str = Field(..., description="Database name")
    schema: str = Field("public", description="Schema name")

class SemanticModelRequest(BaseModel):
    """Request model for semantic model generation."""
    database: str = Field(..., description="Database name")
    tables: List[str] = Field(..., description="List of table names to include in model")
    schema: str = Field("public", description="Schema name")
    model_type: str = Field("lookml", regex="^(lookml|dbt)$", description="Type of semantic model")
    model_name: str = Field(..., description="Name for the generated model")

class BusinessContextRequest(BaseModel):
    """Request model for business context explanation."""
    database: str = Field(..., description="Database name")
    table: str = Field(..., description="Table name")
    column: Optional[str] = Field(None, description="Column name (optional - explains entire table if not provided)")
    schema: str = Field("public", description="Schema name")


class MetadataFastMCPServer:
    """FastMCP Server for metadata intelligence - Modern, type-safe, and performant."""
    
    def __init__(self):
        self.app = FastMCP("Metadata Intelligence Server")
        self.config = load_config()
        self._setup_tools()
        self._setup_resources()
        
    def _setup_tools(self):
        """Register FastMCP tools with automatic documentation and type safety."""
        
        @self.app.tool()
        async def get_table_metadata(request: TableMetadataRequest) -> str:
            """
            Get comprehensive metadata for a database table.
            
            Provides detailed information including:
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
                summary = self._format_metadata_for_ai(metadata)
                
                return f"""Table Metadata for {request.database}.{request.schema}.{request.table}:

{summary}

Full metadata available in JSON format:
{json.dumps(metadata, indent=2, default=str)}"""
                
            except Exception as e:
                logger.error(f"Error getting table metadata: {str(e)}")
                return f"Error retrieving metadata for {request.database}.{request.table}: {str(e)}"

        @self.app.tool()
        async def search_tables(request: TableSearchRequest) -> str:
            """
            Search for tables across databases using patterns or business terms.
            
            Helps AI agents discover relevant data sources by:
            - Searching table names with pattern matching
            - Finding tables related to business concepts
            - Providing contextual information about matches
            
            Returns a ranked list of matching tables with metadata.
            """
            try:
                results = []
                databases_to_search = [request.database] if request.database else list(self.config.get('databases', {}).keys())
                
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
                    return f"No tables found matching '{request.query}'"
                
                search_summary = f"Found {len(results)} tables matching '{request.query}':\n\n"
                for result in results[:request.limit]:
                    search_summary += f"📊 {result['database']}.{result['table']}"
                    if 'columns' in result:
                        search_summary += f" ({result['columns']} columns)"
                    search_summary += f"\n   Match: {result['match_reason']}\n"
                    if 'sample_columns' in result:
                        search_summary += f"   Columns: {', '.join(result['sample_columns'])}\n"
                    search_summary += "\n"
                    
                return search_summary
                
            except Exception as e:
                logger.error(f"Error in table search: {str(e)}")
                return f"Error searching for tables: {str(e)}"

        @self.app.tool()
        async def analyze_data_quality(request: QualityAnalysisRequest) -> str:
            """
            Analyze data quality metrics for tables or entire schemas.
            
            Provides comprehensive quality assessment including:
            - Completeness metrics (null rates, missing values)
            - Consistency checks (format validation, outliers)
            - Accuracy indicators (data type compliance)
            - Timeliness metrics (freshness, update patterns)
            
            Helps AI agents understand data reliability before analysis.
            """
            try:
                if request.table:
                    # Analyze specific table
                    metadata = generate_complete_table_metadata(
                        db_name=request.database,
                        table_name=request.table,
                        schema_name=request.schema,
                        include_data_quality=True,
                        include_relationships=False,  # Focus on quality
                        sample_size=1000,  # Larger sample for quality analysis
                        num_samples=5
                    )
                    
                    quality_metrics = metadata.get('data_quality_metrics', {})
                    column_stats = metadata.get('column_statistics', {})
                    
                    summary = f"🔍 Data Quality Analysis for {request.database}.{request.schema}.{request.table}:\n\n"
                    
                    # Overall quality score (if available)
                    if 'overall_quality_score' in quality_metrics:
                        score = quality_metrics['overall_quality_score']
                        summary += f"📊 Overall Quality Score: {score}/100\n\n"
                    
                    # Column-level quality
                    summary += "📋 Column Quality Metrics:\n"
                    for col_name, col_info in column_stats.items():
                        if isinstance(col_info, dict):
                            null_rate = col_info.get('null_percentage', 0)
                            unique_count = col_info.get('unique_count', 'N/A')
                            summary += f"  • {col_name}: {100-null_rate:.1f}% complete, {unique_count} unique values\n"
                    
                    # Additional quality insights
                    if 'quality_issues' in quality_metrics:
                        issues = quality_metrics['quality_issues']
                        if issues:
                            summary += f"\n⚠️ Quality Issues Found:\n"
                            for issue in issues:
                                summary += f"  • {issue}\n"
                        else:
                            summary += f"\n✅ No major quality issues detected\n"
                    
                    return summary
                    
                else:
                    # Analyze entire database/schema
                    return f"📊 Schema-wide quality analysis for {request.database}.{request.schema}\n\nFull schema analysis is being enhanced. For now, analyze specific tables individually for detailed quality metrics."
                    
            except Exception as e:
                logger.error(f"Error in quality analysis: {str(e)}")
                return f"Error analyzing data quality: {str(e)}"

        @self.app.tool()
        async def get_schema_overview(request: SchemaOverviewRequest) -> str:
            """
            Get a comprehensive overview of database schema structure.
            
            Provides high-level information about:
            - All tables in the schema
            - Table sizes and column counts
            - Basic metadata for quick understanding
            - Relationships between tables (if detectable)
            
            Perfect for AI agents getting familiar with a new database.
            """
            try:
                db = get_db_handler(request.database)
                tables = db.get_all_tables(request.schema)
                
                overview = f"🗄️ Schema Overview for {request.database}.{request.schema}:\n\n"
                overview += f"📊 Total Tables: {len(tables)}\n\n"
                
                if not tables:
                    return overview + "No tables found in this schema."
                
                overview += "📋 Tables Summary:\n"
                
                table_details = []
                for table in tables[:50]:  # Limit to avoid overwhelming output
                    try:
                        columns = db.get_table_schema(table, request.schema)
                        # Try to get row count (if supported)
                        try:
                            row_count_query = f"SELECT COUNT(*) as count FROM {request.schema}.{table}" if request.schema != "public" else f"SELECT COUNT(*) as count FROM {table}"
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
                    
                return overview
                
            except Exception as e:
                logger.error(f"Error getting schema overview: {str(e)}")
                return f"Error retrieving schema overview: {str(e)}"

        @self.app.tool()
        async def generate_semantic_model(request: SemanticModelRequest) -> str:
            """
            Generate semantic models (LookML, dbt) for business intelligence.
            
            Creates production-ready semantic models including:
            - View definitions with proper field types
            - Dimension and measure specifications
            - Join relationships between tables
            - Business-friendly naming and descriptions
            
            Essential for AI agents building BI solutions and data products.
            """
            try:
                if request.model_type == "lookml":
                    lookml_result = generate_lookml_model(
                        db_name=request.database,
                        schema_name=request.schema,
                        table_names=request.tables,
                        model_name=request.model_name,
                        include_derived_tables=True,
                        include_explores=True
                    )
                    
                    summary = f"🏗️ Generated LookML model '{request.model_name}' for tables: {', '.join(request.tables)}\n\n"
                    
                    # Extract key information
                    if 'view_files' in lookml_result:
                        view_files = lookml_result['view_files']
                        summary += f"📊 Generated Components:\n"
                        summary += f"  • {len(view_files)} view files\n"
                        
                        # List view files
                        for view_name in view_files.keys():
                            summary += f"    - {view_name}.view.lkml\n"
                    
                    if 'model_file' in lookml_result:
                        summary += f"  • 1 model file ({request.model_name}.model.lkml)\n"
                        
                    if 'explore_definitions' in lookml_result:
                        explores = lookml_result['explore_definitions']
                        summary += f"  • {len(explores)} explore definitions\n"
                    
                    # Include processing stats
                    stats = lookml_result.get('processing_stats', {})
                    if 'total_time_seconds' in stats:
                        summary += f"\n⏱️ Generated in {stats['total_time_seconds']:.2f} seconds\n"
                    
                    # Include full LookML for implementation
                    summary += f"\n📝 Full LookML Model:\n"
                    summary += "```lookml\n"
                    summary += json.dumps(lookml_result, indent=2, default=str)
                    summary += "\n```\n"
                    
                    return summary
                    
                elif request.model_type == "dbt":
                    return "🚧 dbt model generation is coming soon! Currently supported: LookML"
                    
                else:
                    return f"❌ Unsupported model type: {request.model_type}. Supported types: lookml, dbt"
                    
            except Exception as e:
                logger.error(f"Error generating semantic model: {str(e)}")
                return f"Error generating {request.model_type} model: {str(e)}"

        @self.app.tool()
        async def explain_business_context(request: BusinessContextRequest) -> str:
            """
            Explain business context and meaning for tables and columns.
            
            Uses AI analysis to provide:
            - Business purpose and domain context
            - Column meanings in business terms
            - Usage patterns and relationships
            - Recommended use cases and constraints
            
            Helps AI agents understand the business semantics behind data structures.
            """
            try:
                # Get metadata with business context
                metadata = generate_complete_table_metadata(
                    db_name=request.database,
                    table_name=request.table,
                    schema_name=request.schema,
                    include_additional_insights=True,
                    include_business_rules=True
                )
                
                if request.column:
                    # Explain specific column
                    column_info = metadata.get('columns', {}).get(request.column, {})
                    
                    if not column_info:
                        return f"❌ Column '{request.column}' not found in table {request.database}.{request.schema}.{request.table}"
                    
                    explanation = f"💼 Business Context for Column: {request.database}.{request.schema}.{request.table}.{request.column}\n\n"
                    
                    # Basic information
                    explanation += f"📊 **Technical Details:**\n"
                    explanation += f"  • Data Type: {column_info.get('data_type', 'Unknown')}\n"
                    explanation += f"  • Nullable: {column_info.get('is_nullable', 'Unknown')}\n"
                    
                    # Business information
                    explanation += f"\n💼 **Business Information:**\n"
                    explanation += f"  • Business Name: {column_info.get('business_name', 'Not specified')}\n"
                    explanation += f"  • Description: {column_info.get('description', 'No description available')}\n"
                    
                    # Additional insights
                    if column_info.get('categorical_values'):
                        explanation += f"  • Possible Values: {', '.join(column_info['categorical_values'][:10])}\n"
                        if len(column_info['categorical_values']) > 10:
                            explanation += f"    (and {len(column_info['categorical_values']) - 10} more...)\n"
                    
                    # Statistics if available
                    stats = column_info.get('statistics', {})
                    if stats:
                        explanation += f"\n📈 **Statistics:**\n"
                        for stat_name, stat_value in stats.items():
                            explanation += f"  • {stat_name}: {stat_value}\n"
                    
                else:
                    # Explain entire table
                    table_desc = metadata.get('table_description', {})
                    
                    explanation = f"💼 Business Context for Table: {request.database}.{request.schema}.{request.table}\n\n"
                    
                    # High-level purpose
                    explanation += f"🎯 **Purpose:** {table_desc.get('purpose', 'No purpose description available')}\n\n"
                    explanation += f"🏢 **Business Domain:** {table_desc.get('business_domain', 'Not specified')}\n\n"
                    
                    # Key columns
                    columns = metadata.get('columns', {})
                    if columns:
                        explanation += f"📋 **Key Columns ({len(columns)} total):**\n"
                        # Show first 10 columns with descriptions
                        for i, (col_name, col_info) in enumerate(list(columns.items())[:10]):
                            desc = col_info.get('description', 'No description')
                            explanation += f"  • **{col_name}** ({col_info.get('data_type', 'unknown')}): {desc}\n"
                        
                        if len(columns) > 10:
                            explanation += f"  ... and {len(columns) - 10} more columns\n"
                    
                    # Business rules
                    business_rules = metadata.get('business_rules', {})
                    if business_rules:
                        explanation += f"\n📋 **Business Rules:**\n"
                        for rule_type, rules in business_rules.items():
                            if rules:
                                explanation += f"  • {rule_type}: {rules}\n"
                    
                    # Usage recommendations
                    insights = metadata.get('additional_insights', {})
                    if insights:
                        explanation += f"\n💡 **Usage Insights:**\n"
                        for insight_type, insight_value in insights.items():
                            explanation += f"  • {insight_type}: {insight_value}\n"
                
                return explanation
                
            except Exception as e:
                logger.error(f"Error explaining business context: {str(e)}")
                return f"Error explaining business context: {str(e)}"

    def _setup_resources(self):
        """Setup FastMCP resources for metadata access."""
        
        @self.app.resource("metadata://databases/{database}/schema")
        async def get_database_schema(database: str) -> str:
            """Get complete database schema as a resource."""
            try:
                db = get_db_handler(database)
                tables = db.get_all_tables()
                
                schema_info = {
                    "database": database,
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

        @self.app.resource("metadata://databases/{database}/quality-report")
        async def get_quality_report(database: str) -> str:
            """Get data quality report as a resource."""
            # Enhanced quality reporting could be implemented here
            return json.dumps({
                "database": database,
                "quality_summary": "Comprehensive quality analysis available via tools",
                "generated_at": datetime.now().isoformat(),
                "recommendation": "Use analyze_data_quality tool for detailed analysis"
            })

    def _format_metadata_for_ai(self, metadata: Dict[str, Any]) -> str:
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

    def get_app(self) -> FastMCP:
        """Get the FastMCP application instance."""
        return self.app


# Create global instance
server = MetadataFastMCPServer()
app = server.get_app()

# Entry point for running the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 