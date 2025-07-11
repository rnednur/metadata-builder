# Project Structure

This document provides an overview of the Metadata Builder project structure and organization.

## Root Directory

```
metadata-builder/
├── README.md                           # Main project documentation
├── LICENSE                             # MIT license
├── MANIFEST.in                         # Package manifest for PyPI
├── pyproject.toml                      # Python project configuration
├── requirements.txt                    # Python dependencies
├── setup.py                           # Package setup script
├── .gitignore                         # Git ignore rules
├── main.py                            # Interactive CLI entry point
├── cli.py                             # Command-line interface
└── logs/                              # Application logs (auto-created)
```

## Organized Subdirectories

### `/configs/` - Configuration Files
```
configs/
├── config.yaml                        # Sample configuration
└── .config.yaml.example              # Configuration template
```

### `/docker/` - Docker and Deployment
```
docker/
├── Dockerfile                         # Main application Dockerfile
├── Dockerfile.api                     # API server Dockerfile
├── docker-compose.api.yml             # API-only Docker Compose
└── docker-compose.fullstack.yml       # Full-stack Docker Compose
```

### `/scripts/` - Setup and Utility Scripts
```
scripts/
├── setup_frontend.sh                 # Frontend setup script
└── setup_frontend_simple.sh          # Simplified frontend setup
```

### `/documentation/` - Project Documentation
```
documentation/
├── README.md                          # Documentation index
├── API_DOCUMENTATION.md               # API reference
├── API_SUMMARY.md                     # API overview
├── BIGQUERY_PARTITION_SUPPORT.md     # BigQuery partitioning
├── CHANGELOG.md                       # Version history
├── CONTRIBUTING.md                    # Contribution guidelines
├── FRONTEND_INSTALLATION.md          # Frontend setup guide
├── FRONTEND_REQUIREMENTS.md          # Frontend specifications
├── IMPLEMENTATION_SUMMARY.md         # Technical implementation
├── OPTIONAL_SECTIONS_GUIDE.md        # Optional features guide
├── README_LOOKML.md                   # LookML generation guide
├── SECURITY.md                        # Security policy
├── SMART_CATEGORICAL_INTEGRATION.md  # Categorical data handling
└── STRUCTURE.md                       # This file
```

### `/metadata_builder/` - Core Python Package
```
metadata_builder/
├── __init__.py                        # Package initialization
├── __main__.py                        # Main module entry point
├── api/                               # FastAPI server components
├── config/                            # Configuration management
├── database/                          # Database connectivity
├── llm/                               # LLM integration services
├── metadata_storage/                  # Generated metadata storage (db.schema.table format)
├── models/                            # Data models and schemas
├── utils/                             # Utility functions
└── worker/                            # Background task workers
```

### `/frontend/` - React Web Interface
```
frontend/
├── package.json                       # Node.js dependencies
├── package-lock.json                  # Locked dependency versions
├── tsconfig.json                      # TypeScript configuration
├── tsconfig.node.json                 # Node TypeScript config
├── vite.config.ts                     # Vite build configuration
├── index.html                         # HTML entry point
├── Dockerfile                         # Frontend Docker image
├── nginx.conf                         # Nginx configuration
├── .env.local                         # Environment variables
├── public/                            # Static assets
├── src/                               # Source code
│   ├── components/                    # Reusable UI components
│   ├── pages/                         # Page components
│   ├── hooks/                         # Custom React hooks
│   ├── services/                      # API client services
│   ├── utils/                         # Utility functions
│   ├── types/                         # TypeScript definitions
│   ├── styles/                        # CSS and styling
│   ├── test/                          # Test utilities
│   ├── App.tsx                        # Main App component
│   └── main.tsx                       # React entry point
└── dist/                              # Build output (generated)
```

### `/tests/` - Test Suite
```
tests/
├── __init__.py                        # Test package initialization
├── test_config.py                     # Configuration tests
├── test_lookml.py                     # LookML generation tests
├── test_optional_sections.py          # Optional features tests
├── unit/                              # Unit tests
├── integration/                       # Integration tests
└── fixtures/                          # Test data and fixtures
```

### `/examples/` - Usage Examples
```
examples/
├── api_example.py                     # API usage examples
├── bigquery_partition_example.py     # BigQuery partition examples
├── cli_usage.md                       # CLI usage examples
└── config_examples/                   # Configuration examples
```

### `/metadata_storage/` - Generated Output
```
metadata_storage/
├── database_name/                     # Database-specific metadata
│   ├── schema_name/                   # Schema-specific organization
│   │   ├── table_name.json            # Table metadata files
│   │   └── another_table.json         # Additional tables
│   └── another_schema/                # Multiple schemas supported
│       └── table_name.json            # Same table name, different schema
└── another_database/                  # Multiple databases supported
    └── public/
        └── table_name.json            # Same table name, different database
```

## Key Design Principles

### 1. **Separation of Concerns**
- **Backend**: Pure Python package with CLI and API
- **Frontend**: Independent React application
- **Configuration**: Centralized in `/configs/` directory
- **Documentation**: Comprehensive and organized
- **Deployment**: Docker-first with multiple deployment options

### 2. **Modularity**
- Each major component is in its own directory
- Clear interfaces between frontend and backend
- Pluggable architecture for database connectors
- Extensible metadata generation pipeline

### 3. **Development Experience**
- Hot reloading for both frontend and backend
- Comprehensive testing setup
- Linting and formatting tools
- Clear development workflows

### 4. **Production Ready**
- Multi-stage Docker builds
- Health checks and monitoring
- Security best practices
- Scalable architecture with Redis and Celery

## File Naming Conventions

### Python Files
- `snake_case.py` for all Python modules
- `test_*.py` for test files
- `__init__.py` for package initialization

### Frontend Files
- `PascalCase.tsx` for React components
- `camelCase.ts` for utilities and services
- `kebab-case.css` for stylesheets

### Configuration Files
- `lowercase.yml` or `lowercase.yaml` for YAML configs
- `lowercase.json` for JSON configs
- `.env` for environment variables

### Documentation Files
- `UPPERCASE.md` for major documentation
- `lowercase.md` for guides and examples

## Build Artifacts

The following directories contain generated content and should not be committed:

```
# Build outputs
frontend/dist/
frontend/node_modules/
metadata_builder.egg-info/
build/
dist/

# Runtime files
logs/
*.log
.config.yaml

# Dependencies
node_modules/
__pycache__/
*.pyc
```

## Getting Started

1. **Backend Development**:
   ```bash
   pip install -e ".[dev]"
   python main.py
   ```

2. **Frontend Development**:
   ```bash
   ./scripts/setup_frontend_simple.sh
   cd frontend && npm run dev
   ```

3. **Full Stack with Docker**:
   ```bash
   docker-compose -f docker/docker-compose.fullstack.yml up
   ```

4. **API Only**:
   ```bash
   docker-compose -f docker/docker-compose.api.yml up
   ```

## Adding New Features

### Backend Components
1. Add new modules under `metadata_builder/`
2. Update `__init__.py` exports
3. Add tests in `tests/`
4. Update API endpoints if needed

### Frontend Components
1. Add components under `frontend/src/components/`
2. Add pages under `frontend/src/pages/`
3. Add services under `frontend/src/services/`
4. Update routing in `App.tsx`

### Documentation
1. Add guides to `documentation/`
2. Update `documentation/README.md` index
3. Add examples to `examples/`

This structure ensures maintainability, scalability, and clear separation of concerns while providing excellent developer experience. 