#!/usr/bin/env python3
"""
Test script for LookML generation functionality.
"""

import logging
import json
from semantic_models import generate_lookml_model

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_lookml_generation():
    """Test LookML generation with sample metadata."""
    
    # Sample metadata for testing
    sample_metadata = {
        "users": {
            "schema": {
                "id": "INTEGER",
                "name": "VARCHAR(255)",
                "email": "VARCHAR(255)",
                "created_at": "TIMESTAMP",
                "is_active": "BOOLEAN"
            },
            "constraints": {
                "primary_keys": ["id"],
                "foreign_keys": [],
                "unique_constraints": ["email"]
            }
        }
    }
    
    try:
        result = generate_lookml_model(
            db_name="test_db",
            schema_name="public",
            table_names=["users"],
            model_name="test_model",
            include_derived_tables=True,
            include_explores=True,
            metadata=sample_metadata
        )
        
        print("LookML Generation Test Results:")
        print("=" * 50)
        print(f"Model Name: {result.get('model_name')}")
        print(f"Views Generated: {len(result.get('views', []))}")
        print(f"Explores Generated: {len(result.get('explores', []))}")
        
        stats = result.get('processing_stats', {})
        print(f"Processing Time: {stats.get('total_time_seconds', 0):.2f} seconds")
        print(f"Total Tokens: {stats.get('total_tokens', 0)}")
        
        # Save result to file for inspection
        with open('test_lookml_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        print("\nTest completed successfully!")
        print("Results saved to test_lookml_result.json")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lookml_generation() 