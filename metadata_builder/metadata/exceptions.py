"""Custom exceptions for metadata generation."""

class MetadataError(Exception):
    """Base class for all metadata-related exceptions."""
    pass

class LLMError(MetadataError):
    """Base class for all LLM-related exceptions."""
    pass

class LLMEmptyResponseError(LLMError):
    """Exception raised when LLM returns an empty response."""
    pass

class LLMConnectionError(LLMError):
    """Exception raised when there is a connection error to the LLM API."""
    pass

class LLMRateLimitError(LLMError):
    """Exception raised when the LLM API rate limit is exceeded."""
    pass

class LLMResponseParsingError(LLMError):
    """Exception raised when there is an error parsing the LLM response."""
    pass

class DatabaseError(MetadataError):
    """Base class for all database-related exceptions."""
    pass

class DatabaseConnectionError(DatabaseError):
    """Exception raised when there is a connection error to the database."""
    pass

class DatabaseQueryError(DatabaseError):
    """Exception raised when there is an error with a database query."""
    pass

class MetadataValidationError(MetadataError):
    """Exception raised when metadata validation fails."""
    pass

class MetadataGenerationError(MetadataError):
    """Exception raised when there is an error generating metadata."""
    pass

class ConfigurationError(MetadataError):
    """Exception raised when there is an error with configuration."""
    pass 