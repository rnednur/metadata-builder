#!/usr/bin/env python3
"""
Command-line interface for directly generating table metadata.
This script provides a non-interactive way to call the metadata generation
functions, suitable for automation and scripting.
"""

import argparse
import json
import yaml
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

from ..core.generate_table_metadata import generate_complete_table_metadata
from ..core.semantic_models import generate_lookml_model
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("metadata_builder.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
console = Console()

def main():
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        description="Metadata Builder CLI - Generate rich table metadata with LLM enhancement"
    )
    
    # Required arguments
    parser.add_argument("--db", required=True, help="Database name (must be in config)")
    parser.add_argument("--table", required=True, help="Table name to analyze")
    
    # Optional arguments
    parser.add_argument("--schema", default="public", help="Schema name (default: public)")
    parser.add_argument("--sql-file", help="Path to file containing custom SQL query")
    parser.add_argument("--sample-size", type=int, default=100, help="Sample size for each sample (default: 100)")
    parser.add_argument("--num-samples", type=int, default=5, help="Number of samples to take (default: 5)")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Output format (default: json)")
    parser.add_argument("--summary", action="store_true", help="Display a summary of the metadata after generation")
    
    # Semantic model generation arguments
    parser.add_argument("--generate-lookml", action="store_true", help="Generate LookML semantic model instead of metadata")
    parser.add_argument("--model-name", help="Name for the LookML model (default: table_name_model)")
    parser.add_argument("--include-derives", action="store_true", help="Include derived table suggestions in LookML")
    parser.add_argument("--include-explores", action="store_true", default=True, help="Include explore definitions in LookML (default: True)")
    parser.add_argument("--additional-prompt", help="Additional requirements for LookML generation")

    args = parser.parse_args()
    
    # Banner
    console.print(Panel.fit("🔍 [bold blue]Metadata Builder CLI[/bold blue]", 
                            subtitle="Generate enhanced metadata with LLM analysis"))
    
    try:
        # Load custom SQL from file if provided
        analysis_sql = None
        if args.sql_file:
            try:
                with open(args.sql_file, 'r') as f:
                    analysis_sql = f.read().strip()
                console.print(f"[green]Loaded custom SQL from {args.sql_file}[/green]")
            except Exception as e:
                console.print(f"[red]Error loading SQL file: {str(e)}[/red]")
                return 1
        
        # Check if LookML generation is requested
        if args.generate_lookml:
            # Generate LookML model
            with Progress() as progress:
                task = progress.add_task("[cyan]Generating LookML model...", total=1)
                
                model_name = args.model_name or f"{args.table}_model"
                
                lookml_result = generate_lookml_model(
                    db_name=args.db,
                    schema_name=args.schema,
                    table_names=[args.table],
                    model_name=model_name,
                    include_derived_tables=args.include_derives,
                    include_explores=args.include_explores,
                    additional_prompt=args.additional_prompt
                )
                
                progress.update(task, completed=1)
            
            # Determine output path for LookML
            if args.output:
                output_path = args.output
            else:
                # Default output directory
                output_dir = os.path.join(os.path.dirname(__file__), 'metadata')
                os.makedirs(output_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(
                    output_dir,
                    f"{args.db}_{args.schema}_{args.table}_lookml_{timestamp}.{args.format}"
                )
            
            # Save LookML output
            with open(output_path, 'w') as f:
                if args.format == "json":
                    json.dump(lookml_result, f, indent=2)
                else:
                    yaml.dump(lookml_result, f, sort_keys=False)
            
            console.print(f"[green]LookML model generated and saved to {output_path}[/green]")
            
            # Display summary if requested
            if args.summary:
                # Show processing time
                stats = lookml_result.get('processing_stats', {})
                total_time = stats.get('total_time_seconds', 0)
                total_tokens = stats.get('total_tokens', 0)
                console.print(f"[blue]Processing time: {total_time:.2f} seconds[/blue]")
                console.print(f"[blue]Total tokens used: {total_tokens}[/blue]")
                
                # Show content summary
                views_count = len(lookml_result.get('views', []))
                explores_count = len(lookml_result.get('explores', []))
                console.print(f"[blue]Generated {views_count} views and {explores_count} explores[/blue]")
                
                # Show model name
                model_name = lookml_result.get('model_name', 'Unknown')
                console.print(f"[bold]Model Name:[/bold] {model_name}")
            
            return 0
        
        # Generate metadata
        with Progress() as progress:
            task = progress.add_task("[cyan]Generating metadata...", total=1)
            
            metadata = generate_complete_table_metadata(
                db_name=args.db,
                table_name=args.table,
                schema_name=args.schema,
                analysis_sql=analysis_sql,
                sample_size=args.sample_size,
                num_samples=args.num_samples
            )
            
            progress.update(task, completed=1)
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            # Default output directory
            output_dir = os.path.join(os.path.dirname(__file__), 'metadata')
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(
                output_dir,
                f"{args.db}_{args.schema}_{args.table}_{timestamp}.{args.format}"
            )
        
        # Save output
        with open(output_path, 'w') as f:
            if args.format == "json":
                json.dump(metadata, f, indent=2)
            else:
                yaml.dump(metadata, f, sort_keys=False)
        
        console.print(f"[green]Metadata generated and saved to {output_path}[/green]")
        
        # Display summary if requested
        if args.summary:
            # Show processing time
            stats = metadata.get('processing_stats', {})
            total_time = stats.get('total_duration_seconds', 0)
            console.print(f"[blue]Processing time: {total_time:.2f} seconds[/blue]")
            
            # Show column count
            column_count = len(metadata.get('columns', {}))
            console.print(f"[blue]Columns analyzed: {column_count}[/blue]")
            
            # Show table purpose
            table_purpose = metadata.get('table_description', {}).get('purpose', 'No description available')
            console.print(f"[bold]Table Purpose:[/bold] {table_purpose}")
            
            # Show relationships count
            relationships = metadata.get('relationships', [])
            console.print(f"[blue]Potential relationships identified: {len(relationships)}[/blue]")
            
            # Show business rules count
            rules = metadata.get('business_rules', [])
            console.print(f"[blue]Business rules suggested: {len(rules)}[/blue]")
        
        return 0
    
    except Exception as e:
        console.print(f"[red]Error generating metadata: {str(e)}[/red]")
        logger.error(f"Error in CLI: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 