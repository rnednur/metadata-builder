#!/bin/bash

# Demo Frontend Script for Metadata Builder
# This script starts the frontend with mock data enabled for demonstration

set -e

echo "🚀 Starting Metadata Builder Frontend Demo..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "metadata_builder" ]; then
    echo "❌ Error: Please run this script from the metadata-builder root directory"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "📁 Frontend directory not found. Setting up frontend first..."
    ./scripts/setup_frontend.sh
fi

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Create .env.local with mock data enabled
echo "⚙️  Configuring demo environment..."
cat > .env.local << EOF
# Frontend Environment Configuration - DEMO MODE
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=demo

# Enable mock data for demo
REACT_APP_USE_MOCK_DATA=true

# Feature Flags
REACT_APP_ENABLE_REAL_TIME=true
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_EXPORT=true
EOF

echo "✅ Demo environment configured with mock data enabled"
echo ""
echo "🎯 Starting frontend in demo mode..."
echo "   • Mock data: ENABLED"
echo "   • Backend API: Not required"
echo "   • URL: http://localhost:3000"
echo ""
echo "📱 Demo Features Available:"
echo "   ✅ Dashboard with sample metrics"
echo "   ✅ Metadata management (3 sample tables)"
echo "   ✅ Search and filtering"
echo "   ✅ Data quality visualization"
echo "   ✅ Export functionality"
echo "   ✅ Real-time activity simulation"
echo ""
echo "🔄 Coming Soon:"
echo "   🚧 Database connections"
echo "   🚧 Schema explorer"
echo "   🚧 Metadata generation"
echo "   🚧 LookML models"
echo ""

# Start the development server
npm run dev 