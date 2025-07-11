#!/usr/bin/env python3
"""
Environment setup script for Metadata Builder.

This script helps you create a .env file with your configuration.
Run this script interactively to set up your environment variables.
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    """Main setup function."""
    print("🚀 Metadata Builder Environment Setup")
    print("=" * 50)
    
    # Check if we're in the correct directory
    project_root = Path(__file__).parent.parent
    env_example_path = project_root / "env.example"
    env_path = project_root / ".env"
    
    if not env_example_path.exists():
        print("❌ Error: env.example file not found!")
        print(f"   Expected location: {env_example_path}")
        sys.exit(1)
    
    # Check if .env already exists
    if env_path.exists():
        print(f"⚠️  .env file already exists at {env_path}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    print(f"📋 Creating .env file from template...")
    
    # Copy the template
    shutil.copy2(env_example_path, env_path)
    
    print(f"✅ Created {env_path}")
    print()
    print("🔧 Configuration Setup")
    print("-" * 30)
    
    # Ask for key configuration values
    configs = {}
    
    # LLM Provider
    print("\n1. LLM Provider Configuration")
    print("   Choose your preferred LLM provider:")
    print("   a) OpenRouter (recommended - access to multiple models)")
    print("   b) OpenAI (direct API)")
    print("   c) Anthropic (direct API)")
    print("   d) Skip for now")
    
    choice = input("   Your choice (a/b/c/d): ").strip().lower()
    
    if choice == 'a':
        print("\n   🔑 OpenRouter Setup")
        print("   Get your API key from: https://openrouter.ai/keys")
        api_key = input("   Enter your OpenRouter API key: ").strip()
        if api_key:
            configs['OPENROUTER_API_KEY'] = api_key
            
        print("\n   🤖 Model Selection")
        models = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4-turbo-preview",
            "openai/gpt-3.5-turbo",
            "google/gemini-pro",
            "mistral/mistral-large",
            "google/gemini-2.5-flash-lite-preview-06-17"
        ]
        print("   Available models:")
        for i, model in enumerate(models, 1):
            print(f"     {i}) {model}")
        
        model_choice = input("   Choose model number (1-6) or enter custom: ").strip()
        try:
            model_idx = int(model_choice) - 1
            if 0 <= model_idx < len(models):
                configs['OPENROUTER_MODEL'] = models[model_idx]
        except ValueError:
            if model_choice:
                configs['OPENROUTER_MODEL'] = model_choice
                
    elif choice == 'b':
        print("\n   🔑 OpenAI Setup")
        print("   Get your API key from: https://platform.openai.com/api-keys")
        api_key = input("   Enter your OpenAI API key: ").strip()
        if api_key:
            configs['OPENAI_API_KEY'] = api_key
            
    elif choice == 'c':
        print("\n   🔑 Anthropic Setup")
        print("   Get your API key from: https://console.anthropic.com/")
        api_key = input("   Enter your Anthropic API key: ").strip()
        if api_key:
            configs['ANTHROPIC_API_KEY'] = api_key
    
    # Database Configuration
    print("\n2. Database Configuration")
    print("   Current default: PostgreSQL on localhost:5432")
    change_db = input("   Do you want to change database settings? (y/N): ").strip().lower()
    
    if change_db == 'y':
        db_url = input("   Enter database URL (or press Enter to skip): ").strip()
        if db_url:
            configs['DATABASE_URL'] = db_url
    
    # Apply configurations
    if configs:
        print(f"\n📝 Updating {env_path}...")
        
        # Read the current file
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Update the values
        for key, value in configs.items():
            # Find the line with the key and replace it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    break
            content = '\n'.join(lines)
        
        # Write back
        with open(env_path, 'w') as f:
            f.write(content)
        
        print("✅ Configuration updated!")
    
    print()
    print("🎉 Setup Complete!")
    print("-" * 20)
    print(f"📁 Your .env file is ready at: {env_path}")
    print()
    print("📋 Next Steps:")
    print("1. Review and edit your .env file if needed")
    print("2. Start the backend: python3 -m metadata_builder.api.server")
    print("3. Start the frontend: cd frontend && npm run dev")
    print()
    print("🔒 Security Note:")
    print("   Never commit your .env file to version control!")
    print("   It contains sensitive API keys and passwords.")
    print()
    print("📚 For more information, see the documentation.")

if __name__ == "__main__":
    main() 