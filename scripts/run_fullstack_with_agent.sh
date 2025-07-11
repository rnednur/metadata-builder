#!/bin/bash

# Metadata Builder - Full Stack Runner with AI Agent
# This script starts both backend API and frontend with AI agent functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_HOST=${BACKEND_HOST:-"0.0.0.0"}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}

echo -e "${BLUE}🤖 Metadata Builder - Full Stack with AI Agent${NC}"
echo -e "${BLUE}================================================${NC}"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if required files exist
if [ ! -f "metadata_builder/api/app.py" ]; then
    echo -e "${RED}❌ Backend API files not found. Are you in the project root?${NC}"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}❌ Frontend files not found. Are you in the project root?${NC}"
    exit 1
fi

# Check ports
echo -e "${BLUE}🔍 Checking ports...${NC}"
if ! check_port $BACKEND_PORT; then
    echo -e "${RED}❌ Backend port $BACKEND_PORT is in use. Stop the service or use a different port.${NC}"
    exit 1
fi

if ! check_port $FRONTEND_PORT; then
    echo -e "${RED}❌ Frontend port $FRONTEND_PORT is in use. Stop the service or use a different port.${NC}"
    exit 1
fi

# Check environment variables
echo -e "${BLUE}🔧 Checking configuration...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY not set. AI agent features may not work properly.${NC}"
    echo -e "${YELLOW}   Set it with: export OPENAI_API_KEY=your_api_key${NC}"
fi

# Install frontend dependencies if needed
echo -e "${BLUE}📦 Setting up frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
cd ..

# Start backend
echo -e "\n${BLUE}🚀 Starting Backend API with AI Agent...${NC}"
echo -e "${GREEN}   URL: http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}   API Docs: http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${GREEN}   Agent Chat: http://localhost:$BACKEND_PORT/api/v1/agent/chat${NC}"

python3 -m metadata_builder.api.server \
    --host $BACKEND_HOST \
    --port $BACKEND_PORT \
    --reload \
    --log-level info &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}⏳ Waiting for backend to start...${NC}"
sleep 5

# Check if backend is running
if ! curl -s http://localhost:$BACKEND_PORT/health >/dev/null 2>&1; then
    echo -e "${RED}❌ Backend failed to start. Check the logs above.${NC}"
    cleanup
fi

echo -e "${GREEN}✅ Backend is running!${NC}"

# Start frontend
echo -e "\n${BLUE}🎨 Starting Frontend with AI Chat Interface...${NC}"
echo -e "${GREEN}   URL: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${GREEN}   Chat Interface: http://localhost:$FRONTEND_PORT/agent${NC}"

cd frontend
npm run start -- --port $FRONTEND_PORT &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
sleep 10

echo -e "\n${GREEN}🎉 Full Stack is running!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🔗 Frontend: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${GREEN}🔗 Backend API: http://localhost:$BACKEND_PORT${NC}"
echo -e "${GREEN}🔗 API Documentation: http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${GREEN}🤖 AI Agent Status: http://localhost:$BACKEND_PORT/api/v1/agent/status${NC}"
echo -e "\n${BLUE}Features Available:${NC}"
echo -e "${BLUE}• 🤖 AI Agent Chat Interface${NC}"
echo -e "${BLUE}• 📊 Metadata Generation${NC}"
echo -e "${BLUE}• 🔍 Natural Language Queries${NC}"
echo -e "${BLUE}• 📈 Data Quality Analysis${NC}"
echo -e "${BLUE}• 🏗️ Schema Change Detection${NC}"
echo -e "${BLUE}• 💼 Business Context Explanations${NC}"

echo -e "\n${YELLOW}💡 Try these natural language queries in the chat interface:${NC}"
echo -e "   • 'Generate metadata for the users table'"
echo -e "   • 'Show me all tables with customer data'"
echo -e "   • 'Check data quality issues in my database'"
echo -e "   • 'Export metadata for compliance reporting'"

echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep script running and wait for signals
wait 