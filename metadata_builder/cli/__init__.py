"""CLI interfaces for metadata builder."""

from .main import MetadataGenerator, main as interactive_main
from .cli import main as cli_main

__all__ = ['MetadataGenerator', 'interactive_main', 'cli_main'] 