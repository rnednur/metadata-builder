from enum import Enum, auto

class CatalogStatus(str, Enum):
    """Status values for catalog metadata"""
    ACTIVE = "active"
    PENDING = "pending"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ColumnType(str, Enum):
    """Types of columns for metadata classification"""
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    TEXT = "text"
    DATE = "date"
    BINARY = "binary"
    JSON = "json"
    ARRAY = "array"
    UNKNOWN = "unknown"

class DataQualityIssue(str, Enum):
    """Common data quality issues"""
    MISSING_VALUES = "missing_values"
    DUPLICATE_VALUES = "duplicate_values"
    INCONSISTENT_FORMATS = "inconsistent_formats"
    OUTLIERS = "outliers"
    INVALID_VALUES = "invalid_values"
    DATA_TYPE_MISMATCH = "data_type_mismatch"
    PRIMARY_KEY_ISSUES = "primary_key_issues"
    REFERENTIAL_INTEGRITY_ISSUES = "referential_integrity_issues" 