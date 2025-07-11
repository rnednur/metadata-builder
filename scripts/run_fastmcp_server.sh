#!/bin/bash

# FastMCP Server Runner - Superior to traditional MCP
# Provides FastAPI-like experience with better performance

set -e

echo "🚀 Metadata Builder - FastMCP Server"
echo "======================================"

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

# Install FastMCP if not available
echo "📦 Checking FastMCP installation..."
python3 -c "import fastmcp" 2>/dev/null || {
    echo "⬇️  Installing FastMCP 2.9.2..."
    pip3 install --user fastmcp==2.9.2
}

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
echo "🚀 Starting FastMCP Server..."
echo "   🌐 Server URL: http://localhost:$PORT"
echo "   📊 Health check: http://localhost:$PORT/health"
echo "   📚 API docs: http://localhost:$PORT/docs"
echo "   🔧 MCP tools: http://localhost:$PORT/tools"
echo ""
echo "🎯 Usage Examples:"
echo "   • Claude Desktop: Add to claude_desktop_config.json"
echo "   • Cursor: Use as MCP server in AI settings"
echo "   • API: Direct HTTP calls to endpoints"
echo ""
echo "💡 Advantages over traditional MCP:"
echo "   ✅ FastAPI-like syntax and performance"
echo "   ✅ Type safety with Pydantic models"
echo "   ✅ Auto-generated documentation"
echo "   ✅ Better error handling and debugging"
echo "   ✅ Middleware support for auth/logging"
echo "   ✅ Can serve both REST API and MCP"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the FastMCP server
python3 -m metadata_builder.mcp.fastmcp_server

echo ""
echo "✅ FastMCP Server stopped" 