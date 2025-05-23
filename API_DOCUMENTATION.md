# Metadata Builder API Documentation

A comprehensive REST API for generating structured metadata from database tables with LLM-enhanced capabilities.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Base URL](#base-url)
5. [API Endpoints](#api-endpoints)
6. [Data Models](#data-models)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Rate Limiting](#rate-limiting)
10. [SDKs and Client Libraries](#sdks-and-client-libraries)

## Overview

The Metadata Builder API provides programmatic access to all the functionality of the metadata-builder tool:

- **Database Connection Management**: Create, test, and manage database connections
- **Schema Inspection**: Explore database schemas and tables
- **Metadata Generation**: Generate rich table metadata with LLM analysis
- **LookML Generation**: Create LookML semantic models automatically
- **Background Jobs**: Handle long-running operations asynchronously
- **Health Monitoring**: Check API and service health

### Supported Database Types

- PostgreSQL
- MySQL
- SQLite
- Oracle
- BigQuery
- Kinetica
- DuckDB

## Getting Started

### Installation

The API server is included with the metadata-builder package:

```bash
pip install metadata-builder
```

### Running the API Server

#### Basic Usage

```bash
# Start the API server
python -m metadata_builder.api.server

# Or use the CLI entry point
metadata-builder-api
```

#### Development Mode

```bash
# Start with auto-reload for development
python -m metadata_builder.api.server --reload --log-level debug
```

#### Production Deployment

```bash
# Start with multiple workers for production
python -m metadata_builder.api.server --host 0.0.0.0 --port 8000 --workers 4
```

#### Docker Deployment

```bash
# Build the Docker image
docker build -t metadata-builder-api .

# Run the container
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_api_key \
  -v $(pwd)/.config.yaml:/app/.config.yaml \
  metadata-builder-api
```

### Server Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | 0.0.0.0 | Host to bind to |
| `--port` | 8000 | Port to bind to |
| `--reload` | False | Enable auto-reload for development |
| `--workers` | 1 | Number of worker processes |
| `--log-level` | info | Log level (debug, info, warning, error, critical) |
| `--access-log` | False | Enable access logging |

## Authentication

### Environment Variables

Set the following environment variables for LLM operations:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
export OPENAI_API_BASE_URL=https://api.openai.com/v1  # Optional
export OPENAI_API_MODEL=gpt-4-turbo-preview  # Optional
```

### Configuration File

Alternatively, configure via `.config.yaml`:

```yaml
llm_api:
  api_key: ${OPENAI_API_KEY}
  base_url: https://api.openai.com/v1
  model: gpt-4-turbo-preview
```

## Base URL

When running locally:
```
http://localhost:8000
```

All API endpoints are prefixed with `/api/v1`.

## API Endpoints

### System Endpoints

#### Health Check
```http
GET /health
```

Returns the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "database_connections": 3,
  "llm_api_status": "configured"
}
```

#### API Information
```http
GET /api/v1/info
```

Returns information about the API capabilities and endpoints.

### Database Connection Management

#### List Connections
```http
GET /api/v1/database/connections
```

Returns all configured database connections.

#### Create Connection
```http
POST /api/v1/database/connections
```

**Request Body:**
```json
{
  "name": "production_db",
  "type": "postgresql",
  "host": "localhost",
  "port": 5432,
  "username": "user",
  "password": "password",
  "database": "mydb"
}
```

#### Get Connection
```http
GET /api/v1/database/connections/{connection_name}
```

#### Delete Connection
```http
DELETE /api/v1/database/connections/{connection_name}
```

#### Test Connection
```http
POST /api/v1/database/connections/{connection_name}/test
```

### Schema Inspection

#### Get Database Schemas
```http
GET /api/v1/database/connections/{connection_name}/schemas
```

Returns all schemas and their tables for a database connection.

#### Get Schema Tables
```http
GET /api/v1/database/connections/{connection_name}/schemas/{schema_name}/tables
```

Returns detailed information about tables in a specific schema.

#### Get Table Information
```http
GET /api/v1/database/connections/{connection_name}/schemas/{schema_name}/tables/{table_name}
```

Returns detailed information about a specific table.

### Metadata Generation

#### Generate Metadata (Synchronous)
```http
POST /api/v1/metadata/generate
```

**Request Body:**
```json
{
  "db_name": "production_db",
  "table_name": "users",
  "schema_name": "public",
  "sample_size": 100,
  "num_samples": 5,
  "include_relationships": true,
  "include_data_quality": true,
  "include_business_rules": true
}
```

#### Generate Metadata (Asynchronous)
```http
POST /api/v1/metadata/generate/async
```

Returns a job ID for tracking the operation status.

### LookML Generation

#### Generate LookML (Synchronous)
```http
POST /api/v1/metadata/lookml/generate
```

**Request Body:**
```json
{
  "db_name": "production_db",
  "schema_name": "public",
  "table_names": ["users", "orders"],
  "model_name": "user_analytics_model",
  "include_explores": true,
  "include_derived_tables": false
}
```

#### Generate LookML (Asynchronous)
```http
POST /api/v1/metadata/lookml/generate/async
```

### Background Job Management

#### Get Job Status
```http
GET /api/v1/metadata/jobs/{job_id}
```

Returns the status and results of a background job.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "progress": 1.0,
  "result": {
    "database_name": "production_db",
    "table_name": "users",
    "metadata": {...}
  }
}
```

## Data Models

### DatabaseConnectionRequest

```json
{
  "name": "string",
  "type": "postgresql|mysql|sqlite|oracle|bigquery|kinetica|duckdb",
  "host": "string",
  "port": 5432,
  "username": "string",
  "password": "string",
  "database": "string",
  "service_name": "string",  // Oracle only
  "sid": "string",           // Oracle only
  "tns_name": "string",      // Oracle only
  "project_id": "string",    // BigQuery only
  "credentials_path": "string"  // BigQuery only
}
```

### MetadataGenerationRequest

```json
{
  "db_name": "string",
  "table_name": "string",
  "schema_name": "public",
  "analysis_sql": "string",
  "sample_size": 100,
  "num_samples": 5,
  "include_relationships": true,
  "include_aggregation_rules": true,
  "include_query_rules": true,
  "include_data_quality": true,
  "include_query_examples": true,
  "include_additional_insights": true,
  "include_business_rules": true,
  "include_categorical_definitions": true
}
```

### LookMLGenerationRequest

```json
{
  "db_name": "string",
  "schema_name": "string",
  "table_names": ["string"],
  "model_name": "string",
  "include_derived_tables": false,
  "include_explores": true,
  "additional_prompt": "string",
  "generation_type": "full",
  "existing_lookml": "string",
  "token_threshold": 8000
}
```

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

### Error Response Format

```json
{
  "error": "Validation Error",
  "message": "Invalid request parameters",
  "details": {
    "field": "table_name",
    "issue": "Field is required"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Examples

### Complete Workflow Example

```python
import requests
import time

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

# 1. Create a database connection
connection_data = {
    "name": "my_postgres_db",
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "postgres",
    "password": "password",
    "database": "mydb"
}

response = requests.post(f"{BASE_URL}/database/connections", json=connection_data)
print(f"Connection created: {response.status_code}")

# 2. Test the connection
response = requests.post(f"{BASE_URL}/database/connections/my_postgres_db/test")
print(f"Connection test: {response.json()}")

# 3. List schemas and tables
response = requests.get(f"{BASE_URL}/database/connections/my_postgres_db/schemas")
schemas = response.json()
print(f"Found {len(schemas['schemas'])} schemas")

# 4. Generate metadata asynchronously
metadata_request = {
    "db_name": "my_postgres_db",
    "table_name": "users",
    "schema_name": "public",
    "sample_size": 100,
    "num_samples": 5
}

response = requests.post(f"{BASE_URL}/metadata/generate/async", json=metadata_request)
job = response.json()
job_id = job["job_id"]
print(f"Started metadata generation job: {job_id}")

# 5. Poll for job completion
while True:
    response = requests.get(f"{BASE_URL}/metadata/jobs/{job_id}")
    job_status = response.json()
    
    print(f"Job status: {job_status['status']}")
    
    if job_status["status"] == "completed":
        metadata = job_status["result"]
        print(f"Metadata generated successfully!")
        print(f"Columns analyzed: {len(metadata['metadata']['columns'])}")
        break
    elif job_status["status"] == "failed":
        print(f"Job failed: {job_status['error']}")
        break
    
    time.sleep(5)  # Wait 5 seconds before checking again

# 6. Generate LookML model
lookml_request = {
    "db_name": "my_postgres_db",
    "schema_name": "public", 
    "table_names": ["users", "orders"],
    "model_name": "user_analytics",
    "include_explores": True
}

response = requests.post(f"{BASE_URL}/metadata/lookml/generate", json=lookml_request)
lookml_result = response.json()
print(f"LookML model generated: {lookml_result['model_name']}")
```

### cURL Examples

#### Create a connection
```bash
curl -X POST "http://localhost:8000/api/v1/database/connections" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_db",
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "username": "postgres",
    "password": "password",
    "database": "testdb"
  }'
```

#### Generate metadata
```bash
curl -X POST "http://localhost:8000/api/v1/metadata/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "test_db",
    "table_name": "users",
    "schema_name": "public"
  }'
```

#### Check health
```bash
curl "http://localhost:8000/health"
```

## Rate Limiting

The API implements basic rate limiting to prevent abuse:

- **Metadata Generation**: Maximum 10 requests per minute per IP
- **LookML Generation**: Maximum 5 requests per minute per IP
- **Other Endpoints**: Maximum 100 requests per minute per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## SDKs and Client Libraries

### Python SDK

A Python SDK is available for easier integration:

```python
from metadata_builder_client import MetadataBuilderClient

# Initialize client
client = MetadataBuilderClient(base_url="http://localhost:8000")

# Create connection
client.create_connection(
    name="my_db",
    db_type="postgresql",
    host="localhost",
    port=5432,
    username="user",
    password="password",
    database="mydb"
)

# Generate metadata
metadata = client.generate_metadata("my_db", "users", "public")

# Generate LookML
lookml = client.generate_lookml("my_db", "public", ["users", "orders"], "analytics_model")
```

### JavaScript/TypeScript SDK

```typescript
import { MetadataBuilderClient } from 'metadata-builder-client';

const client = new MetadataBuilderClient({ baseUrl: 'http://localhost:8000' });

// Create connection
await client.createConnection({
  name: 'my_db',
  type: 'postgresql',
  host: 'localhost',
  port: 5432,
  username: 'user',
  password: 'password',
  database: 'mydb'
});

// Generate metadata
const metadata = await client.generateMetadata({
  dbName: 'my_db',
  tableName: 'users',
  schemaName: 'public'
});
```

## Interactive API Documentation

When the API server is running, interactive documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These interfaces allow you to explore the API, test endpoints, and see request/response schemas interactively.

## Support and Contributing

- **Issues**: [GitHub Issues](https://github.com/rnednur/metadata-builder/issues)
- **Documentation**: [Project README](https://github.com/rnednur/metadata-builder)
- **Contributing**: [Contributing Guide](https://github.com/rnednur/metadata-builder/blob/main/CONTRIBUTING.md)

## Changelog

See [CHANGELOG.md](https://github.com/rnednur/metadata-builder/blob/main/CHANGELOG.md) for API version history and changes. 