# LookML Generation Feature

This document describes the new LookML semantic model generation feature added to the Metadata Builder.

## Overview

The LookML generation feature allows you to automatically create LookML semantic models from your database tables using AI/LLM assistance. This feature can generate:

- **Views**: LookML view definitions with appropriate dimensions and measures
- **Explores**: Explore definitions with intelligent join suggestions
- **Derived Tables**: Suggestions for useful derived tables and aggregations

## Usage

### Interactive CLI

1. Start the metadata builder:
   ```bash
   python main.py
   ```

2. Connect to your database and select a table

3. Choose "Generate semantic models (LookML, dbt, etc.)" from the menu

4. Select "LookML" as the model type

5. Configure your options:
   - Model name
   - Include derived table suggestions
   - Include explore definitions
   - Additional requirements (optional)

### Command Line Interface

Generate LookML models directly from the command line:

```bash
# Basic LookML generation
python cli.py --db mydb --table users --generate-lookml

# With additional options
python cli.py --db mydb --table users --generate-lookml \
  --model-name "user_analytics" \
  --include-derives \
  --include-explores \
  --additional-prompt "Focus on user engagement metrics" \
  --output "user_model.yaml" \
  --format yaml \
  --summary
```

### Programmatic Usage

```python
from semantic_models import generate_lookml_model

# Generate LookML model
result = generate_lookml_model(
    db_name="mydb",
    schema_name="public", 
    table_names=["users", "orders"],
    model_name="ecommerce_model",
    include_derived_tables=True,
    include_explores=True,
    additional_prompt="Focus on customer analytics and revenue metrics"
)

# Access the generated content
views = result['views']
explores = result['explores']
stats = result['processing_stats']
```

## Command Line Arguments

### LookML-specific arguments:

- `--generate-lookml`: Generate LookML semantic model instead of metadata
- `--model-name`: Name for the LookML model (default: table_name_model)
- `--include-derives`: Include derived table suggestions in LookML
- `--include-explores`: Include explore definitions in LookML (default: True)
- `--additional-prompt`: Additional requirements for LookML generation

### Standard arguments that also apply:

- `--db`: Database name (required)
- `--table`: Table name (required)
- `--schema`: Schema name (default: public)
- `--output`: Output file path
- `--format`: Output format (json or yaml)
- `--summary`: Display generation summary

## Output Format

The LookML generation produces a structured JSON/YAML output with the following format:

```yaml
model_name: "my_model"
views:
  - view_name: "users"
    sql_table_name: "public.users"
    dimensions:
      - name: "id"
        type: "number"
        sql: "${TABLE}.id"
        description: "Unique user identifier"
        primary_key: true
      - name: "name"
        type: "string"
        sql: "${TABLE}.name"
        description: "User full name"
    measures:
      - name: "count"
        type: "count"
        sql: "*"
        description: "Total number of users"
    suggestions:
      indexes: ["CREATE INDEX idx_users_email ON users(email)"]
      relationships: ["users.id -> orders.user_id"]
      drill_fields: ["id", "name", "email"]

explores:
  - name: "user_analysis"
    view_name: "users"
    label: "User Analysis"
    description: "Explore user data and behavior"
    joins:
      - name: "orders"
        type: "left_join"
        relationship: "one_to_many"
        sql_on: "${users.id} = ${orders.user_id}"

processing_stats:
  total_time_seconds: 15.2
  total_tokens: 2500
  request_count: 3
  timestamp: "2024-01-15 10:30:00"
```

## Features

### Intelligent Dimension Generation
- Automatically detects appropriate dimension types based on data types
- Sets primary keys and foreign keys correctly
- Groups related dimensions with labels
- Suggests appropriate value formats

### Smart Measure Creation
- Generates relevant measures based on data types and business context
- Includes count, sum, average, and other appropriate aggregations
- Provides clear descriptions for each measure

### Explore Generation
- Identifies logical join relationships between tables
- Suggests appropriate join types and conditions
- Considers foreign key relationships from metadata
- Groups related explores together

### Derived Table Suggestions
- Suggests useful derived tables for common aggregations
- Recommends performance optimization opportunities
- Identifies useful data combinations

## Configuration

The LookML generation uses your existing LLM configuration from `config.yaml`:

```yaml
llm_api:
  api_key: "your-openai-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4-turbo-preview"
  max_tokens: 8192
```

## Error Handling

The system includes robust error handling:

- **Empty LLM responses**: Automatically retries with exponential backoff
- **Invalid JSON**: Attempts to clean and parse malformed responses
- **Token limits**: Automatically chunks large metadata to stay within limits
- **Database errors**: Gracefully handles connection and query issues

## Performance Considerations

- **Token usage**: Large tables may consume significant tokens. Use `token_threshold` parameter to limit metadata size
- **Processing time**: Complex models with multiple tables and explores may take several minutes
- **Rate limits**: Respects OpenAI API rate limits with automatic retry logic

## Examples

### E-commerce Model
```bash
python cli.py --db ecommerce --table users --generate-lookml \
  --model-name "customer_analytics" \
  --include-derives \
  --additional-prompt "Focus on customer lifetime value and purchase behavior"
```

### Financial Analytics
```bash
python cli.py --db finance --table transactions --generate-lookml \
  --model-name "financial_reporting" \
  --include-explores \
  --additional-prompt "Include measures for revenue, profit margins, and trend analysis"
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

2. **LLM API errors**: Check your API key and configuration in `config.yaml`

3. **Database connection issues**: Verify your database configuration and connectivity

4. **Empty results**: Check that your table has data and the schema is accessible

### Debug Mode

Enable debug logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Planned features for future releases:

- **dbt model generation**: Generate dbt semantic models
- **Cube.js support**: Generate Cube.js schema files  
- **Multi-table models**: Generate models spanning multiple related tables
- **Custom templates**: Support for custom LookML templates
- **Validation**: Validate generated LookML syntax
- **Git integration**: Automatically commit generated models to version control 