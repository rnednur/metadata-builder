#!/usr/bin/env python3
"""
BigQuery Partition Example

This example demonstrates how the metadata-builder handles BigQuery partitioned tables
with proper partition pruning and cost optimization.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to the path so we can import metadata_builder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metadata_builder.config.config import get_db_handler
from metadata_builder.core.generate_table_metadata import generate_complete_table_metadata

def demonstrate_bigquery_partitions():
    """Demonstrate BigQuery partition handling capabilities."""
    
    print("🔍 BigQuery Partition Handling Demo")
    print("=" * 50)
    
    # Example BigQuery configuration
    bigquery_config = {
        "type": "bigquery",
        "project_id": "your-project-id",
        "credentials_path": "/path/to/service-account.json"
    }
    
    print("📋 Example BigQuery Configuration:")
    print(json.dumps(bigquery_config, indent=2))
    print()
    
    # Example partitioned table scenarios
    scenarios = [
        {
            "name": "Daily Partitioned Events Table",
            "table": "events",
            "dataset": "analytics",
            "description": "Table partitioned by event_date (daily partitions)"
        },
        {
            "name": "Monthly Partitioned Sales Table", 
            "table": "sales_data",
            "dataset": "warehouse",
            "description": "Table partitioned by sale_month (monthly partitions)"
        },
        {
            "name": "Clustered User Activity Table",
            "table": "user_activity", 
            "dataset": "analytics",
            "description": "Table partitioned by date and clustered by user_id"
        }
    ]
    
    print("🎯 Supported BigQuery Partition Scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   Table: {scenario['dataset']}.{scenario['table']}")
        print(f"   Description: {scenario['description']}")
        print()
    
    print("✨ BigQuery Partition Features:")
    features = [
        "🔍 Automatic partition detection",
        "📊 Partition metadata extraction (type, column, available partitions)",
        "💰 Cost estimation with dry-run queries",
        "🎯 Partition pruning for efficient sampling",
        "📅 Support for date/time partitions (daily, monthly, yearly)",
        "🏷️  Support for integer range partitions",
        "🔗 Clustering field detection",
        "⚡ Table decorator support (table$20231201)",
        "📈 Row count estimation per partition",
        "🛡️  Query cost protection (prevents expensive full scans)"
    ]
    
    for feature in features:
        print(f"  {feature}")
    print()
    
    print("🚀 Example Usage:")
    print("""
# 1. Configure BigQuery connection
bigquery_config = {
    "my_bigquery": {
        "type": "bigquery",
        "project_id": "your-project-id", 
        "credentials_path": "/path/to/service-account.json"
    }
}

# 2. Generate metadata for partitioned table
metadata = generate_complete_table_metadata(
    db_name="my_bigquery",
    table_name="events",
    schema_name="analytics",
    sample_size=1000,  # Samples per partition
    num_samples=5      # Number of recent partitions to sample
)

# 3. Access partition information
partition_info = metadata.get('partition_info', {})
if partition_info.get('is_partitioned'):
    print(f"Partition type: {partition_info['partition_type']}")
    print(f"Partition column: {partition_info['partition_column']}")
    print(f"Available partitions: {len(partition_info['available_partitions'])}")
""")
    
    print("💡 Partition-Aware Query Examples:")
    query_examples = [
        {
            "scenario": "Recent data sampling",
            "query": """
-- Automatically samples from recent partitions only
SELECT * FROM `project.dataset.events`
WHERE DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
LIMIT 1000
""",
            "benefit": "Only scans recent partitions, dramatically reducing cost"
        },
        {
            "scenario": "Specific partition access",
            "query": """
-- Uses table decorator for specific partition
SELECT * FROM `project.dataset.events$20231201`
LIMIT 1000
""",
            "benefit": "Scans only one partition, minimal cost"
        },
        {
            "scenario": "Multi-partition sampling",
            "query": """
-- Samples from multiple specific partitions
SELECT * FROM `project.dataset.events`
WHERE DATE(event_timestamp) IN ('2023-12-01', '2023-12-02', '2023-12-03')
LIMIT 1000
""",
            "benefit": "Controlled partition scanning with cost predictability"
        }
    ]
    
    for i, example in enumerate(query_examples, 1):
        print(f"\n{i}. {example['scenario']}:")
        print(f"   Query: {example['query'].strip()}")
        print(f"   Benefit: {example['benefit']}")
    
    print("\n⚠️  Cost Protection Features:")
    protection_features = [
        "🛡️  Dry-run cost estimation before query execution",
        "💰 Configurable cost thresholds (default: 10GB limit)",
        "📊 Bytes processed reporting",
        "⏰ Query timeout protection",
        "🎯 Automatic partition pruning",
        "📈 Row count estimation without full scan"
    ]
    
    for feature in protection_features:
        print(f"  {feature}")
    
    print("\n🔧 Configuration Tips:")
    tips = [
        "Use service account JSON for authentication",
        "Set appropriate cost thresholds for your use case", 
        "Consider using table decorators for specific date ranges",
        "Enable partition pruning by including partition column in WHERE clauses",
        "Use clustering fields in ORDER BY for better performance",
        "Monitor query costs in BigQuery console",
        "Test with small sample sizes first"
    ]
    
    for tip in tips:
        print(f"  • {tip}")
    
    print(f"\n✅ Demo completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    demonstrate_bigquery_partitions() 