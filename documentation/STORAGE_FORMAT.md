# Metadata Storage Format

## Overview

The metadata storage system organizes files using a `db.schema.table` directory structure to prevent conflicts and provide clear organization.

## Directory Structure

```
metadata_storage/
├── database_name/
│   ├── schema_name/
│   │   ├── table_name.json
│   │   └── another_table.json
│   └── another_schema/
│       └── table_name.json
└── another_database/
    └── public/
        └── table_name.json
```

## Benefits

- **No Conflicts**: Same table names in different databases/schemas don't conflict
- **Clear Organization**: Directory structure mirrors your database hierarchy
- **Easy Navigation**: Browse metadata by database → schema → table
- **Scalable**: Works efficiently with large numbers of tables

## Example Usage

### API Endpoints

```bash
# Store metadata for a table
curl -X POST http://localhost:8000/api/v1/metadata/store \
  -H "Content-Type: application/json" \
  -d '{
    "db_name": "postgres",
    "schema_name": "public",
    "table_name": "users",
    "metadata": {...}
  }'

# Retrieve metadata
curl http://localhost:8000/api/v1/metadata/stored/postgres/public/users

# List all tables with metadata for a database
curl http://localhost:8000/api/v1/metadata/tables/postgres
```

### Python Code

```python
from metadata_builder.utils.storage_utils import (
    get_metadata_storage_path,
    get_fully_qualified_table_name
)

# Get storage path for a table
path = get_metadata_storage_path("postgres", "public", "users")
# Returns: metadata_storage/postgres/public/users.json

# Get fully qualified name
name = get_fully_qualified_table_name("postgres", "public", "users")  
# Returns: "postgres.public.users"
```

## File Format

Each metadata file contains:

```json
{
  "database_name": "postgres",
  "schema_name": "public",
  "table_name": "users",
  "table_metadata": {
    "description": "User accounts table",
    "purpose": "Store user account information"
  },
  "column_metadata": {
    "id": {
      "description": "Primary key",
      "data_type": "integer"
    },
    "email": {
      "description": "User email address", 
      "data_type": "varchar"
    }
  },
  "last_updated": "2024-01-01T00:00:00Z"
}
```

## Best Practices

1. **Consistent Naming**: Use consistent database, schema, and table names
2. **Regular Cleanup**: Remove metadata files when tables are dropped
3. **Backup Strategy**: Include `metadata_storage/` in your backup strategy
4. **Access Control**: Secure the metadata_storage directory appropriately

## Integration

The storage format works seamlessly with:

- **Web Interface**: Frontend automatically handles the directory structure
- **API**: All endpoints use the consistent format
- **CLI Tools**: Both interactive and command-line tools
- **Background Jobs**: Metadata generation and processing 