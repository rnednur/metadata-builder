#!/bin/bash

# Metadata Builder - MCP Server Runner
# This script starts the MCP server for AI agent integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Metadata Builder - MCP Server${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if mcp package is installed (Python 3.9 compatible)
if ! python3 -c "import mcp" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  MCP package not found. Installing Python 3.9 compatible version...${NC}"
    pip3 install --user mcp-python-sdk
fi

# Check environment variables
echo -e "${BLUE}🔧 Checking configuration...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. MCP server may not work properly.${NC}"
    echo -e "${YELLOW}   Set it with: export OPENAI_API_KEY=your_api_key${NC}"
fi

# Check if config file exists
if [ ! -f "metadata_builder/config/config.yaml" ] && [ ! -f "configs/config.yaml" ]; then
    echo -e "${YELLOW}⚠️  Configuration file not found. Creating sample config...${NC}"
    mkdir -p configs
    cat > configs/config.yaml << EOF
# Sample configuration for Metadata Builder MCP Server
databases:
  sample_db:
    type: sqlite
    database: ":memory:"
    
# LLM Configuration
llm:
  api_key: \${OPENAI_API_KEY}
  base_url: "https://api.openai.com/v1"
  model: "gpt-4-turbo-preview"
EOF
    echo -e "${GREEN}✅ Created sample config at configs/config.yaml${NC}"
fi

echo -e "\n${BLUE}🚀 Starting MCP Server...${NC}"
echo -e "${GREEN}   Ready to accept AI agent connections${NC}"
echo -e "${GREEN}   Server will provide metadata intelligence tools${NC}"

echo -e "\n${BLUE}Available MCP Tools:${NC}"
echo -e "${BLUE}• get_table_metadata - Get comprehensive table metadata${NC}"
echo -e "${BLUE}• search_tables - Search for tables across databases${NC}"
echo -e "${BLUE}• analyze_data_quality - Analyze data quality metrics${NC}"
echo -e "${BLUE}• get_schema_overview - Get database schema overview${NC}"
echo -e "${BLUE}• generate_semantic_model - Generate LookML/dbt models${NC}"
echo -e "${BLUE}• explain_business_context - Get business context explanations${NC}"

echo -e "\n${YELLOW}💡 To use with Claude Desktop, add this to your config:${NC}"
echo -e "${YELLOW}   {${NC}"
echo -e "${YELLOW}     \"metadata-builder\": {${NC}"
echo -e "${YELLOW}       \"command\": \"python3\",${NC}"
echo -e "${YELLOW}       \"args\": [\"-m\", \"metadata_builder.mcp.server\"],${NC}"
echo -e "${YELLOW}       \"cwd\": \"$(pwd)\"${NC}"
echo -e "${YELLOW}     }${NC}"
echo -e "${YELLOW}   }${NC}"

echo -e "\n${YELLOW}Press Ctrl+C to stop the server${NC}"

# Run the MCP server
python3 -m metadata_builder.mcp.server 