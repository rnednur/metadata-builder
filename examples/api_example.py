#!/usr/bin/env python3
"""
Example script demonstrating the Metadata Builder API usage.

This script shows how to:
1. Create database connections
2. Test connections
3. List schemas and tables
4. Generate metadata
5. Generate LookML models

Run the API server first:
    python -m metadata_builder.api.server

Then run this script:
    python examples/api_example.py
"""

import requests
import time
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health"


def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API is healthy: {health_data['status']}")
            print(f"   Database connections: {health_data['database_connections']}")
            print(f"   LLM API status: {health_data['llm_api_status']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("   Make sure to start the API server first:")
        print("   python -m metadata_builder.api.server")
        return False


def create_sample_connection() -> bool:
    """Create a sample SQLite database connection."""
    connection_data = {
        "name": "sample_sqlite",
        "type": "sqlite",
        "database": ":memory:"  # In-memory SQLite database
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/database/connections", json=connection_data)
        if response.status_code == 200:
            print("✅ Sample connection created successfully")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print("ℹ️  Sample connection already exists")
            return True
        else:
            print(f"❌ Failed to create connection: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating connection: {e}")
        return False


def list_connections() -> None:
    """List all database connections."""
    try:
        response = requests.get(f"{API_BASE_URL}/database/connections")
        if response.status_code == 200:
            connections = response.json()
            print(f"📋 Found {len(connections)} database connections:")
            for conn in connections:
                print(f"   - {conn['name']} ({conn['type']})")
        else:
            print(f"❌ Failed to list connections: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error listing connections: {e}")


def test_connection(connection_name: str) -> bool:
    """Test a database connection."""
    try:
        response = requests.post(f"{API_BASE_URL}/database/connections/{connection_name}/test")
        if response.status_code == 200:
            test_result = response.json()
            if test_result['status'] == 'success':
                print(f"✅ Connection '{connection_name}' test successful")
                print(f"   Response time: {test_result['response_time_ms']:.2f}ms")
                return True
            else:
                print(f"❌ Connection '{connection_name}' test failed: {test_result['message']}")
                return False
        else:
            print(f"❌ Failed to test connection: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing connection: {e}")
        return False


def get_schemas(connection_name: str) -> None:
    """Get schemas for a database connection."""
    try:
        response = requests.get(f"{API_BASE_URL}/database/connections/{connection_name}/schemas")
        if response.status_code == 200:
            schema_data = response.json()
            print(f"📊 Database '{connection_name}' has {len(schema_data['schemas'])} schemas:")
            for schema in schema_data['schemas']:
                print(f"   - {schema['schema_name']}: {schema['table_count']} tables")
                if schema['tables']:
                    print(f"     Tables: {', '.join(schema['tables'][:3])}{'...' if len(schema['tables']) > 3 else ''}")
        else:
            print(f"❌ Failed to get schemas: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting schemas: {e}")


def generate_metadata_example() -> None:
    """Example of generating metadata (this will fail with SQLite in-memory DB, but shows the API)."""
    metadata_request = {
        "db_name": "sample_sqlite",
        "table_name": "users",  # This table doesn't exist, but shows the API structure
        "schema_name": "main",
        "sample_size": 50,
        "num_samples": 3,
        "include_relationships": True,
        "include_data_quality": True
    }
    
    print("📝 Example metadata generation request:")
    print(json.dumps(metadata_request, indent=2))
    
    try:
        response = requests.post(f"{API_BASE_URL}/metadata/generate", json=metadata_request)
        if response.status_code == 200:
            metadata = response.json()
            print("✅ Metadata generated successfully!")
            print(f"   Processing time: {metadata['processing_stats']['total_duration_seconds']:.2f}s")
        else:
            print(f"ℹ️  Metadata generation failed (expected with empty database): {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating metadata: {e}")


def generate_metadata_async_example() -> None:
    """Example of asynchronous metadata generation."""
    metadata_request = {
        "db_name": "sample_sqlite",
        "table_name": "orders",
        "schema_name": "main"
    }
    
    try:
        # Start async job
        response = requests.post(f"{API_BASE_URL}/metadata/generate/async", json=metadata_request)
        if response.status_code == 200:
            job = response.json()
            job_id = job['job_id']
            print(f"🔄 Started async metadata generation job: {job_id}")
            
            # Poll for completion (in real usage, you'd do this with proper intervals)
            for i in range(5):  # Check 5 times
                time.sleep(1)
                status_response = requests.get(f"{API_BASE_URL}/metadata/jobs/{job_id}")
                if status_response.status_code == 200:
                    job_status = status_response.json()
                    print(f"   Job status: {job_status['status']}")
                    
                    if job_status['status'] == 'completed':
                        print("✅ Async metadata generation completed!")
                        break
                    elif job_status['status'] == 'failed':
                        print(f"❌ Async metadata generation failed: {job_status.get('error')}")
                        break
                else:
                    print(f"❌ Failed to get job status: {status_response.status_code}")
                    break
        else:
            print(f"❌ Failed to start async metadata generation: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error with async metadata generation: {e}")


def generate_lookml_example() -> None:
    """Example of LookML generation."""
    lookml_request = {
        "db_name": "sample_sqlite",
        "schema_name": "main",
        "table_names": ["users", "orders"],
        "model_name": "sample_analytics_model",
        "include_explores": True,
        "include_derived_tables": False
    }
    
    print("🔧 Example LookML generation request:")
    print(json.dumps(lookml_request, indent=2))
    
    try:
        response = requests.post(f"{API_BASE_URL}/metadata/lookml/generate", json=lookml_request)
        if response.status_code == 200:
            lookml = response.json()
            print("✅ LookML generated successfully!")
            print(f"   Model name: {lookml['model_name']}")
            print(f"   Processing time: {lookml['processing_stats']['total_duration_seconds']:.2f}s")
        else:
            print(f"ℹ️  LookML generation failed (expected with empty database): {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error generating LookML: {e}")


def main():
    """Main function demonstrating the API usage."""
    print("🚀 Metadata Builder API Example")
    print("=" * 50)
    
    # Check API health
    if not check_api_health():
        return
    
    print("\n1. Creating sample database connection...")
    if not create_sample_connection():
        return
    
    print("\n2. Listing all connections...")
    list_connections()
    
    print("\n3. Testing connection...")
    if not test_connection("sample_sqlite"):
        print("   Note: Connection test may fail with in-memory SQLite")
    
    print("\n4. Getting database schemas...")
    get_schemas("sample_sqlite")
    
    print("\n5. Example metadata generation (synchronous)...")
    generate_metadata_example()
    
    print("\n6. Example metadata generation (asynchronous)...")
    generate_metadata_async_example()
    
    print("\n7. Example LookML generation...")
    generate_lookml_example()
    
    print("\n✨ API example completed!")
    print("\nNext steps:")
    print("- Configure real database connections in .config.yaml")
    print("- Set OPENAI_API_KEY for LLM-enhanced metadata generation")
    print("- Explore the interactive API docs at http://localhost:8000/docs")


if __name__ == "__main__":
    main() 