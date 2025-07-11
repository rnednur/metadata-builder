"""
Persistence layer for metadata storage in PostgreSQL.
"""

from .models import (
    Base,
    DatabaseMetadata,
    TableMetadata, 
    ColumnMetadata,
    IndexMetadata,
    ConstraintMetadata,
    RelationshipMetadata,
    SampleDataMetadata,
    ProcessingStatsMetadata
)
from .repository import MetadataRepository
from .migration import create_metadata_tables

__all__ = [
    'Base',
    'DatabaseMetadata',
    'TableMetadata',
    'ColumnMetadata', 
    'IndexMetadata',
    'ConstraintMetadata',
    'RelationshipMetadata',
    'SampleDataMetadata',
    'ProcessingStatsMetadata',
    'MetadataRepository',
    'create_metadata_tables'
] 