#!/usr/bin/env python3
"""
Test script to demonstrate optional sections functionality
"""

import json
import time
from metadata_builder.core import generate_complete_table_metadata

def test_optional_sections():
    """Test different configurations of optional sections"""
    
    print("🔬 Testing Optional Sections Functionality")
    print("=" * 50)
    
    # Sample data for testing (mock function)
    test_cases = [
        {
            "name": "Full Metadata (All Sections)",
            "config": {},  # All defaults to True
            "description": "Complete metadata with all sections enabled"
        },
        {
            "name": "Minimal Metadata", 
            "config": {
                "include_relationships": False,
                "include_aggregation_rules": False,
                "include_query_rules": False,
                "include_data_quality": False,
                "include_query_examples": False,
                "include_additional_insights": False,
                "include_business_rules": False,
                "include_categorical_definitions": False
            },
            "description": "Only basic table structure and column definitions"
        },
        {
            "name": "Data Quality Focus",
            "config": {
                "include_relationships": False,
                "include_aggregation_rules": False,
                "include_query_rules": False,
                "include_data_quality": True,
                "include_query_examples": False,
                "include_additional_insights": False,
                "include_business_rules": True,
                "include_categorical_definitions": True
            },
            "description": "Focus on data quality and business rules"
        },
        {
            "name": "Analytics Focus",
            "config": {
                "include_relationships": True,
                "include_aggregation_rules": True,
                "include_query_rules": True,
                "include_data_quality": True,
                "include_query_examples": True,
                "include_additional_insights": False,
                "include_business_rules": False,
                "include_categorical_definitions": False
            },
            "description": "Focus on analytics and query optimization"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test {i}: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Configuration: {test_case['config']}")
        
        # Show what sections would be enabled/disabled
        config = test_case['config']
        enabled_sections = []
        disabled_sections = []
        
        sections = [
            'relationships', 'aggregation_rules', 'query_rules', 
            'data_quality', 'query_examples', 'additional_insights',
            'business_rules', 'categorical_definitions'
        ]
        
        for section in sections:
            key = f'include_{section}'
            if config.get(key, True):  # Default is True
                enabled_sections.append(section)
            else:
                disabled_sections.append(section)
        
        print(f"✅ Enabled: {', '.join(enabled_sections) if enabled_sections else 'None'}")
        print(f"❌ Disabled: {', '.join(disabled_sections) if disabled_sections else 'None'}")
        
        # Simulate processing time and cost
        estimated_time = len(enabled_sections) * 15  # ~15 seconds per section
        estimated_tokens = len(enabled_sections) * 2500  # ~2500 tokens per section
        
        print(f"⏱️  Estimated time: {estimated_time} seconds")
        print(f"🎯 Estimated tokens: {estimated_tokens}")
        
        print("-" * 30)

def demonstrate_api_usage():
    """Show various API usage patterns"""
    
    print("\n🚀 API Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "1. Quick Development Check",
            "code": """
# Fast check for development
metadata = generate_complete_table_metadata(
    db_name="dev_db",
    table_name="users",
    include_relationships=False,
    include_query_examples=False,
    include_additional_insights=False
)
            """,
            "use_case": "Quick schema validation during development"
        },
        {
            "title": "2. Production Documentation",
            "code": """
# Complete metadata for production docs
metadata = generate_complete_table_metadata(
    db_name="prod_db",
    table_name="customers"
    # All sections enabled by default
)
            """,
            "use_case": "Comprehensive documentation for production systems"
        },
        {
            "title": "3. Data Quality Audit",
            "code": """
# Focus on data quality
metadata = generate_complete_table_metadata(
    db_name="audit_db",
    table_name="transactions",
    include_data_quality=True,
    include_business_rules=True,
    include_categorical_definitions=True,
    # Skip expensive analytics sections
    include_query_examples=False,
    include_additional_insights=False,
    include_aggregation_rules=False
)
            """,
            "use_case": "Data quality assessment and validation"
        }
    ]
    
    for example in examples:
        print(f"\n{example['title']}")
        print(f"Use Case: {example['use_case']}")
        print("```python")
        print(example['code'].strip())
        print("```")

def show_cli_examples():
    """Show command line usage examples"""
    
    print("\n💻 Command Line Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "Minimal metadata (fastest)",
            "command": "python3 -m metadata_builder.core.generate_table_metadata --db mydb --table users --minimal"
        },
        {
            "title": "Fast metadata with data quality",
            "command": "python3 -m metadata_builder.core.generate_table_metadata --db mydb --table users --fast"
        },
        {
            "title": "Custom selection",
            "command": "python3 -m metadata_builder.core.generate_table_metadata --db mydb --table users --no-query-examples --no-additional-insights"
        },
        {
            "title": "Full metadata with output file",
            "command": "python3 -m metadata_builder.core.generate_table_metadata --db mydb --table users --output users_metadata.json"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"```bash")
        print(f"{example['command']}")
        print(f"```")

if __name__ == "__main__":
    test_optional_sections()
    demonstrate_api_usage()
    show_cli_examples()
    
    print(f"\n🎉 Optional Sections Feature Summary")
    print("=" * 50)
    print("✅ 8 optional sections can be controlled independently")
    print("✅ Command line flags for individual section control")
    print("✅ Quick presets (--minimal, --fast) for common use cases")
    print("✅ Backward compatibility with existing code")
    print("✅ Processing stats show which sections were enabled/disabled")
    print("✅ Significant cost and time savings possible")
    
    print(f"\n📚 See OPTIONAL_SECTIONS_GUIDE.md for detailed usage examples") 