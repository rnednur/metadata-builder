#!/usr/bin/env python3
"""
Backwards compatibility entry point for cli.py.
Use 'metadata-builder-cli' command or 'python -m metadata_builder.cli.cli' instead.
"""

import sys
import warnings

# Warn about deprecated usage
warnings.warn(
    "Direct execution of cli.py is deprecated. "
    "Use 'metadata-builder-cli' command or 'python -m metadata_builder.cli.cli' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the actual main function
try:
    from metadata_builder.cli.cli import main
    main()
except ImportError as e:
    print(f"Error: Could not import metadata_builder. {e}", file=sys.stderr)
    print("Please install the package with: pip install -e .", file=sys.stderr)
    sys.exit(1) 