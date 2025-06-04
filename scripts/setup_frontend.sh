#!/bin/bash

# Frontend Setup Script for Metadata Builder
# This script sets up the complete frontend development environment

set -e

echo "🚀 Setting up Metadata Builder Frontend..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "metadata_builder" ]; then
    echo "❌ Error: Please run this script from the metadata-builder root directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ and npm 9+"
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version $NODE_VERSION is too old. Please upgrade to Node.js 18+"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed"
    exit 1
fi

echo "✅ npm $(npm -v) detected"

# Create frontend directory if it doesn't exist
if [ ! -d "frontend" ]; then
    echo "📁 Creating frontend directory..."
    mkdir -p frontend
fi

cd frontend

# Create package.json if it doesn't exist
if [ ! -f "package.json" ]; then
    echo "📦 Creating package.json..."
    cat > package.json << 'EOF'
{
  "name": "metadata-builder-frontend",
  "private": true,
  "version": "1.0.0",
  "description": "Frontend interface for metadata-builder",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:e2e": "playwright test",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "analyze": "npx vite-bundle-analyzer"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "antd": "^5.12.8",
    "@ant-design/icons": "^5.2.6",
    "@tanstack/react-query": "^5.8.4",
    "axios": "^1.6.2",
    "zustand": "^4.4.7",
    "recharts": "^2.8.0",
    "@monaco-editor/react": "^4.6.0",
    "react-syntax-highlighter": "^15.5.0",
    "@uiw/react-json-view": "^2.0.0-alpha.16",
    "dayjs": "^1.11.10",
    "lodash": "^4.17.21",
    "classnames": "^2.3.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@types/lodash": "^4.14.202",
    "@types/react-syntax-highlighter": "^15.5.10",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.1.1",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "prettier": "^3.1.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0",
    "vitest": "^0.34.6",
    "@vitest/ui": "^0.34.6",
    "jsdom": "^23.0.1",
    "@testing-library/react": "^13.4.0",
    "@testing-library/jest-dom": "^6.1.4",
    "@testing-library/user-event": "^14.5.1",
    "playwright": "^1.40.0",
    "@playwright/test": "^1.40.0",
    "@storybook/react-vite": "^7.5.3",
    "@storybook/addon-essentials": "^7.5.3",
    "@storybook/addon-interactions": "^7.5.3",
    "@storybook/addon-links": "^7.5.3",
    "@storybook/blocks": "^7.5.3",
    "@storybook/testing-library": "^0.2.2",
    "storybook": "^7.5.3"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
EOF
fi

echo "📦 Installing frontend dependencies..."
npm install

# Create environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "⚙️  Creating frontend environment configuration..."
    cat > .env.local << EOF
# Frontend Environment Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development
EOF
    echo "📝 Created .env.local with default configuration"
fi

# Create Vite config if it doesn't exist
if [ ! -f "vite.config.ts" ]; then
    echo "⚙️  Creating Vite configuration..."
    cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd', '@ant-design/icons'],
          charts: ['recharts'],
          editor: ['@monaco-editor/react'],
        },
      },
    },
  },
})
EOF
fi

# Create TypeScript config if it doesn't exist
if [ ! -f "tsconfig.json" ]; then
    echo "⚙️  Creating TypeScript configuration..."
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
fi

# Create tsconfig.node.json if it doesn't exist
if [ ! -f "tsconfig.node.json" ]; then
    echo "⚙️  Creating Node TypeScript configuration..."
    cat > tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF
fi

# Create basic src structure if it doesn't exist
if [ ! -d "src" ]; then
    echo "📁 Creating basic src structure..."
    mkdir -p src/{components,pages,hooks,services,utils,types,styles}
    
    # Create basic App component
    cat > src/App.tsx << 'EOF'
import React from 'react';
import { ConfigProvider, Layout, Typography } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title } = Typography;

function App() {
  return (
    <ConfigProvider>
      <Router>
        <Layout style={{ minHeight: '100vh' }}>
          <Header style={{ display: 'flex', alignItems: 'center' }}>
            <Title level={3} style={{ color: 'white', margin: 0 }}>
              Metadata Builder
            </Title>
          </Header>
          <Content style={{ padding: '24px' }}>
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Title level={2}>Welcome to Metadata Builder</Title>
              <p>Your modern interface for database metadata management</p>
            </div>
          </Content>
        </Layout>
      </Router>
    </ConfigProvider>
  );
}

export default App;
EOF

    # Create main entry point
    cat > src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import 'antd/dist/reset.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF

    # Create index.html
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Metadata Builder</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF
fi

echo "✅ Frontend setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. cd frontend"
echo "   2. npm run dev    # Start development server"
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Other useful commands:"
echo "   npm run build    # Build for production"
echo "   npm run test     # Run tests"
echo "   npm run lint     # Check code quality"
echo ""
echo "🔧 Make sure the backend API is running on http://localhost:8000"
echo "   Run: python -m metadata_builder.api.server" 