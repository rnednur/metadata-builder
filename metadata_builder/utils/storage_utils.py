"""
Utility functions for metadata storage path management.
Ensures consistent db.schema.table format across all storage operations.
"""

import os
from pathlib import Path
from typing import Tuple, Optional


def get_metadata_storage_path(db_name: str, schema_name: str, table_name: str, 
                             base_dir: str = "metadata_storage") -> Path:
    """
    Generate a consistent storage path for metadata files using db.schema.table format.
    
    Args:
        db_name: Database name
        schema_name: Schema name  
        table_name: Table name
        base_dir: Base directory for metadata storage
        
    Returns:
        Path object representing the full file path
    """
    # Sanitize names to be filesystem-safe
    safe_db_name = sanitize_filename(db_name)
    safe_schema_name = sanitize_filename(schema_name)
    safe_table_name = sanitize_filename(table_name)
    
    # Create directory structure: metadata_storage/db_name/schema_name/table_name.json
    metadata_dir = Path(base_dir)
    storage_path = metadata_dir / safe_db_name / safe_schema_name
    storage_path.mkdir(parents=True, exist_ok=True)
    
    return storage_path / f"{safe_table_name}.json"


def get_metadata_directory_path(db_name: str, schema_name: str, 
                               base_dir: str = "metadata_storage") -> Path:
    """
    Generate directory path for a specific database and schema.
    
    Args:
        db_name: Database name
        schema_name: Schema name
        base_dir: Base directory for metadata storage
        
    Returns:
        Path object representing the directory path
    """
    safe_db_name = sanitize_filename(db_name)
    safe_schema_name = sanitize_filename(schema_name)
    
    return Path(base_dir) / safe_db_name / safe_schema_name


def parse_metadata_path(file_path: Path) -> Tuple[str, str, str]:
    """
    Parse a metadata file path to extract db, schema, and table names.
    
    Args:
        file_path: Path to metadata file
        
    Returns:
        Tuple of (db_name, schema_name, table_name)
    """
    if not file_path.suffix == '.json':
        raise ValueError("Invalid metadata file: must be a .json file")
    
    parts = file_path.parts
    if len(parts) < 3:
        raise ValueError("Invalid metadata file path: must follow db/schema/table.json structure")
    
    table_name = file_path.stem
    schema_name = parts[-2]
    db_name = parts[-3]
    
    return db_name, schema_name, table_name


def sanitize_filename(name: str) -> str:
    """
    Sanitize a name to be filesystem-safe.
    
    Args:
        name: Original name
        
    Returns:
        Sanitized name safe for filesystem use
    """
    # Remove/replace problematic characters
    safe_name = name.replace('/', '_').replace('\\', '_').replace(':', '_')
    safe_name = safe_name.replace('<', '_').replace('>', '_').replace('|', '_')
    safe_name = safe_name.replace('*', '_').replace('?', '_').replace('"', '_')
    
    # Remove leading/trailing spaces and dots
    safe_name = safe_name.strip(' .')
    
    return safe_name


def list_stored_metadata(db_name: str, base_dir: str = "metadata_storage") -> list:
    """
    List all stored metadata files for a database.
    
    Args:
        db_name: Database name
        base_dir: Base directory for metadata storage
        
    Returns:
        List of dictionaries containing metadata file information
    """
    metadata_files = []
    db_path = Path(base_dir) / sanitize_filename(db_name)
    
    if not db_path.exists():
        return metadata_files
    
    for schema_dir in db_path.iterdir():
        if schema_dir.is_dir():
            schema_name = schema_dir.name
            for metadata_file in schema_dir.glob("*.json"):
                table_name = metadata_file.stem
                
                # Get file modification time
                mtime = metadata_file.stat().st_mtime
                
                metadata_files.append({
                    "database_name": db_name,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "file_path": str(metadata_file),
                    "modified_timestamp": mtime
                })
    
    return metadata_files


def get_fully_qualified_table_name(db_name: str, schema_name: str, table_name: str) -> str:
    """
    Generate a fully qualified table name in db.schema.table format.
    
    Args:
        db_name: Database name
        schema_name: Schema name
        table_name: Table name
        
    Returns:
        Fully qualified table name
    """
    return f"{db_name}.{schema_name}.{table_name}" 