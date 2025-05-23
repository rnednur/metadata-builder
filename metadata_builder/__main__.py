#!/usr/bin/env python3
"""
Entry point for executing metadata_builder as a module.
Usage: python -m metadata_builder
"""

from .cli.main import main

if __name__ == "__main__":
    main() 