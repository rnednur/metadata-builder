#!/usr/bin/env python3
"""
Comprehensive demonstration of the predefined schema and table filtering system.
Shows how to configure and use schema/table filters for database connections.
"""

import json
from typing import Dict, Any, List

def demonstrate_schema_table_filtering():
    """Demonstrate the new schema and table filtering capabilities."""
    
    print("=" * 80)
    print("PREDEFINED SCHEMA AND TABLE FILTERING SYSTEM")
    print("=" * 80)
    
    print("\n🎯 OVERVIEW")
    print("-" * 50)
    print("This system allows you to:")
    print("  • Define specific schemas to include in metadata generation")
    print("  • Filter tables within each schema using multiple criteria")
    print("  • Use regex patterns for flexible table matching")
    print("  • Exclude specific tables or patterns")
    print("  • Enable/disable entire schemas")
    print("  • Focus on relevant tables in large databases")
    
    print("\n📊 FILTERING CONFIGURATION STRUCTURE")
    print("-" * 50)
    
    schema_config_example = {
        "schema_name": {
            "enabled": True,
            "tables": ["specific_table1", "specific_table2"],
            "excluded_tables": ["temp_table", "backup_table"],
            "table_patterns": ["user_.*", "order_.*", "product_.*"],
            "excluded_patterns": [".*_temp", ".*_backup", ".*_old"],
            "description": "Main application tables for user data"
        }
    }
    
    print("Configuration structure for each schema:")
    print(json.dumps(schema_config_example, indent=2))
    
    print("\n🏗️ REAL-WORLD EXAMPLES")
    print("-" * 50)
    
    # Example 1: E-commerce Database
    print("\n📈 Example 1: E-commerce Database")
    ecommerce_config = {
        "public": {
            "enabled": True,
            "tables": [],  # Include all tables, but use patterns and exclusions
            "excluded_tables": ["migration_log", "temp_data"],
            "table_patterns": ["user.*", "product.*", "order.*", "payment.*"],
            "excluded_patterns": [".*_backup", ".*_temp", "test_.*"],
            "description": "Core e-commerce tables"
        },
        "analytics": {
            "enabled": True,
            "tables": ["daily_sales", "user_metrics", "product_performance"],
            "excluded_tables": [],
            "table_patterns": [],
            "excluded_patterns": [".*_raw", ".*_staging"],
            "description": "Analytics and reporting tables"
        },
        "logs": {
            "enabled": False,  # Disable entire schema
            "tables": [],
            "excluded_tables": [],
            "table_patterns": [],
            "excluded_patterns": [],
            "description": "Log tables (disabled for metadata generation)"
        }
    }
    
    print("E-commerce filtering configuration:")
    print(json.dumps(ecommerce_config, indent=2))
    
    # Example 2: BigQuery Analytics
    print("\n📊 Example 2: BigQuery Analytics Dataset")
    bigquery_config = {
        "marketing_data": {
            "enabled": True,
            "tables": [],
            "excluded_tables": ["temp_campaigns", "test_data"],
            "table_patterns": ["campaign_.*", "audience_.*", "conversion_.*"],
            "excluded_patterns": [".*_test", ".*_backup"],
            "description": "Marketing campaign and audience data"
        },
        "sales_data": {
            "enabled": True,
            "tables": ["sales_fact", "sales_dim_product", "sales_dim_customer"],
            "excluded_tables": [],
            "table_patterns": [],
            "excluded_patterns": [],
            "description": "Core sales data warehouse tables"
        }
    }
    
    print("BigQuery filtering configuration:")
    print(json.dumps(bigquery_config, indent=2))
    
    print("\n🔧 API USAGE EXAMPLES")
    print("-" * 50)
    
    api_examples = [
        {
            "endpoint": "GET /database/connections/{connection_name}/predefined-schemas",
            "description": "Get current predefined schemas configuration",
            "example_response": {
                "connection_name": "production_db",
                "predefined_schemas": ecommerce_config,
                "available_schemas": ["public", "analytics", "logs", "admin"]
            }
        },
        {
            "endpoint": "PUT /database/connections/{connection_name}/predefined-schemas",
            "description": "Update entire predefined schemas configuration",
            "example_request": {
                "predefined_schemas": ecommerce_config
            }
        },
        {
            "endpoint": "POST /database/connections/{connection_name}/predefined-schemas/{schema_name}",
            "description": "Add or update a specific schema configuration",
            "example_request": {
                "enabled": True,
                "tables": ["users", "orders"],
                "excluded_tables": ["temp_users"],
                "table_patterns": ["user_.*"],
                "excluded_patterns": [".*_backup"],
                "description": "User-related tables"
            }
        },
        {
            "endpoint": "DELETE /database/connections/{connection_name}/predefined-schemas/{schema_name}",
            "description": "Remove a schema from predefined configuration",
            "example_response": {
                "message": "Schema 'logs' removed from predefined schemas"
            }
        }
    ]
    
    for i, example in enumerate(api_examples, 1):
        print(f"\n{i}. {example['endpoint']}")
        print(f"   Description: {example['description']}")
        if 'example_request' in example:
            print(f"   Request: {json.dumps(example['example_request'], indent=6)}")
        if 'example_response' in example:
            print(f"   Response: {json.dumps(example['example_response'], indent=6)}")
    
    print("\n🔄 TABLE FILTERING LOGIC")
    print("-" * 50)
    
    filtering_steps = [
        "1. Check if schema is enabled (if disabled, return empty list)",
        "2. Start with all tables in the schema",
        "3. If 'tables' list is specified, filter to only those tables",
        "4. Apply 'table_patterns' (regex) for inclusion",
        "5. Remove tables listed in 'excluded_tables'", 
        "6. Apply 'excluded_patterns' (regex) for exclusion",
        "7. Return final filtered list"
    ]
    
    for step in filtering_steps:
        print(f"  {step}")
    
    print("\n📋 FILTERING EXAMPLE")
    print("-" * 50)
    
    # Demonstrate filtering logic
    all_tables = [
        "users", "user_profiles", "user_sessions", "user_temp",
        "orders", "order_items", "order_history", "order_backup",
        "products", "product_categories", "product_reviews",
        "temp_data", "migration_log", "test_table", "backup_users"
    ]
    
    filter_config = {
        "enabled": True,
        "tables": [],  # No specific tables, use patterns
        "excluded_tables": ["temp_data", "migration_log"],
        "table_patterns": ["user.*", "order.*", "product.*"],
        "excluded_patterns": [".*_temp", ".*_backup", "test_.*"]
    }
    
    print(f"All tables in schema: {all_tables}")
    print(f"Filter configuration: {json.dumps(filter_config, indent=2)}")
    
    # Simulate filtering
    import re
    
    filtered_tables = all_tables.copy()
    
    # Apply inclusion patterns
    if filter_config.get("table_patterns"):
        pattern_matched = []
        for table in filtered_tables:
            for pattern in filter_config["table_patterns"]:
                if re.match(pattern, table):
                    pattern_matched.append(table)
                    break
        filtered_tables = pattern_matched
        print(f"After inclusion patterns: {filtered_tables}")
    
    # Remove excluded tables
    if filter_config.get("excluded_tables"):
        filtered_tables = [t for t in filtered_tables if t not in filter_config["excluded_tables"]]
        print(f"After excluded tables: {filtered_tables}")
    
    # Apply exclusion patterns
    if filter_config.get("excluded_patterns"):
        for pattern in filter_config["excluded_patterns"]:
            filtered_tables = [t for t in filtered_tables if not re.match(pattern, t)]
        print(f"After exclusion patterns: {filtered_tables}")
    
    print(f"\\n✅ Final filtered tables: {filtered_tables}")

def show_benefits_and_use_cases():
    """Show the benefits and use cases for the filtering system."""
    
    print("\\n" + "=" * 80)
    print("BENEFITS AND USE CASES")
    print("=" * 80)
    
    benefits = [
        {
            "benefit": "🎯 Focus on Relevant Data",
            "description": "Only generate metadata for tables you actually use",
            "example": "In a 500-table database, focus on 20 core business tables"
        },
        {
            "benefit": "⚡ Faster Processing",
            "description": "Reduce metadata generation time by excluding unnecessary tables",
            "example": "Skip temp, backup, and test tables"
        },
        {
            "benefit": "💰 Cost Optimization",
            "description": "Reduce LLM API costs by processing fewer tables",
            "example": "Filter 100 tables down to 25 relevant ones"
        },
        {
            "benefit": "🔧 Pattern-Based Flexibility",
            "description": "Use regex patterns for dynamic table selection",
            "example": "Include all tables matching 'user_.*' pattern"
        },
        {
            "benefit": "📊 Schema Organization",
            "description": "Organize tables by purpose with different filter rules",
            "example": "Core tables vs analytics tables vs temp tables"
        },
        {
            "benefit": "🔒 Security and Compliance",
            "description": "Exclude sensitive or compliance-restricted tables",
            "example": "Exclude PII tables or audit logs from metadata generation"
        }
    ]
    
    for benefit in benefits:
        print(f"\\n{benefit['benefit']}")
        print(f"  {benefit['description']}")
        print(f"  Example: {benefit['example']}")
    
    print("\\n📋 COMMON USE CASES")
    print("-" * 50)
    
    use_cases = [
        {
            "scenario": "Large E-commerce Platform",
            "challenge": "Database has 200+ tables including temp, backup, and test tables",
            "solution": "Filter to only production tables using patterns and exclusions",
            "result": "Focus on 40 core business tables for metadata generation"
        },
        {
            "scenario": "Multi-tenant SaaS Application",
            "challenge": "Database has tables for different tenants and environments",
            "solution": "Use schema-level filtering to focus on specific tenant data",
            "result": "Generate metadata only for relevant tenant schemas"
        },
        {
            "scenario": "Data Warehouse with BigQuery",
            "challenge": "Multiple datasets with staging, raw, and processed tables",
            "solution": "Include only processed/mart tables, exclude staging/raw",
            "result": "Clean metadata for business-ready tables only"
        },
        {
            "scenario": "Legacy Database Migration",
            "challenge": "Old tables mixed with new ones, unclear naming conventions",
            "solution": "Use date-based patterns to include only recent tables",
            "result": "Focus metadata generation on current data structures"
        },
        {
            "scenario": "Development vs Production",
            "challenge": "Development database has test tables and experimental schemas",
            "solution": "Exclude test/temp tables and development schemas",
            "result": "Generate metadata only for production-ready structures"
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        print(f"\\n{i}. {use_case['scenario']}")
        print(f"   Challenge: {use_case['challenge']}")
        print(f"   Solution: {use_case['solution']}")
        print(f"   Result: {use_case['result']}")

if __name__ == "__main__":
    demonstrate_schema_table_filtering()
    show_benefits_and_use_cases()
    
    print("\\n" + "=" * 80)
    print("READY TO USE!")
    print("=" * 80)
    print("The predefined schema and table filtering system is now available.")
    print("\\nKey Features:")
    print("  ✅ Persist predefined schemas in database connections")
    print("  ✅ Filter tables within schemas using multiple criteria")
    print("  ✅ Support regex patterns for flexible matching")
    print("  ✅ API endpoints for managing filter configurations")
    print("  ✅ Backward compatibility with legacy comma-separated schemas")
    print("  ✅ Enable/disable entire schemas")
    print("\\nNext Steps:")
    print("  1. Configure predefined schemas for your connections")
    print("  2. Define table filtering rules for each schema") 
    print("  3. Use the API endpoints to manage configurations")
    print("  4. Generate metadata only for relevant tables")
    print("\\nThe system automatically respects your filtering configuration")
    print("during schema discovery and metadata generation!")