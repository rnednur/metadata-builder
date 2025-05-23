#!/usr/bin/env python3
"""
Metadata Builder

An interactive CLI tool for generating structured metadata from database tables.
"""

import logging
import yaml
import os
import sys
import json
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

# Import the advanced metadata generation function
from ..core.generate_table_metadata import generate_complete_table_metadata
from ..utils.database_handler import SQLAlchemyHandler
from ..config.config import load_config, get_db_config, get_db_handler
from ..core.semantic_models import generate_lookml_model

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

class MetadataGenerator:
    """
    Main class for generating and managing database metadata.
    """
    
    def __init__(self):
        self.config = load_config()
        self.databases = self.config.get('databases', {})
        self.current_db = None
        self.current_schema = None
        self.current_table = None
        self.metadata_output_dir = self.config.get('metadata', {}).get('output_dir', './metadata')
        
        # Ensure metadata output directory exists
        os.makedirs(self.metadata_output_dir, exist_ok=True)

    def run(self):
        """
        Run the interactive CLI for metadata generation.
        """
        console.print(Panel.fit("🔍 [bold blue]Metadata Builder[/bold blue]", 
                                subtitle="Interactive CLI for generating database metadata"))
        
        try:
            while True:
                self._display_status()
                action = self._main_menu()
                
                if action == "add_database":
                    self.add_database_connection()
                elif action == "connect_database":
                    self.connect_database()
                elif action == "select_schema":
                    self.select_schema()
                elif action == "select_table":
                    self.select_table()
                elif action == "edit_column_metadata":
                    self.edit_column_metadata()
                elif action == "generate_yaml":
                    self.generate_metadata_yaml()
                elif action == "push_metadata":
                    self.push_metadata()
                elif action == "generate_advanced":
                    self.generate_advanced_metadata()
                elif action == "generate_semantic_models":
                    self.generate_semantic_models()
                elif action == "exit":
                    console.print("[green]Exiting Metadata Builder. Goodbye![/green]")
                    break
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation canceled. Exiting...[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            
        # Clean up database connections
        SQLAlchemyHandler.dispose_pools()

    def _display_status(self):
        """
        Display current connection status.
        """
        status_table = Table(show_header=False, box=None)
        status_table.add_column("Key", style="bold")
        status_table.add_column("Value")
        
        status_table.add_row("Database", self.current_db or "Not connected")
        status_table.add_row("Schema", self.current_schema or "Not selected")
        status_table.add_row("Table", self.current_table or "Not selected")
        
        console.print(status_table)

    def _main_menu(self) -> str:
        """
        Display main menu and get user selection.
        
        Returns:
            Selected action
        """
        options = []
        
        # Database connection options
        options.append(questionary.Choice("Add database connection", value="add_database"))
        options.append(questionary.Choice("Connect to database", value="connect_database"))
        
        # Schema and table selection (if connected)
        if self.current_db:
            options.append(questionary.Choice("Select schema", value="select_schema"))
            
            if self.current_schema:
                options.append(questionary.Choice("Select table", value="select_table"))
        
        # Metadata options (if table selected)
        if self.current_table:
            options.append(questionary.Choice("Edit column metadata", value="edit_column_metadata"))
            options.append(questionary.Choice("Generate metadata YAML", value="generate_yaml"))
            options.append(questionary.Choice("Push metadata to database", value="push_metadata"))
            options.append(questionary.Choice("Generate advanced metadata with LLM", value="generate_advanced"))
            options.append(questionary.Choice("Generate semantic models (LookML, dbt, etc.)", value="generate_semantic_models"))
        
        options.append(questionary.Choice("Exit", value="exit"))
        
        result = questionary.select(
            "Select an option:",
            choices=options
        ).ask()
        
        return result

    def add_database_connection(self):
        """
        Add a new database connection.
        """
        db_name = questionary.text("Database name:").ask()
        if not db_name:
            console.print("[yellow]Database name cannot be empty.[/yellow]")
            return
            
        db_type = questionary.select(
            "Select database type:",
            choices=[
                "postgresql",
                "mysql",
                "sqlite",
                "oracle",
                "duckdb",
                "bigquery",
                "kinetica"
            ]
        ).ask()
        
        db_config = {
            "type": db_type
        }
        
        if db_type in ["postgresql", "mysql"]:
            db_config["host"] = questionary.text("Host:").ask() or "localhost"
            db_config["port"] = questionary.text("Port:").ask() or ("5432" if db_type == "postgresql" else "3306")
            db_config["database"] = questionary.text("Database name:").ask()
            db_config["username"] = questionary.text("Username:").ask()
            db_config["password"] = questionary.password("Password:").ask()
            
            # Build connection string
            if db_type == "postgresql":
                conn_str = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
            else:
                conn_str = f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
                
            db_config["connection_string"] = conn_str
            
        elif db_type == "sqlite":
            db_path = questionary.text("Database file path:").ask()
            db_config["database"] = db_path
            db_config["connection_string"] = f"sqlite:///{db_path}"
            
        elif db_type == "duckdb":
            db_path = questionary.text("Database file path:").ask()
            db_config["database"] = db_path
            db_config["connection_string"] = f"duckdb:///{db_path}"
            
        elif db_type == "oracle":
            connection_method = questionary.select(
                "Select Oracle connection method:",
                choices=[
                    "Service Name (recommended)",
                    "SID",
                    "TNS Name"
                ]
            ).ask()
            
            if connection_method == "TNS Name":
                # TNS name connection
                db_config["username"] = questionary.text("Username:").ask()
                db_config["password"] = questionary.password("Password:").ask()
                db_config["tns_name"] = questionary.text("TNS Name:").ask()
                
                conn_str = f"oracle+cx_oracle://{db_config['username']}:{db_config['password']}@{db_config['tns_name']}"
            else:
                # Service Name or SID connection
                db_config["host"] = questionary.text("Host:").ask() or "localhost"
                db_config["port"] = questionary.text("Port:").ask() or "1521"
                db_config["username"] = questionary.text("Username:").ask()
                db_config["password"] = questionary.password("Password:").ask()
                
                if connection_method == "Service Name (recommended)":
                    db_config["service_name"] = questionary.text("Service Name:").ask()
                    conn_str = f"oracle+cx_oracle://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/?service_name={db_config['service_name']}"
                else:  # SID
                    db_config["sid"] = questionary.text("SID:").ask()
                    conn_str = f"oracle+cx_oracle://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/?sid={db_config['sid']}"
            
            db_config["connection_string"] = conn_str
            
        elif db_type == "bigquery":
            project_id = questionary.text("Project ID:").ask()
            credentials_path = questionary.text("Service account credentials JSON path:").ask()
            db_config["project_id"] = project_id
            db_config["credentials_path"] = credentials_path
            
        elif db_type == "kinetica":
            host = questionary.text("Host:").ask() or "localhost"
            port = questionary.text("Port:").ask() or "9191"
            username = questionary.text("Username:").ask()
            password = questionary.password("Password:").ask()
            
            db_config["host"] = host
            db_config["port"] = port
            db_config["username"] = username
            db_config["password"] = password
        
        # Add to config
        self.config.setdefault('databases', {})[db_name] = db_config
        
        # Save updated config - use the main config directory
        config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        config_path = os.path.join(config_dir, 'config.yaml')
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f)
            
        console.print(f"[green]Added database connection: {db_name}[/green]")

    def connect_database(self):
        """
        Connect to a database from the available connections.
        """
        if not self.config.get('databases'):
            console.print("[yellow]No database connections available. Please add one first.[/yellow]")
            return
            
        db_choices = list(self.config.get('databases', {}).keys())
        db_name = questionary.select(
            "Select database to connect to:",
            choices=db_choices
        ).ask()
        
        try:
            with Progress() as progress:
                task = progress.add_task("[cyan]Connecting to database...", total=1)
                
                # Get a database handler for the selected database
                db = get_db_handler(db_name)
                
                # Test connection
                if hasattr(db, 'execute_query'):
                    db.execute_query("SELECT 1")
                    
                progress.update(task, completed=1)
            
            self.current_db = db_name
            self.current_schema = None
            self.current_table = None
            
            console.print(f"[green]Successfully connected to {db_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error connecting to database: {str(e)}[/red]")

    def select_schema(self):
        """
        Select a schema from the connected database.
        """
        if not self.current_db:
            console.print("[yellow]Not connected to any database. Please connect first.[/yellow]")
            return
            
        try:
            db = get_db_handler(self.current_db)
            schemas = db.get_database_schemas()
            
            if not schemas:
                console.print("[yellow]No schemas found in the database.[/yellow]")
                return
                
            schema_name = questionary.select(
                "Select schema:",
                choices=schemas
            ).ask()
            
            self.current_schema = schema_name
            self.current_table = None
            
            console.print(f"[green]Selected schema: {schema_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error selecting schema: {str(e)}[/red]")

    def select_table(self):
        """
        Select a table from the current schema.
        """
        if not self.current_db or not self.current_schema:
            console.print("[yellow]Database or schema not selected. Please select both first.[/yellow]")
            return
            
        try:
            db = get_db_handler(self.current_db)
            tables = db.get_database_tables(self.current_schema)
            
            if not tables:
                console.print("[yellow]No tables found in the schema.[/yellow]")
                return
                
            table_name = questionary.select(
                "Select table:",
                choices=tables
            ).ask()
            
            self.current_table = table_name
            
            console.print(f"[green]Selected table: {table_name}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error selecting table: {str(e)}[/red]")

    def edit_column_metadata(self):
        """
        Edit metadata for individual columns.
        """
        if not self.current_db or not self.current_table:
            console.print("[yellow]Database or table not selected. Please select both first.[/yellow]")
            return
            
        try:
            db = get_db_handler(self.current_db)
            schema = db.get_table_schema(self.current_table, self.current_schema)
            
            if not schema:
                console.print("[yellow]No columns found in the table.[/yellow]")
                return
                
            # Load existing metadata if available
            metadata_file = os.path.join(
                self.metadata_output_dir,
                f"{self.current_db}_{self.current_schema}_{self.current_table}.yaml"
            )
            
            existing_metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    existing_metadata = yaml.safe_load(f)
                
            columns_metadata = existing_metadata.get('columns', {})
            
            # Get a list of columns
            columns = list(schema.keys())
            column_choice = questionary.select(
                "Select column to edit:",
                choices=columns + ["[Done]"]
            ).ask()
            
            while column_choice != "[Done]":
                existing_column_metadata = columns_metadata.get(column_choice, {})
                
                # Edit metadata for the selected column
                description = questionary.text(
                    "Description:",
                    default=existing_column_metadata.get('description', '')
                ).ask()
                
                business_name = questionary.text(
                    "Business name:",
                    default=existing_column_metadata.get('business_name', '')
                ).ask()
                
                # Save back to metadata
                if not columns_metadata.get(column_choice):
                    columns_metadata[column_choice] = {}
                    
                columns_metadata[column_choice]['description'] = description
                columns_metadata[column_choice]['business_name'] = business_name
                columns_metadata[column_choice]['data_type'] = schema[column_choice]
                
                # Select another column
                column_choice = questionary.select(
                    "Select column to edit:",
                    choices=columns + ["[Done]"]
                ).ask()
            
            # Save back to existing metadata
            existing_metadata['columns'] = columns_metadata
            
            # Save to file
            with open(metadata_file, 'w') as f:
                yaml.dump(existing_metadata, f, sort_keys=False)
                
            console.print(f"[green]Saved metadata to {metadata_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error editing column metadata: {str(e)}[/red]")

    def generate_metadata_yaml(self):
        """
        Generate YAML metadata file for the selected table.
        """
        if not self.current_db or not self.current_table:
            console.print("[yellow]Database or table not selected. Please select both first.[/yellow]")
            return
            
        try:
            db = get_db_handler(self.current_db)
            
            # Get table schema
            schema = db.get_table_schema(self.current_table, self.current_schema)
            
            # Get primary keys
            primary_keys = db.get_primary_keys(self.current_table, self.current_schema)
            
            # Get indexes
            indexes = db.get_table_indexes(self.current_table, self.current_schema)
            
            # Get sample data
            if self.current_schema:
                qualified_table_name = f"{self.current_schema}.{self.current_table}"
            else:
                qualified_table_name = self.current_table
                
            query = f"SELECT * FROM {qualified_table_name} LIMIT 5"
            sample_data = db.fetch_all(query)
            
            # Load existing metadata if available
            metadata_file = os.path.join(
                self.metadata_output_dir,
                f"{self.current_db}_{self.current_schema}_{self.current_table}.yaml"
            )
            
            existing_metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    existing_metadata = yaml.safe_load(f)
            
            # Create metadata structure
            metadata = {
                "database_name": self.current_db,
                "schema_name": self.current_schema,
                "table_name": self.current_table,
                "description": existing_metadata.get('description', ''),
                "columns": {},
                "primary_key": primary_keys,
                "indexes": indexes,
                "sample_data": sample_data,
                "generated_at": datetime.now().isoformat()
            }
            
            # Add columns metadata
            for column, data_type in schema.items():
                existing_column = existing_metadata.get('columns', {}).get(column, {})
                
                metadata['columns'][column] = {
                    "name": column,
                    "data_type": data_type,
                    "description": existing_column.get('description', ''),
                    "business_name": existing_column.get('business_name', ''),
                    "is_nullable": True  # Would need schema info to be more accurate
                }
            
            # Save to file
            with open(metadata_file, 'w') as f:
                yaml.dump(metadata, f, sort_keys=False)
                
            console.print(f"[green]Generated metadata YAML at {metadata_file}[/green]")
            
        except Exception as e:
            console.print(f"[red]Error generating metadata YAML: {str(e)}[/red]")

    def push_metadata(self):
        """
        Push metadata to the database if supported.
        """
        console.print("[yellow]This feature requires a metadata database setup. Coming soon...[/yellow]")

    def generate_advanced_metadata(self):
        """
        Generate advanced metadata with LLM and related tools.
        """
        if not self.current_db or not self.current_table:
            console.print("[yellow]Database or table not selected. Please select both first.[/yellow]")
            return
            
        try:
            # Ask for sample size and number of samples
            use_custom_sql = questionary.confirm("Use custom SQL query for analysis?").ask()
            
            analysis_sql = None
            if use_custom_sql:
                analysis_sql = questionary.text("Enter custom SQL query:").ask()
                
            sample_size = questionary.text("Sample size per batch (default: 100):", default="100").ask()
            num_samples = questionary.text("Number of samples to take (default: 5):", default="5").ask()
            
            try:
                sample_size = int(sample_size)
                num_samples = int(num_samples)
            except ValueError:
                console.print("[yellow]Invalid numbers. Using defaults: sample_size=100, num_samples=5[/yellow]")
                sample_size = 100
                num_samples = 5
            
            # Generate metadata
            with Progress() as progress:
                task = progress.add_task("[cyan]Generating advanced metadata...", total=1)
                
                metadata = generate_complete_table_metadata(
                    db_name=self.current_db,
                    table_name=self.current_table,
                    schema_name=self.current_schema,
                    analysis_sql=analysis_sql,
                    sample_size=sample_size,
                    num_samples=num_samples
                )
                
                progress.update(task, completed=1)
            
            # Save as both YAML and JSON
            yaml_file = os.path.join(
                self.metadata_output_dir,
                f"{self.current_db}_{self.current_schema}_{self.current_table}_advanced.yaml"
            )
            
            json_file = os.path.join(
                self.metadata_output_dir,
                f"{self.current_db}_{self.current_schema}_{self.current_table}_advanced.json"
            )
            
            # Save YAML
            with open(yaml_file, 'w') as f:
                yaml.dump(metadata, f, sort_keys=False)
            
            # Save JSON
            with open(json_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            # Show summary
            console.print(f"[green]Generated advanced metadata:[/green]")
            console.print(f"  - YAML file: {yaml_file}")
            console.print(f"  - JSON file: {json_file}")
            
            # Display statistics
            stats = metadata.get('processing_stats', {})
            total_time = stats.get('total_duration_seconds', 0)
            console.print(f"[blue]Processing time: {total_time:.2f} seconds[/blue]")
            
            show_details = questionary.confirm("Show metadata details?").ask()
            if show_details:
                # Create a table for column summary
                table = Table(title=f"Columns Summary for {self.current_table}")
                table.add_column("Column", style="cyan")
                table.add_column("Type", style="green")
                table.add_column("Description", style="yellow")
                
                for col_name, col_info in metadata.get('columns', {}).items():
                    description = col_info.get('description', '')
                    # Truncate long descriptions
                    if len(description) > 50:
                        description = description[:47] + "..."
                    table.add_row(col_name, col_info.get('data_type', ''), description)
                
                console.print(table)
                
                # Show table description
                table_purpose = metadata.get('table_description', {}).get('purpose', 'No description available')
                console.print(f"[bold]Table Purpose:[/bold] {table_purpose}")
            
        except Exception as e:
            console.print(f"[red]Error generating advanced metadata: {str(e)}[/red]")
            logger.error(f"Error generating advanced metadata: {str(e)}", exc_info=True)

    def generate_semantic_models(self):
        """
        Generate semantic models (LookML, dbt, etc.) for the selected table.
        """
        if not self.current_db or not self.current_table:
            console.print("[yellow]Database or table not selected. Please select both first.[/yellow]")
            return
            
        try:
            # Ask what type of semantic model to generate
            model_type = questionary.select(
                "Select semantic model type:",
                choices=[
                    "LookML",
                    "dbt (coming soon)",
                    "Cube.js (coming soon)"
                ]
            ).ask()
            
            if model_type != "LookML":
                console.print(f"[yellow]{model_type} generation is coming soon![/yellow]")
                return
            
            # Get model configuration
            model_name = questionary.text(f"Model name (default: {self.current_table}_model):", 
                                        default=f"{self.current_table}_model").ask()
            
            include_derives = questionary.confirm("Include derived table suggestions?").ask()
            include_explores = questionary.confirm("Include explore definitions?").ask()
            
            additional_requirements = questionary.text("Additional requirements (optional):").ask()
            
            # Generate LookML model
            with Progress() as progress:
                task = progress.add_task("[cyan]Generating LookML model...", total=1)
                
                lookml_result = generate_lookml_model(
                    db_name=self.current_db,
                    schema_name=self.current_schema,
                    table_names=[self.current_table],
                    model_name=model_name,
                    include_derived_tables=include_derives,
                    include_explores=include_explores,
                    additional_prompt=additional_requirements if additional_requirements else None
                )
                
                progress.update(task, completed=1)
            
            # Save outputs
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_filename = f"{self.current_db}_{self.current_schema}_{self.current_table}_lookml_{timestamp}"
            
            yaml_file = os.path.join(self.metadata_output_dir, f"{base_filename}.yaml")
            json_file = os.path.join(self.metadata_output_dir, f"{base_filename}.json")
            
            # Save YAML
            with open(yaml_file, 'w') as f:
                yaml.dump(lookml_result, f, sort_keys=False)
            
            # Save JSON
            with open(json_file, 'w') as f:
                json.dump(lookml_result, f, indent=2)
                
            # Show summary
            console.print(f"[green]Generated LookML model:[/green]")
            console.print(f"  - YAML file: {yaml_file}")
            console.print(f"  - JSON file: {json_file}")
            
            # Display statistics
            stats = lookml_result.get('processing_stats', {})
            total_time = stats.get('total_time_seconds', 0)
            total_tokens = stats.get('total_tokens', 0)
            console.print(f"[blue]Processing time: {total_time:.2f} seconds[/blue]")
            console.print(f"[blue]Total tokens used: {total_tokens}[/blue]")
            
            # Show generated content summary
            views_count = len(lookml_result.get('views', []))
            explores_count = len(lookml_result.get('explores', []))
            console.print(f"[blue]Generated {views_count} views and {explores_count} explores[/blue]")
            
            show_details = questionary.confirm("Show LookML structure details?").ask()
            if show_details:
                # Show views summary
                if views_count > 0:
                    views_table = Table(title="Generated Views")
                    views_table.add_column("View Name", style="cyan")
                    views_table.add_column("Dimensions", style="green")
                    views_table.add_column("Measures", style="yellow")
                    
                    for view in lookml_result.get('views', []):
                        view_name = view.get('view_name', 'Unknown')
                        dimensions_count = len(view.get('dimensions', []))
                        measures_count = len(view.get('measures', []))
                        views_table.add_row(view_name, str(dimensions_count), str(measures_count))
                    
                    console.print(views_table)
                
                # Show explores summary
                if explores_count > 0:
                    explores_table = Table(title="Generated Explores")
                    explores_table.add_column("Explore Name", style="cyan")
                    explores_table.add_column("Base View", style="green")
                    explores_table.add_column("Joins", style="yellow")
                    
                    for explore in lookml_result.get('explores', []):
                        explore_name = explore.get('name', 'Unknown')
                        base_view = explore.get('view_name', 'Unknown')
                        joins_count = len(explore.get('joins', []))
                        explores_table.add_row(explore_name, base_view, str(joins_count))
                    
                    console.print(explores_table)
            
        except Exception as e:
            console.print(f"[red]Error generating semantic models: {str(e)}[/red]")
            logger.error(f"Error generating semantic models: {str(e)}", exc_info=True)

if __name__ == "__main__":
    generator = MetadataGenerator()
    generator.run()

def main():
    """Entry point for the metadata-builder CLI command."""
    generator = MetadataGenerator()
    generator.run()