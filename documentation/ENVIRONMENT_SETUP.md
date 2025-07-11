# Environment Setup Guide

This guide helps you configure environment variables for the Metadata Builder, including OpenRouter integration for LLM operations.

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the interactive setup script:

```bash
python3 scripts/setup_env.py
```

This script will:
- Create a `.env` file from the template
- Guide you through LLM provider configuration
- Set up database connections
- Configure other essential settings

### Option 2: Manual Setup

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   nano .env  # or your preferred editor
   ```

## LLM Provider Configuration

### OpenRouter (Recommended)

OpenRouter provides access to multiple AI models through a single API:

```bash
# Get your API key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

**Popular Model Options:**
- `anthropic/claude-3.5-sonnet` - Best for analysis and reasoning
- `anthropic/claude-3-opus` - Most capable but slower
- `openai/gpt-4-turbo-preview` - Latest GPT-4 model
- `openai/gpt-3.5-turbo` - Fast and cost-effective
- `google/gemini-pro` - Google's latest model
- `mistral/mistral-large` - European alternative

### Alternative Providers

**OpenAI Direct:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo-preview
```

**Anthropic Direct:**
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## Database Configuration

### PostgreSQL (Default)
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DEFAULT_DATABASE=postgres
```

### Other Databases
The system supports multiple database types. Update the connection strings accordingly:

- **MySQL**: `mysql+pymysql://user:pass@localhost:3306/db`
- **SQLite**: `sqlite:///path/to/database.db`
- **Oracle**: `oracle+cx_oracle://user:pass@localhost:1521/?service_name=service`
- **BigQuery**: Requires service account credentials

## API Configuration

```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Frontend integration
REACT_APP_API_URL=http://localhost:8000

# CORS settings for production
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Security Settings

```bash
# Generate secure keys for production
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-here

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

## Optional Features

### Background Jobs (Redis)
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ENABLE_BACKGROUND_JOBS=true
```

### Monitoring
```bash
# Application monitoring
SENTRY_DSN=your_sentry_dsn_here
ENABLE_METRICS=true

# Usage analytics
ENABLE_ANALYTICS=true
ANALYTICS_ENDPOINT=https://analytics.example.com
```

### MCP Server
```bash
MCP_SERVER_PORT=8001
MCP_SERVER_HOST=0.0.0.0
MCP_ENABLE_FASTMCP=false  # Set to true if you have Python 3.10+
```

## Verification

After setting up your environment, verify the configuration:

### 1. Check API Health
```bash
curl http://localhost:8000/health
```

### 2. Test LLM Configuration
```bash
# Start the API server
python3 -m metadata_builder.api.server

# Test metadata generation
curl -X POST http://localhost:8000/api/v1/metadata/generate \
  -H "Content-Type: application/json" \
  -d '{"db_name": "your_db", "table_name": "your_table", "schema_name": "public"}'
```

### 3. Check Frontend Integration
```bash
# Start the frontend
cd frontend && npm run dev

# Visit http://localhost:3000
```

## Troubleshooting

### Common Issues

**LLM API Errors:**
- Verify your API key is correct
- Check if you have sufficient credits/quota
- Ensure the model name is valid for your provider

**Database Connection Issues:**
- Verify connection string format
- Check database server is running
- Confirm credentials and permissions

**Import Errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility (3.9+ required)

### Debug Mode

Enable debug logging:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Security Best Practices

1. **Never commit `.env` files** - They're already in `.gitignore`
2. **Use strong secret keys** - Generate random keys for production
3. **Restrict CORS origins** - Don't use `*` in production
4. **Rotate API keys regularly** - Especially for production environments
5. **Use environment-specific configs** - Separate dev/staging/prod settings

## Getting API Keys

### OpenRouter
1. Visit [OpenRouter](https://openrouter.ai/keys)
2. Sign up for an account
3. Generate an API key
4. Add credits to your account

### OpenAI
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account
3. Generate an API key
4. Set up billing

### Anthropic
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account
3. Generate an API key
4. Add credits

## Support

For additional help:
- Check the main [README.md](README.md)
- Review the [documentation](documentation/)
- Open an issue on GitHub

---

**Remember**: Keep your API keys secure and never share them publicly! 