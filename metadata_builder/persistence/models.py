"""
SQLAlchemy models for metadata persistence in PostgreSQL.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, JSON, DECIMAL, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()


class DatabaseMetadata(Base):
    """Stores metadata about source databases being analyzed."""
    
    __tablename__ = 'database_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # postgresql, mysql, bigquery, etc.
    host = Column(String(255))
    port = Column(Integer)
    database_name = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tables = relationship("TableMetadata", back_populates="database", cascade="all, delete-orphan")


class TableMetadata(Base):
    """Stores comprehensive metadata about database tables."""
    
    __tablename__ = 'table_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    database_id = Column(UUID(as_uuid=True), ForeignKey('database_metadata.id'), nullable=False)
    table_name = Column(String(255), nullable=False)
    schema_name = Column(String(255), nullable=False, default='public')
    description = Column(Text)
    business_context = Column(Text)
    
    # Table-level metadata
    row_count = Column(Integer)
    size_bytes = Column(Integer)
    data_quality_score = Column(DECIMAL(5, 2))  # 0-100 score
    
    # LLM-generated insights
    table_purpose = Column(Text)
    primary_entity = Column(String(255))
    business_use_cases = Column(JSONB)  # List of use cases
    special_handling = Column(JSONB)    # List of special handling notes
    
    # Processing metadata
    generated_by = Column(String(20), default='llm')  # manual, llm, hybrid
    generation_version = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_analyzed = Column(DateTime)
    
    # Relationships
    database = relationship("DatabaseMetadata", back_populates="tables")
    columns = relationship("ColumnMetadata", back_populates="table", cascade="all, delete-orphan")
    indexes = relationship("IndexMetadata", back_populates="table", cascade="all, delete-orphan")
    constraints = relationship("ConstraintMetadata", back_populates="table", cascade="all, delete-orphan")
    relationships = relationship("RelationshipMetadata", back_populates="table", cascade="all, delete-orphan")
    sample_data = relationship("SampleDataMetadata", back_populates="table", cascade="all, delete-orphan")
    processing_stats = relationship("ProcessingStatsMetadata", back_populates="table", cascade="all, delete-orphan")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('database_id', 'schema_name', 'table_name', name='uq_table_per_database'),
        Index('idx_table_database_schema', 'database_id', 'schema_name'),
        Index('idx_table_name', 'table_name'),
    )


class ColumnMetadata(Base):
    """Stores detailed metadata about table columns."""
    
    __tablename__ = 'column_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    # Column basic info
    name = Column(String(255), nullable=False)
    data_type = Column(String(100), nullable=False)
    ordinal_position = Column(Integer)
    is_nullable = Column(Boolean, default=True)
    default_value = Column(Text)
    
    # Business metadata
    description = Column(Text)
    business_name = Column(String(255))
    purpose = Column(Text)
    format = Column(Text)
    data_classification = Column(String(50))  # public, internal, confidential, restricted
    
    # Column characteristics
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    foreign_key_reference = Column(String(500))  # "table.column" format
    is_unique = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    is_categorical = Column(Boolean, default=False)
    is_numerical = Column(Boolean, default=False)
    
    # Statistics and analysis
    statistics = Column(JSONB)  # Numerical stats (min, max, mean, etc.)
    categorical_values = Column(JSONB)  # Categorical value analysis
    quality_metrics = Column(JSONB)  # Data quality metrics
    constraints = Column(JSONB)  # Business rules and constraints
    
    # LLM-generated insights
    business_rules = Column(JSONB)  # List of business rules
    data_quality_checks = Column(JSONB)  # List of quality checks
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="columns")
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('table_id', 'name', name='uq_column_per_table'),
        Index('idx_column_table', 'table_id'),
        Index('idx_column_name', 'name'),
        Index('idx_column_type', 'data_type'),
    )


class IndexMetadata(Base):
    """Stores information about database indexes."""
    
    __tablename__ = 'index_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    index_type = Column(String(50))  # BTREE, HASH, etc.
    columns = Column(JSONB, nullable=False)  # List of column names
    is_unique = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    description = Column(Text)
    
    # Additional index metadata
    definition = Column(Text)  # Full index definition
    size_bytes = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="indexes")
    
    __table_args__ = (
        Index('idx_index_table', 'table_id'),
        Index('idx_index_name', 'name'),
    )


class ConstraintMetadata(Base):
    """Stores information about database constraints."""
    
    __tablename__ = 'constraint_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    constraint_type = Column(String(50), nullable=False)  # primary_key, foreign_key, unique, check
    columns = Column(JSONB, nullable=False)  # List of column names
    description = Column(Text)
    
    # For foreign keys
    reference_table = Column(String(255))
    reference_columns = Column(JSONB)
    reference_schema = Column(String(255))
    
    # For check constraints
    definition = Column(Text)
    
    # Additional metadata
    is_deferrable = Column(Boolean, default=False)
    initially_deferred = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="constraints")
    
    __table_args__ = (
        Index('idx_constraint_table', 'table_id'),
        Index('idx_constraint_type', 'constraint_type'),
    )


class RelationshipMetadata(Base):
    """Stores information about table relationships."""
    
    __tablename__ = 'relationship_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    relationship_type = Column(String(50), nullable=False)  # one-to-many, many-to-many, one-to-one
    target_table = Column(String(255), nullable=False)
    target_schema = Column(String(255))
    target_column = Column(String(255))
    source_column = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Relationship strength and confidence
    confidence_score = Column(DECIMAL(3, 2))  # 0-1 confidence score
    relationship_strength = Column(String(20))  # strong, moderate, weak
    
    # Discovery metadata
    discovered_by = Column(String(20))  # manual, llm, schema_analysis
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="relationships")
    
    __table_args__ = (
        Index('idx_relationship_table', 'table_id'),
        Index('idx_relationship_target', 'target_table'),
    )


class SampleDataMetadata(Base):
    """Stores sample data from tables for analysis and documentation."""
    
    __tablename__ = 'sample_data_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    sample_set_name = Column(String(100), default='default')  # For multiple sample sets
    sample_data = Column(JSONB, nullable=False)  # Array of sample records
    sample_size = Column(Integer, nullable=False)
    sampling_method = Column(String(50))  # random, stratified, systematic
    sampling_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Sample metadata
    total_rows_at_sampling = Column(Integer)
    sample_percentage = Column(DECIMAL(5, 2))
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="sample_data")
    
    __table_args__ = (
        Index('idx_sample_table', 'table_id'),
        Index('idx_sample_date', 'sampling_date'),
    )


class ProcessingStatsMetadata(Base):
    """Stores statistics about metadata generation processes."""
    
    __tablename__ = 'processing_stats_metadata'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    # Processing information
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_duration_seconds = Column(DECIMAL(10, 3), nullable=False)
    
    # LLM usage stats
    total_tokens = Column(Integer)
    estimated_cost = Column(DECIMAL(10, 4))
    model_used = Column(String(100))
    
    # Processing steps
    steps = Column(JSONB)  # Detailed step-by-step timing
    optional_sections = Column(JSONB)  # Which optional sections were included
    
    # Processing metadata
    version = Column(String(50))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    table = relationship("TableMetadata", back_populates="processing_stats")
    
    __table_args__ = (
        Index('idx_processing_table', 'table_id'),
        Index('idx_processing_date', 'start_time'),
        Index('idx_processing_success', 'success'),
    )


# Additional models for extended functionality

class BusinessGlossary(Base):
    """Business glossary terms for consistent metadata."""
    
    __tablename__ = 'business_glossary'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term = Column(String(255), unique=True, nullable=False)
    definition = Column(Text, nullable=False)
    category = Column(String(100))
    aliases = Column(JSONB)  # Alternative terms
    related_terms = Column(JSONB)  # Related term IDs
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255))
    
    __table_args__ = (
        Index('idx_glossary_term', 'term'),
        Index('idx_glossary_category', 'category'),
    )


class MetadataVersion(Base):
    """Version control for metadata changes."""
    
    __tablename__ = 'metadata_version'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id = Column(UUID(as_uuid=True), ForeignKey('table_metadata.id'), nullable=False)
    
    version_number = Column(Integer, nullable=False)
    change_type = Column(String(50), nullable=False)  # create, update, delete
    changed_fields = Column(JSONB)  # List of changed field names
    old_values = Column(JSONB)  # Previous values
    new_values = Column(JSONB)  # New values
    
    change_reason = Column(Text)
    changed_by = Column(String(255))
    approved_by = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_version_table', 'table_id'),
        Index('idx_version_number', 'version_number'),
        Index('idx_version_date', 'created_at'),
    ) 