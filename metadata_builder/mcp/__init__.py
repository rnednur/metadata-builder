"""MCP (Model Context Protocol) server for metadata intelligence."""

# Import only servers that don't require Python 3.10+
try:
    from .server import MetadataMCPServer
    __all__ = ['MetadataMCPServer']
except ImportError:
    # Traditional MCP not available (requires Python 3.10+)
    __all__ = []

# Simple FastAPI server is always available
try:
    from .simple_fastapi_server import app as simple_fastapi_app
    __all__.append('simple_fastapi_app')
except ImportError:
    pass 