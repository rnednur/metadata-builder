# Project Structure

This document explains the organized structure of the Metadata Builder project.

## 📁 **New Organized Structure**

```
metadata-builder/
├── 📁 metadata_builder/           # Main package directory
│   ├── __init__.py                # Package initialization & main exports
│   ├── __main__.py                # Entry point for `python -m metadata_builder`
│   │
│   ├── 📁 cli/                    # Command-line interfaces
│   │   ├── __init__.py            # CLI package exports
│   │   ├── __main__.py            # Entry point for `python -m metadata_builder.cli`
│   │   ├── main.py                # Interactive CLI (MetadataGenerator class)
│   │   └── cli.py                 # Non-interactive CLI for automation
│   │
│   ├── 📁 core/                   # Core business logic
│   │   ├── __init__.py            # Core package exports
│   │   ├── generate_table_metadata.py  # Main metadata generation logic
│   │   ├── semantic_models.py     # LookML and semantic model generation
│   │   └── llm_service.py         # LLM client and API interactions
│   │
│   ├── 📁 config/                 # Configuration management
│   │   ├── __init__.py            # Config package exports
│   │   ├── config.py              # Configuration loading and management
│   │   └── config.yaml            # Default configuration file
│   │
│   ├── 📁 utils/                  # Utility functions
│   │   ├── __init__.py            # Utils package exports
│   │   ├── database_handler.py    # Generic database handler
│   │   ├── database_handlers.py   # Database-specific handlers
│   │   ├── metadata_utils.py      # Metadata extraction utilities
│   │   ├── token_counter.py       # LLM token counting
│   │   ├── compute_data_quality_metrics.py
│   │   ├── compute_numerical_stats.py
│   │   ├── extract_categorical_values.py
│   │   ├── extract_constraints.py
│   │   └── identify_column_types.py
│   │
│   ├── 📁 database/               # Database-specific code
│   │   ├── __init__.py
│   │   └── enums.py               # Database type enumerations
│   │
│   └── 📁 metadata/               # Metadata storage and exceptions
│       ├── __init__.py
│       └── exceptions.py          # Custom exception classes
│
├── 📁 tests/                      # Test suite
│   ├── __init__.py
│   ├── test_config.py
│   └── test_lookml.py
│
├── 📁 .github/workflows/          # CI/CD automation
│   └── ci.yml                     # GitHub Actions workflow
│
├── main.py                        # Backwards compatibility script
├── cli.py                         # Backwards compatibility script
├── setup.py                       # Package setup (legacy)
├── pyproject.toml                 # Modern package configuration
├── requirements.txt               # Dependencies
├── README.md                      # Project documentation
├── CONTRIBUTING.md                # Contribution guidelines
├── SECURITY.md                    # Security policy
├── CHANGELOG.md                   # Version history
├── LICENSE                        # MIT license
├── Dockerfile                     # Container configuration
├── .gitignore                     # Git ignore rules
└── MANIFEST.in                    # Package manifest
```

## 🎯 **Key Improvements**

### **1. Professional Package Structure**
- ✅ Proper Python package hierarchy
- ✅ Clear separation of concerns
- ✅ Standard directory layout
- ✅ Proper `__init__.py` files with exports

### **2. Import Organization**
- ✅ Relative imports throughout the package
- ✅ Clean import paths
- ✅ No circular import issues
- ✅ Proper module dependencies

### **3. Entry Points**
- ✅ `metadata-builder` - Interactive CLI
- ✅ `metadata-builder-cli` - Automation CLI
- ✅ `python -m metadata_builder` - Module execution
- ✅ Backwards compatibility scripts

### **4. Logical Grouping**

#### **CLI Package** (`metadata_builder.cli`)
- Interactive user interface
- Command-line automation tools
- User interaction logic

#### **Core Package** (`metadata_builder.core`)
- Business logic
- Metadata generation algorithms
- LLM integration
- Semantic model generation

#### **Config Package** (`metadata_builder.config`)
- Configuration management
- Database connection handling
- Settings validation

#### **Utils Package** (`metadata_builder.utils`)
- Database handlers
- Utility functions
- Data processing tools
- Token counting

## 🚀 **Usage Examples**

### **As Installed Package**
```bash
# Install the package
pip install metadata-builder

# Use CLI commands
metadata-builder
metadata-builder-cli --db mydb --table users

# Use as Python module
python -m metadata_builder
```

### **As Development Package**
```bash
# Install in development mode
pip install -e .

# Import in Python code
import metadata_builder
from metadata_builder import generate_complete_table_metadata
from metadata_builder.cli import MetadataGenerator
```

### **Backwards Compatibility**
```bash
# These still work but show deprecation warnings
python main.py
python cli.py
```

## 📦 **Distribution Ready**

The new structure is fully compatible with:
- ✅ PyPI distribution
- ✅ Docker containerization
- ✅ GitHub Actions CI/CD
- ✅ Modern Python packaging standards
- ✅ IDE auto-completion and navigation

## 🔄 **Migration Notes**

### **For Users**
- No breaking changes for CLI usage
- Package imports may need updating if used as library
- New entry points available

### **For Developers**
- All imports now use relative paths
- Clear module boundaries
- Better IDE support
- Easier testing and debugging

## 🎉 **Benefits**

1. **Professional Standards**: Follows Python packaging best practices
2. **Maintainability**: Clear code organization and dependencies
3. **Scalability**: Easy to add new features and modules
4. **Distribution**: Ready for PyPI and other package managers
5. **Development**: Better IDE support and debugging experience
6. **Testing**: Easier to write and organize tests
7. **Documentation**: Clear structure for documentation generation 