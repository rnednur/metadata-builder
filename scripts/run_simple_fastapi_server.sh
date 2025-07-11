#!/bin/bash

# Simple FastAPI-based MCP Server - Python 3.9 Compatible
# This works when FastMCP has compatibility issues

set -e

echo "🚀 Metadata Builder - Simple FastAPI MCP Server"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Please run from the project root directory"
    exit 1
fi

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check for environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set. Some AI features may not work."
    echo "   Set it with: export OPENAI_API_KEY=your_api_key"
fi

# Set environment variables for development
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export METADATA_BUILDER_CONFIG="configs/config.yaml"

echo "🔧 Configuration:"
echo "   📁 Project root: $(pwd)"
echo "   🐍 Python path: $PYTHONPATH"
echo "   ⚙️  Config file: $METADATA_BUILDER_CONFIG"

# Check port availability
PORT=8001
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port $PORT is in use. Attempting to free it..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo ""
echo "🚀 Starting Simple FastAPI MCP Server..."
echo "   🌐 Server URL: http://localhost:$PORT"
echo "   📊 Health check: http://localhost:$PORT/health"
echo "   📚 API docs: http://localhost:$PORT/docs"
echo "   🔧 Available tools: http://localhost:$PORT/tools"
echo ""
echo "🎯 Available MCP Tools:"
echo "   • POST /tools/get_table_metadata - Get comprehensive table metadata"
echo "   • POST /tools/search_tables - Search for tables across databases"  
echo "   • GET /tools/get_schema_overview - Get database schema overview"
echo ""
echo "💡 Usage Examples:"
echo "   • Test health: curl http://localhost:$PORT/health"
echo "   • View docs: open http://localhost:$PORT/docs"
echo "   • List tools: curl http://localhost:$PORT/tools"
echo ""
echo "🔧 This is a FastAPI-based MCP-compatible server"
echo "   ✅ Python 3.9 compatible"
echo "   ✅ Type-safe with Pydantic"  
echo "   ✅ Auto-generated documentation"
echo "   ✅ MCP response format compliant"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server
python3 -m metadata_builder.mcp.simple_fastapi_server

echo ""
echo "✅ Simple FastAPI MCP Server stopped" 