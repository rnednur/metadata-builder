# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Planned features for future releases

### Changed
- Improvements to existing features

### Deprecated
- Features that will be removed in future versions

### Removed
- Features removed in this version

### Fixed
- Bug fixes

### Security
- Security improvements

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Metadata Builder
- Interactive CLI for database metadata generation
- Command-line interface for automation and scripting
- Support for multiple database types:
  - PostgreSQL
  - MySQL
  - SQLite
  - Oracle
  - BigQuery
  - DuckDB
  - Kinetica
- LLM-enhanced metadata generation using OpenAI API
- LookML semantic model generation
- Advanced metadata analysis including:
  - Column type identification
  - Statistical analysis for numerical columns
  - Data quality metrics
  - Categorical value extraction
  - Constraint analysis
- Flexible configuration system with environment variable support
- Local configuration override with `.config.yaml`
- Comprehensive logging and error handling
- Rich CLI interface with progress indicators
- Export to JSON and YAML formats
- Docker containerization support
- Comprehensive test suite
- CI/CD pipeline with GitHub Actions
- Security policy and vulnerability reporting
- Contributing guidelines for open source development

### Features
- **Interactive Mode**: User-friendly CLI with guided prompts
- **Automation Mode**: Command-line interface for scripting
- **Multi-Database Support**: Connect to various database types
- **LLM Integration**: AI-powered metadata enhancement
- **Semantic Models**: Generate LookML views and explores
- **Data Profiling**: Automatic column analysis and statistics
- **Quality Metrics**: Data completeness and uniqueness analysis
- **Flexible Output**: JSON and YAML export formats
- **Configuration Management**: Environment variables and config files
- **Extensible Architecture**: Easy to add new database types and features

### Technical Details
- Python 3.8+ support
- SQLAlchemy for database connectivity
- OpenAI API integration for LLM features
- Rich and Questionary for CLI interface
- Comprehensive error handling and retry logic
- Type hints throughout the codebase
- Modular architecture for easy extension

---

## Release Notes Format

Each release will include:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed
- **Removed**: Features that were removed
- **Fixed**: Bug fixes
- **Security**: Security-related changes

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backwards compatible manner
- **PATCH**: Backwards compatible bug fixes 