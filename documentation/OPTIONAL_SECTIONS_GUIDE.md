# Optional Sections Guide

## Overview

The metadata-builder now supports optional sections that can be enabled or disabled based on user requirements. This allows you to:

- **Save time and costs** by skipping expensive LLM operations
- **Focus on specific aspects** of metadata generation
- **Control the complexity** of generated metadata

## Available Optional Sections

### 1. **Relationships** (`include_relationships`)
- Analyzes potential relationships between tables
- Identifies foreign key patterns and table connections
- **Cost**: Medium (LLM analysis)

### 2. **Aggregation Rules** (`include_aggregation_rules`)
- Suggests aggregation patterns for analytics
- Provides SQL patterns for common aggregations
- **Cost**: Medium (LLM analysis)

### 3. **Query Rules** (`include_query_rules`)
- Optimization recommendations for queries
- Performance tuning suggestions
- **Cost**: Medium (LLM analysis)

### 4. **Data Quality** (`include_data_quality`)
- Completeness, uniqueness metrics
- Data quality recommendations
- **Cost**: Low (computational analysis)

### 5. **Query Examples** (`include_query_examples`)
- Sample SQL queries for common use cases
- Ready-to-use query templates
- **Cost**: High (LLM analysis)

### 6. **Additional Insights** (`include_additional_insights`)
- Domain-specific observations
- Advanced pattern analysis
- **Cost**: High (LLM analysis)

### 7. **Business Rules** (`include_business_rules`)
- Validation rules and constraints
- Business logic recommendations
- **Cost**: Medium (LLM analysis)

### 8. **Categorical Definitions** (`include_categorical_definitions`)
- Smart definitions for categorical values
- Filtered meaningful value explanations
- **Cost**: Medium (LLM analysis)

## Usage Examples

### Python API Usage

#### 1. **Full Metadata (Default)**
```python
from metadata_builder.core import generate_complete_table_metadata

# All sections included by default
metadata = generate_complete_table_metadata(
    db_name="ecommerce",
    table_name="orders",
    schema_name="public"
)
```

#### 2. **Minimal Metadata (Fast & Cheap)**
```python
# Only basic table structure and column definitions
metadata = generate_complete_table_metadata(
    db_name="ecommerce",
    table_name="orders",
    schema_name="public",
    include_relationships=False,
    include_aggregation_rules=False,
    include_query_rules=False,
    include_data_quality=False,
    include_query_examples=False,
    include_additional_insights=False,
    include_business_rules=False,
    include_categorical_definitions=False
)
```

#### 3. **Data Quality Focus**
```python
# Focus on data quality and basic insights
metadata = generate_complete_table_metadata(
    db_name="ecommerce",
    table_name="orders",
    schema_name="public",
    include_relationships=False,
    include_aggregation_rules=False,
    include_query_rules=False,
    include_data_quality=True,
    include_query_examples=False,
    include_additional_insights=False,
    include_business_rules=True,
    include_categorical_definitions=True
)
```

#### 4. **Analytics Focus**
```python
# Focus on analytics and query optimization
metadata = generate_complete_table_metadata(
    db_name="ecommerce",
    table_name="orders",
    schema_name="public",
    include_relationships=True,
    include_aggregation_rules=True,
    include_query_rules=True,
    include_data_quality=True,
    include_query_examples=True,
    include_additional_insights=False,
    include_business_rules=False,
    include_categorical_definitions=False
)
```

### Command Line Usage

#### 1. **Full Metadata**
```bash
python3 -m metadata_builder.core.generate_table_metadata \
    --db ecommerce \
    --table orders \
    --schema public \
    --output orders_full.json
```

#### 2. **Minimal Metadata**
```bash
python3 -m metadata_builder.core.generate_table_metadata \
    --db ecommerce \
    --table orders \
    --schema public \
    --minimal \
    --output orders_minimal.json
```

#### 3. **Fast Metadata**
```bash
python3 -m metadata_builder.core.generate_table_metadata \
    --db ecommerce \
    --table orders \
    --schema public \
    --fast \
    --output orders_fast.json
```

#### 4. **Custom Selection**
```bash
python3 -m metadata_builder.core.generate_table_metadata \
    --db ecommerce \
    --table orders \
    --schema public \
    --no-relationships \
    --no-query-examples \
    --no-additional-insights \
    --output orders_custom.json
```

## Command Line Flags

### Individual Section Control
- `--no-relationships`: Skip relationship analysis
- `--no-aggregation-rules`: Skip aggregation rules
- `--no-query-rules`: Skip query optimization rules
- `--no-data-quality`: Skip data quality metrics
- `--no-query-examples`: Skip example queries
- `--no-additional-insights`: Skip additional insights
- `--no-business-rules`: Skip business rules
- `--no-categorical-definitions`: Skip categorical value definitions

### Quick Presets
- `--minimal`: Only basic table structure (fastest, cheapest)
- `--fast`: Basic metadata with data quality (moderate speed/cost)

## Cost and Performance Impact

### Processing Time Estimates
| Configuration | Estimated Time | LLM Calls | Use Case |
|---------------|----------------|-----------|----------|
| **Minimal** | 10-30 seconds | 1-2 | Quick schema documentation |
| **Fast** | 30-60 seconds | 2-3 | Basic analysis with data quality |
| **Standard** | 2-5 minutes | 4-6 | Complete business metadata |
| **Full** | 3-8 minutes | 6-8 | Comprehensive analysis |

### Token Usage Estimates
- **Minimal**: ~2,000-5,000 tokens
- **Fast**: ~5,000-10,000 tokens  
- **Standard**: ~10,000-20,000 tokens
- **Full**: ~15,000-30,000 tokens

## Output Structure

The generated metadata will only include the sections you've enabled:

```json
{
  "database_name": "ecommerce",
  "schema_name": "public", 
  "table_name": "orders",
  "description": "Order transactions table",
  "columns": { ... },
  "constraints": { ... },
  "table_description": { ... },
  "indexes": [ ... ],
  
  // Optional sections (only if enabled)
  "relationships": [ ... ],           // if include_relationships=True
  "categorical_definitions": { ... }, // if include_categorical_definitions=True
  "data_quality": { ... },           // if include_data_quality=True
  "business_rules": [ ... ],         // if include_business_rules=True
  "additional_insights": { ... },    // if include_additional_insights=True
  "aggregation_rules": [ ... ],      // if include_aggregation_rules=True
  "query_rules": [ ... ],           // if include_query_rules=True
  "query_examples": [ ... ],        // if include_query_examples=True
  
  "processing_stats": {
    "optional_sections": {
      "relationships": true,
      "aggregation_rules": false,
      // ... status of each section
    },
    "total_duration_seconds": 45.2
  }
}
```

## Best Practices

### 1. **Development & Testing**
Use `--minimal` or `--fast` for quick iterations:
```bash
# Quick schema check
python3 -m metadata_builder.core.generate_table_metadata \
    --db mydb --table mytable --minimal
```

### 2. **Production Documentation**
Use full metadata for comprehensive documentation:
```bash
# Complete metadata for production
python3 -m metadata_builder.core.generate_table_metadata \
    --db prod_db --table core_table --output prod_metadata.json
```

### 3. **Data Quality Audits**
Focus on data quality and business rules:
```python
metadata = generate_complete_table_metadata(
    db_name="audit_db",
    table_name="customer_data",
    include_data_quality=True,
    include_business_rules=True,
    include_categorical_definitions=True,
    # Skip expensive sections
    include_query_examples=False,
    include_additional_insights=False
)
```

### 4. **Analytics Setup**
Focus on relationships and aggregations:
```python
metadata = generate_complete_table_metadata(
    db_name="analytics_db",
    table_name="fact_sales",
    include_relationships=True,
    include_aggregation_rules=True,
    include_query_rules=True,
    include_query_examples=True,
    # Skip documentation-focused sections
    include_additional_insights=False,
    include_categorical_definitions=False
)
```

## Migration from Previous Versions

The new optional parameters are **backward compatible**. Existing code will work unchanged:

```python
# This still works and includes all sections by default
metadata = generate_complete_table_metadata(
    db_name="mydb",
    table_name="mytable"
)
```

To gradually adopt the new features, start by disabling expensive sections:

```python
# Start by disabling the most expensive operations
metadata = generate_complete_table_metadata(
    db_name="mydb",
    table_name="mytable",
    include_query_examples=False,
    include_additional_insights=False
)
``` 