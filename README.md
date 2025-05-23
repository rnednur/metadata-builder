# Metadata Builder

[![CI/CD Pipeline](https://github.com/yourusername/metadata-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/metadata-builder/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/metadata-builder.svg)](https://badge.fury.io/py/metadata-builder)
[![Python versions](https://img.shields.io/pypi/pyversions/metadata-builder.svg)](https://pypi.org/project/metadata-builder/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/yourusername/metadata-builder/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/metadata-builder)

An interactive CLI tool for generating structured metadata from database tables, with LLM-enhanced capabilities.

## Features

- Connect to various database types (PostgreSQL, MySQL, SQLite, Oracle, BigQuery, Kinetica, DuckDB)
- Inspect database schemas and tables
- Generate structured metadata for tables
- Interactive prompts for metadata enrichment
- LLM integration for intelligent metadata suggestions and analysis
- **NEW: LookML semantic model generation** - Generate LookML views and explores automatically
- **NEW: REST API support** - Programmatic access to all metadata builder functionality
- Automatic identification of categorical and numerical columns
- Statistical analysis of column data quality and distributions
- Generation of column-level business definitions
- Table-level insights and relationship analysis
- Advanced CLI for automation and scripting
- Local configuration via `.config.yaml` for easy customization

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rnednur/metadata-builder.git
cd metadata-builder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file in the root directory with the following content:
```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_MODEL=gpt-4-turbo-preview

# Log Configuration
LOG_LEVEL=INFO

# Token Usage Tracking
ENABLE_TOKEN_TRACKING=true
MAX_TOKENS_PER_REQUEST=8192

# Retry Configuration
MAX_RETRY_ATTEMPTS=3
RETRY_INITIAL_WAIT_SECONDS=1
RETRY_MAX_WAIT_SECONDS=10
```

4. (Optional) Configure local settings:
Copy the example configuration file to create your own local configuration:
```bash
cp .config.yaml.example .config.yaml
```
Edit `.config.yaml` to customize database connections and other settings.

## Usage

### Interactive Mode

Run the interactive CLI tool:
```bash
python main.py
```

Follow the interactive prompts to:
1. Add database connections
2. Connect to a database
3. Select schema and table
4. Edit column metadata
5. Generate and save metadata YAML
6. Push metadata to your database
7. Generate advanced metadata with LLM analysis

### API Server

Start the REST API server for programmatic access:

```bash
# Start the API server
metadata-builder-api

# Or with custom options
metadata-builder-api --host 0.0.0.0 --port 8000 --workers 4
```

The API provides comprehensive endpoints for:
- Database connection management
- Schema and table inspection  
- Metadata generation (sync and async)
- LookML model generation
- Background job tracking

**Interactive API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Docker Deployment:**
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.api.yml up

# Or build manually
docker build -f Dockerfile.api -t metadata-builder-api .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key metadata-builder-api
```

**API Usage Example:**
```python
import requests

# Create a database connection
response = requests.post("http://localhost:8000/api/v1/database/connections", json={
    "name": "my_db",
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "user",
    "password": "password",
    "database": "mydb"
})

# Generate metadata
response = requests.post("http://localhost:8000/api/v1/metadata/generate", json={
    "db_name": "my_db",
    "table_name": "users",
    "schema_name": "public"
})
metadata = response.json()
```

For detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

### Command-line Mode

For automation and scripting, use the dedicated CLI tool:
```bash
python cli.py --db your_database --table your_table --schema your_schema
```

#### LookML Generation

Generate LookML semantic models directly from the command line:
```bash
# Basic LookML generation
python cli.py --db mydb --table users --generate-lookml

# Advanced LookML generation with options
python cli.py --db mydb --table users --generate-lookml \
  --model-name "user_analytics" \
  --include-derives \
  --include-explores \
  --additional-prompt "Focus on user engagement metrics" \
  --output "user_model.yaml" \
  --format yaml \
  --summary
```

Additional CLI options:
```
--schema PUBLIC          Schema name (default: public)
--sql-file FILE_PATH     Path to file containing custom SQL query
--sample-size 100        Sample size for each sample (default: 100)
--num-samples 5          Number of samples to take (default: 5)
--output FILE_PATH       Output file path
--format [json|yaml]     Output format (default: json)
--summary                Display a summary of the metadata after generation
```

#### LookML-specific options:
```
--generate-lookml        Generate LookML semantic model instead of metadata
--model-name NAME        Name for the LookML model (default: table_name_model)
--include-derives        Include derived table suggestions in LookML
--include-explores       Include explore definitions in LookML (default: True)
--additional-prompt TEXT Additional requirements for LookML generation
```

Example with custom options:
```bash
python cli.py --db sales_db --table customers --schema sales \
              --sample-size 200 --num-samples 3 --format yaml \
              --summary --output ./metadata/customer_metadata.yaml
```

### Oracle Database Configuration

Oracle database connections can be configured using three different methods:

1. **Service Name Connection**:
```yaml
sample_oracle_service:
  type: oracle
  host: localhost
  port: 1521
  username: system
  password: ${ORACLE_PASSWORD}
  service_name: XEPDB1
```

2. **SID Connection**:
```yaml
sample_oracle_sid:
  type: oracle
  host: localhost
  port: 1521
  username: system
  password: ${ORACLE_PASSWORD}
  sid: XE
```

3. **TNS Connection**:
```yaml
sample_oracle_tns:
  type: oracle
  username: system
  password: ${ORACLE_PASSWORD}
  tns_name: my_tns_name
```

Note: Oracle connections require the `cx_Oracle` Python package. Make sure to install the Oracle Client libraries on your system. See the [cx_Oracle documentation](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html) for instructions.

## Configuration Options

### Local Configuration with `.config.yaml`

The tool supports loading configuration from a local `.config.yaml` file in your working directory. This file takes precedence over the default configuration files, allowing you to customize settings without modifying the project files.

To use this feature:

1. Copy the example configuration to create your own:
   ```bash
   cp .config.yaml.example .config.yaml
   ```

2. Edit `.config.yaml` with your preferred settings, including:
   - Database connections
   - LLM API configuration
   - Metadata generation options

3. The application will automatically detect and use this file when present.

This approach is especially useful for:
- Storing sensitive database credentials securely
- Customizing settings per environment
- Using different settings across multiple projects
- Keeping your custom configuration separate from version control

### Environment Variables

In addition to the config file, sensitive information can also be set via environment variables:

- Referenced directly in the code
- Used in configuration files with `${VAR_NAME}` syntax
- Loaded from `.env` file (using python-dotenv)

## Advanced Metadata Generation

The advanced metadata generation uses LLM to analyze your table structure and data, providing:

1. **Column Classification**: Automatic identification of categorical vs. numerical columns
2. **Statistical Analysis**: Comprehensive statistics for numerical columns (min, max, percentiles)
3. **Data Quality Metrics**: Completeness, uniqueness, and common issues detection
4. **Column Metadata**: Business-friendly descriptions, potential relationships, and validations
5. **Categorical Definitions**: Definitions for unique values in categorical columns
6. **Table Insights**: Purpose, use cases, relationships, and business rules suggestions

Advanced metadata is generated when:
- Selecting "Generate advanced metadata with LLM" in the interactive menu
- Using the `cli.py` script with appropriate parameters

## LLM Integration

The tool uses OpenAI's API to enhance metadata generation. To use this feature:

1. Ensure you have set the `OPENAI_API_KEY` in your `.env` file
2. The LLM will be used to:
   - Generate column descriptions
   - Identify business terms
   - Define categorical values
   - Suggest data quality rules
   - Identify potential relationships
   - Generate table-level insights
   - Recommend business rules

## Project Structure

- `main.py`: Main interactive CLI application
- `cli.py`: Command-line interface for automation
- `generate_table_metadata.py`: Core functions for advanced metadata generation
- `config/`: Configuration management
- `metadata/`: Generated metadata and related utilities
- `utils/`: Utility functions and helpers including metadata extraction utilities
- `llm_service.py`: LLM integration service

## Development

### Adding Support for New Database Types

To add support for a new database type:
1. Update the `add_database_connection` method in `main.py`
2. Add the required SQLAlchemy dialect to `requirements.txt`

### Extending Metadata Structure

To extend the metadata structure:
1. Update the `generate_metadata_yaml` method in `main.py`
2. Update any related functions that process metadata
3. For advanced metadata, modify the relevant functions in `generate_table_metadata.py`

### Adding New Analysis Features

To add new analysis features:
1. Implement the analysis function in the appropriate utility module
2. Update the `generate_complete_table_metadata` function to include the new analysis
3. Update the LLM prompts to incorporate the new information

## Installation Options

### PyPI Installation (Recommended)

```bash
# Basic installation
pip install metadata-builder

# With all optional dependencies
pip install metadata-builder[all]

# With specific database support
pip install metadata-builder[oracle,bigquery]

# Development installation
pip install metadata-builder[dev]
```

### Docker Installation

```bash
# Pull the latest image
docker pull yourusername/metadata-builder:latest

# Run interactively
docker run -it --rm \
  -v $(pwd)/.config.yaml:/app/.config.yaml \
  -v $(pwd)/metadata:/app/metadata \
  -e OPENAI_API_KEY=your_key_here \
  yourusername/metadata-builder:latest

# Run CLI command
docker run --rm \
  -v $(pwd)/.config.yaml:/app/.config.yaml \
  -v $(pwd)/metadata:/app/metadata \
  -e OPENAI_API_KEY=your_key_here \
  yourusername/metadata-builder:latest \
  metadata-builder-cli --db mydb --table users --summary
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/metadata-builder.git
cd metadata-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Run linting: `black . && flake8 . && mypy .`
6. Submit a pull request

### Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=metadata_builder

# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Build package
python -m build

# Install pre-commit hooks
pre-commit install
```

## Security

Please see our [Security Policy](SECURITY.md) for information about reporting security vulnerabilities.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes in each version.

## Support

- **Documentation**: Check this README and inline code documentation
- **Issues**: [GitHub Issues](https://github.com/yourusername/metadata-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/metadata-builder/discussions)
- **Email**: your.email@example.com

## Acknowledgments

- Thanks to all contributors who have helped improve this project
- Built with [SQLAlchemy](https://www.sqlalchemy.org/) for database connectivity
- Uses [OpenAI API](https://openai.com/api/) for LLM-enhanced metadata generation
- CLI built with [Rich](https://rich.readthedocs.io/) and [Questionary](https://questionary.readthedocs.io/)

## Roadmap

- [ ] Support for additional semantic model types (dbt, Cube.js)
- [ ] Web-based interface
- [ ] Advanced data profiling capabilities
- [ ] Integration with data catalogs
- [ ] Real-time metadata synchronization
- [ ] Custom metadata templates
- [ ] API for programmatic access

---

**Star this repository if you find it useful!** ⭐ 