"""
Metadata Builder - An interactive CLI tool for generating structured metadata from database tables.

This package provides tools for:
- Connecting to various database types
- Analyzing table schemas and data
- Generating rich metadata with LLM enhancement
- Creating semantic models (LookML, dbt, etc.)
"""

__version__ = "1.0.0"
__author__ = "Metadata Builder Project"
__email__ = "your.email@example.com"

# Core functionality imports
from .core.generate_table_metadata import generate_complete_table_metadata
from .core.semantic_models import generate_lookml_model

# Configuration imports
from .config.config import load_config, get_db_config, get_llm_api_config

# Utility imports
from .utils.database_handler import SQLAlchemyHandler
from .utils.metadata_utils import (
    extract_categorical_values,
    identify_column_types,
    compute_numerical_stats,
    compute_data_quality_metrics,
    extract_constraints
)

# CLI imports
from .cli.main import MetadataGenerator

__all__ = [
    # Core functions
    'generate_complete_table_metadata',
    'generate_lookml_model',
    
    # Configuration
    'load_config',
    'get_db_config', 
    'get_llm_api_config',
    
    # Database handling
    'SQLAlchemyHandler',
    
    # Utilities
    'extract_categorical_values',
    'identify_column_types',
    'compute_numerical_stats',
    'compute_data_quality_metrics',
    'extract_constraints',
    
    # CLI
    'MetadataGenerator',
] 