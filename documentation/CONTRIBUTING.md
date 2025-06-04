# Contributing to Metadata Builder

Thank you for your interest in contributing to Metadata Builder! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setting up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/metadata-builder.git
   cd metadata-builder
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks (optional but recommended):**
   ```bash
   pre-commit install
   ```

5. **Copy the example configuration:**
   ```bash
   cp .config.yaml.example .config.yaml
   ```

6. **Set up environment variables:**
   Create a `.env` file with your configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_API_BASE_URL=https://api.openai.com/v1
   OPENAI_API_MODEL=gpt-4-turbo-preview
   LOG_LEVEL=INFO
   ```

## Code Style and Standards

### Python Code Style

We follow PEP 8 with some modifications:

- **Line length:** 88 characters (Black default)
- **String quotes:** Use double quotes for strings
- **Import organization:** Use isort for import sorting
- **Type hints:** Required for all public functions and methods

### Code Formatting

We use the following tools for code formatting and linting:

- **Black:** Code formatting
- **flake8:** Linting
- **mypy:** Type checking
- **isort:** Import sorting

Run all checks:
```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

### Documentation

- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures
- Update README.md for user-facing changes

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=metadata_builder

# Run specific test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names that explain what is being tested
- Follow the AAA pattern: Arrange, Act, Assert
- Mock external dependencies (databases, APIs)
- Aim for high test coverage

Example test structure:
```python
def test_function_name_expected_behavior():
    """Test that function_name does expected_behavior when given specific input."""
    # Arrange
    input_data = "test_input"
    expected_result = "expected_output"
    
    # Act
    result = function_name(input_data)
    
    # Assert
    assert result == expected_result
```

## Project Structure

```
metadata-builder/
├── config/                 # Configuration management
├── utils/                  # Utility functions
├── metadata/              # Metadata storage and exceptions
├── database/              # Database-specific enums and handlers
├── tests/                 # Test files
├── main.py               # Interactive CLI entry point
├── cli.py                # Command-line interface
├── generate_table_metadata.py  # Core metadata generation
├── semantic_models.py    # Semantic model generation
└── requirements.txt      # Dependencies
```

## Adding New Features

### Database Support

To add support for a new database type:

1. **Update configuration schema** in `config/config.yaml`
2. **Add connection string logic** in `config/config.py`
3. **Create database handler** (if needed) in `utils/database_handlers.py`
4. **Update CLI prompts** in `main.py`
5. **Add tests** for the new database type
6. **Update documentation** in README.md

### Metadata Analysis Features

To add new metadata analysis capabilities:

1. **Create utility function** in appropriate module under `utils/`
2. **Update core generation logic** in `generate_table_metadata.py`
3. **Add LLM prompts** if AI analysis is needed
4. **Write comprehensive tests**
5. **Update documentation**

### Semantic Model Types

To add support for new semantic model types (dbt, Cube.js, etc.):

1. **Create new module** following the pattern of `semantic_models.py`
2. **Add CLI options** in both `main.py` and `cli.py`
3. **Implement generation logic** with LLM integration
4. **Add comprehensive tests**
5. **Update documentation**

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the coding standards
3. **Add or update tests** for your changes
4. **Update documentation** as needed
5. **Run the full test suite** and ensure all tests pass
6. **Submit a pull request** with a clear description

### Pull Request Guidelines

- **Title:** Use a clear, descriptive title
- **Description:** Explain what changes you made and why
- **Testing:** Describe how you tested your changes
- **Documentation:** Note any documentation updates needed
- **Breaking changes:** Clearly mark any breaking changes

## Issue Reporting

When reporting issues, please include:

- **Environment details:** Python version, OS, database type
- **Steps to reproduce:** Clear steps to reproduce the issue
- **Expected behavior:** What you expected to happen
- **Actual behavior:** What actually happened
- **Error messages:** Full error messages and stack traces
- **Configuration:** Relevant configuration (sanitized)

## Code Review Process

All contributions go through code review:

1. **Automated checks:** CI/CD runs tests and linting
2. **Peer review:** At least one maintainer reviews the code
3. **Feedback incorporation:** Address review comments
4. **Final approval:** Maintainer approves and merges

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Breaking changes
- **MINOR:** New features, backward compatible
- **PATCH:** Bug fixes, backward compatible

## Getting Help

- **Documentation:** Check README.md and code comments
- **Issues:** Search existing issues or create a new one
- **Discussions:** Use GitHub Discussions for questions
- **Email:** Contact maintainers for sensitive issues

## License

By contributing to Metadata Builder, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors are recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README.md acknowledgments section

Thank you for contributing to Metadata Builder! 