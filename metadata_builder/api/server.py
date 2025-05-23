#!/usr/bin/env python3
"""
Server script for running the Metadata Builder API.
"""

import argparse
import logging
import uvicorn
from .app import app

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the API server."""
    parser = argparse.ArgumentParser(description="Metadata Builder API Server")
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    parser.add_argument(
        "--log-level", 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)"
    )
    parser.add_argument(
        "--access-log", 
        action="store_true", 
        help="Enable access logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info(f"Starting Metadata Builder API server on {args.host}:{args.port}")
    
    # Run the server
    uvicorn.run(
        "metadata_builder.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # reload doesn't work with multiple workers
        log_level=args.log_level,
        access_log=args.access_log
    )


if __name__ == "__main__":
    main() 