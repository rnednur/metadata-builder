#!/usr/bin/env python3
"""Tests for configuration management."""

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch

from config.config import load_config, get_db_config, get_llm_api_config


class TestConfig:
    """Test configuration loading and management."""
    
    def test_load_config_with_valid_file(self):
        """Test loading configuration from a valid YAML file."""
        config_data = {
            'databases': {
                'test_db': {
                    'type': 'sqlite',
                    'database': 'test.db'
                }
            },
            'llm_api': {
                'model': 'gpt-4',
                'max_tokens': 4000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            config = load_config(temp_config_path)
            assert config == config_data
            assert 'databases' in config
            assert 'test_db' in config['databases']
        finally:
            os.unlink(temp_config_path)
    
    def test_get_db_config_existing_database(self):
        """Test getting configuration for an existing database."""
        config_data = {
            'databases': {
                'test_db': {
                    'type': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            # Clear global config cache
            import config.config
            config.config._config = None
            
            db_config = get_db_config('test_db')
            assert db_config['type'] == 'postgresql'
            assert db_config['host'] == 'localhost'
        finally:
            os.unlink(temp_config_path)
    
    def test_get_db_config_nonexistent_database(self):
        """Test getting configuration for a non-existent database."""
        config_data = {'databases': {}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            # Clear global config cache
            import config.config
            config.config._config = None
            
            with pytest.raises(ValueError, match="Database 'nonexistent' not found"):
                get_db_config('nonexistent')
        finally:
            os.unlink(temp_config_path)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key', 'OPENAI_API_MODEL': 'gpt-3.5-turbo'})
    def test_get_llm_api_config_with_env_vars(self):
        """Test LLM API configuration with environment variables."""
        config_data = {
            'llm_api': {
                'model': 'gpt-4',
                'max_tokens': 2000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            # Clear global config cache
            import config.config
            config.config._config = None
            
            llm_config = get_llm_api_config()
            # Environment variables should override config file
            assert llm_config['api_key'] == 'test-key'
            assert llm_config['model'] == 'gpt-3.5-turbo'
            assert llm_config['max_tokens'] == 2000  # From config file
        finally:
            os.unlink(temp_config_path)


if __name__ == '__main__':
    pytest.main([__file__]) 