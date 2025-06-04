#!/bin/bash

# Frontend Setup Script with Dependency Conflict Resolution
# This script handles the React dependency conflicts automatically

set -e  # Exit on any error

echo "🚀 Setting up Metadata Builder Frontend (Simple Mode)"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "metadata_builder" ]; then
    echo "❌ Error: Please run this script from the metadata-builder root directory"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ Error: $1 is not installed. Please install it first."
        echo "📖 Visit: https://nodejs.org/ for Node.js installation"
        exit 1
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."
check_command node
check_command npm

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ $NODE_VERSION -lt 18 ]; then
    echo "❌ Error: Node.js 18+ required. Current version: $(node --version)"
    exit 1
fi

echo "✅ Node.js $(node --version) detected"
echo "✅ npm $(npm --version) detected"

# Create frontend directory if it doesn't exist
if [ ! -d "frontend" ]; then
    echo "📁 Creating frontend directory..."
    mkdir frontend
fi

cd frontend

# Create package.json
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

# Install dependencies with legacy peer deps to handle conflicts
echo "📥 Installing dependencies (this may take a few minutes)..."
npm install --legacy-peer-deps

# Create TypeScript configurations
echo "⚙️ Creating TypeScript configuration..."
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

# Create Vite configuration
echo "⚙️ Creating Vite configuration..."
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
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
          editor: ['@monaco-editor/react']
        }
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts'
  }
})
EOF

# Create basic index.html
echo "📄 Creating index.html..."
cat > index.html << 'EOF'
<!doctype html>
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

# Create source directory structure
echo "📁 Creating source directory structure..."
mkdir -p src/{components,pages,hooks,services,utils,types,styles,test}

# Create main.tsx
cat > src/main.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import 'antd/dist/reset.css'
import App from './App.tsx'
import './styles/global.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <App />
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
EOF

# Create App.tsx
cat > src/App.tsx << 'EOF'
import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import WelcomePage from './pages/WelcomePage'
import './styles/App.css'

const { Content } = Layout

function App() {
  return (
    <Router>
      <Layout className="app-layout">
        <Content className="app-content">
          <Routes>
            <Route path="/" element={<WelcomePage />} />
          </Routes>
        </Content>
      </Layout>
    </Router>
  )
}

export default App
EOF

# Create Welcome Page
cat > src/pages/WelcomePage.tsx << 'EOF'
import React from 'react'
import { Card, Typography, Space, Button, Divider } from 'antd'
import { DatabaseOutlined, ApiOutlined, FileTextOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const WelcomePage: React.FC = () => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div style={{ textAlign: 'center' }}>
          <Title level={1}>
            <DatabaseOutlined style={{ marginRight: '0.5rem' }} />
            Metadata Builder
          </Title>
          <Paragraph style={{ fontSize: '1.2rem', color: '#666' }}>
            Generate structured metadata from database tables with LLM-enhanced capabilities
          </Paragraph>
        </div>

        <Divider />

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          <Card
            title={
              <span>
                <DatabaseOutlined style={{ marginRight: '0.5rem' }} />
                Database Connections
              </span>
            }
            hoverable
          >
            <Paragraph>
              Connect to various database types including PostgreSQL, MySQL, SQLite, Oracle, BigQuery, and more.
            </Paragraph>
            <Button type="primary" block>
              Manage Connections
            </Button>
          </Card>

          <Card
            title={
              <span>
                <FileTextOutlined style={{ marginRight: '0.5rem' }} />
                Metadata Generation
              </span>
            }
            hoverable
          >
            <Paragraph>
              Generate comprehensive metadata with statistical analysis and LLM-enhanced descriptions.
            </Paragraph>
            <Button type="primary" block>
              Generate Metadata
            </Button>
          </Card>

          <Card
            title={
              <span>
                <ApiOutlined style={{ marginRight: '0.5rem' }} />
                LookML Models
              </span>
            }
            hoverable
          >
            <Paragraph>
              Create semantic models and LookML views automatically from your database schema.
            </Paragraph>
            <Button type="primary" block>
              Generate LookML
            </Button>
          </Card>
        </div>

        <Card title="Features" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <div>
              <Title level={4}>🔌 Multi-Database Support</Title>
              <Paragraph>Connect to PostgreSQL, MySQL, SQLite, Oracle, BigQuery, Kinetica, and DuckDB</Paragraph>
            </div>
            <div>
              <Title level={4}>🤖 LLM Integration</Title>
              <Paragraph>AI-powered metadata generation with intelligent descriptions and analysis</Paragraph>
            </div>
            <div>
              <Title level={4}>📊 Visual Analytics</Title>
              <Paragraph>Data quality metrics, statistical analysis, and interactive charts</Paragraph>
            </div>
            <div>
              <Title level={4}>🔄 Real-time Updates</Title>
              <Paragraph>Live progress tracking and WebSocket integration for instant feedback</Paragraph>
            </div>
          </div>
        </Card>
      </Space>
    </div>
  )
}

export default WelcomePage
EOF

# Create global CSS
cat > src/styles/global.css << 'EOF'
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}

#root {
  min-height: 100vh;
}
EOF

cat > src/styles/App.css << 'EOF'
.app-layout {
  min-height: 100vh;
  background: #f5f5f5;
}

.app-content {
  padding: 0;
}
EOF

# Create test setup
cat > src/test/setup.ts << 'EOF'
import '@testing-library/jest-dom'
EOF

# Create environment file
echo "🔧 Creating environment configuration..."
cat > .env.local << 'EOF'
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development
EOF

# Create Dockerfile for the frontend
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
# Multi-stage build for React frontend
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy build files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create health check endpoint
RUN echo '<!DOCTYPE html><html><body>OK</body></html>' > /usr/share/nginx/html/health

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx configuration
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;
        index index.html index.htm;

        # Security
        server_tokens off;

        # Frontend routes
        location / {
            try_files $uri $uri/ /index.html;
        }

        # API proxy
        location /api {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket proxy
        location /ws {
            proxy_pass http://api:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

cd ..

echo ""
echo "✅ Frontend setup completed successfully!"
echo ""
echo "📂 Frontend directory structure created:"
echo "   frontend/"
echo "   ├── src/"
echo "   │   ├── components/"
echo "   │   ├── pages/"
echo "   │   ├── hooks/"
echo "   │   ├── services/"
echo "   │   ├── utils/"
echo "   │   ├── types/"
echo "   │   ├── styles/"
echo "   │   └── test/"
echo "   ├── package.json"
echo "   ├── vite.config.ts"
echo "   ├── tsconfig.json"
echo "   ├── Dockerfile"
echo "   └── nginx.conf"
echo ""
echo "🚀 Next steps:"
echo "   1. Start the backend API: python -m metadata_builder.api.server"
echo "   2. Start the frontend: cd frontend && npm run dev"
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "🐳 Or use Docker Compose:"
echo "   docker-compose -f docker/docker-compose.fullstack.yml up"
echo ""
echo "📖 For more information, see documentation/FRONTEND_INSTALLATION.md" 