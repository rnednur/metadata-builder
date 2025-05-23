#!/usr/bin/env python3
"""
Backwards compatibility entry point for main.py.
Use 'metadata-builder' command or 'python -m metadata_builder.cli.main' instead.
"""

import sys
import warnings

# Warn about deprecated usage
warnings.warn(
    "Direct execution of main.py is deprecated. "
    "Use 'metadata-builder' command or 'python -m metadata_builder.cli.main' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import and run the actual main function
try:
    from metadata_builder.cli.main import main
    main()
except ImportError as e:
    print(f"Error: Could not import metadata_builder. {e}", file=sys.stderr)
    print("Please install the package with: pip install -e .", file=sys.stderr)
    sys.exit(1) 