# Frontend UI Requirements for Metadata Builder

## Overview

This document outlines the requirements for building and integrating a modern frontend user interface with the metadata-builder project. The frontend will provide a web-based interface to complement the existing CLI and API functionality.

## Architecture Requirements

### Frontend Technology Stack

#### Core Framework Options
1. **React.js** (Recommended)
   - TypeScript support for type safety
   - Component-based architecture
   - Rich ecosystem and community support
   - Excellent integration with REST APIs

2. **Vue.js** (Alternative)
   - Simpler learning curve
   - Good TypeScript support
   - Lightweight and performant

3. **Svelte/SvelteKit** (Modern Alternative)
   - Compile-time optimizations
   - Smaller bundle sizes
   - Built-in state management

#### UI Framework/Component Library
- **Ant Design** (React) - Comprehensive enterprise-class UI components
- **Material-UI (MUI)** (React) - Google Material Design components
- **Chakra UI** (React) - Modular and accessible components
- **Quasar** (Vue) - Vue.js based framework
- **Tailwind CSS** - Utility-first CSS framework (works with any framework)

#### Build Tools and Development
- **Vite** - Fast build tool and development server
- **TypeScript** - Type safety and better developer experience
- **ESLint & Prettier** - Code quality and formatting
- **Husky** - Git hooks for pre-commit checks

### Backend Integration Requirements

#### API Client Setup
```typescript
// API client configuration
interface APIClient {
  baseURL: string;
  timeout: number;
  interceptors: {
    request: RequestInterceptor[];
    response: ResponseInterceptor[];
  };
  auth?: AuthConfig;
}
```

#### WebSocket Integration (Future)
- Real-time updates for long-running metadata generation
- Live progress tracking for database operations
- Notification system for completed tasks

## Functional Requirements

### Core Features

#### 1. Database Connection Management
- **Connection Creation Form**
  - Support all database types (PostgreSQL, MySQL, SQLite, Oracle, BigQuery, Kinetica, DuckDB)
  - Connection testing before saving
  - Secure credential handling
  - Import/export connection configurations

- **Connection Dashboard**
  - List all configured connections
  - Connection status indicators
  - Quick connect/disconnect actions
  - Connection usage statistics

#### 2. Schema and Table Explorer
- **Interactive Schema Browser**
  - Hierarchical tree view of databases → schemas → tables
  - Search and filter capabilities
  - Table statistics (row count, size, last modified)
  - Visual indicators for table types (views, materialized views, etc.)

- **Table Detail View**
  - Column list with data types and constraints
  - Sample data preview
  - Table relationships visualization
  - Partition information (for BigQuery)

#### 3. Metadata Generation Interface
- **Metadata Configuration**
  - Sample size configuration
  - Number of samples selection
  - Advanced options (statistical analysis, LLM enhancement)
  - Custom SQL query input

- **Generation Progress**
  - Real-time progress tracking
  - Step-by-step status updates
  - Cancellation capability
  - Error handling and recovery

- **Results Display**
  - Interactive metadata viewer
  - JSON/YAML format toggle
  - Download/export options
  - Metadata editing capabilities

#### 4. LookML Generation Interface
- **LookML Configuration**
  - Model name specification
  - Include/exclude options (derives, explores)
  - Custom prompt input
  - Template selection

- **LookML Preview and Export**
  - Syntax-highlighted LookML code
  - Side-by-side metadata comparison
  - Download as .lkml files
  - Integration with Looker (if API available)

#### 5. Advanced Analytics Dashboard
- **Data Quality Metrics**
  - Visual representation of completeness, uniqueness
  - Distribution charts for numerical columns
  - Categorical value frequency charts
  - Data quality trends over time

- **Column Analysis**
  - Statistical summaries
  - Missing value patterns
  - Outlier detection
  - Business rule suggestions

### User Experience Requirements

#### Navigation and Layout
- **Responsive Design**
  - Mobile-friendly interface
  - Tablet optimization
  - Desktop-first approach with progressive enhancement

- **Intuitive Navigation**
  - Breadcrumb navigation
  - Contextual menus
  - Keyboard shortcuts
  - Search functionality across all data

#### Accessibility
- **WCAG 2.1 AA Compliance**
  - Screen reader compatibility
  - Keyboard navigation
  - High contrast mode
  - Focus indicators

#### Performance
- **Loading States**
  - Skeleton screens for data loading
  - Progressive loading for large datasets
  - Lazy loading for tables and charts

- **Caching Strategy**
  - Client-side caching for connection metadata
  - Server-side response caching
  - Offline capability for previously loaded data

## Technical Requirements

### Frontend Dependencies

#### Core Dependencies (React Example)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "axios": "^1.6.2",
    "antd": "^5.12.5",
    "@ant-design/icons": "^5.2.6",
    "@tanstack/react-query": "^5.8.4",
    "react-hook-form": "^7.48.2",
    "@hookform/resolvers": "^3.3.2",
    "yup": "^1.3.3",
    "recharts": "^2.8.0",
    "@monaco-editor/react": "^4.6.0",
    "js-yaml": "^4.1.0",
    "@uiw/react-json-view": "^2.0.0-alpha.18",
    "dayjs": "^1.11.10",
    "zustand": "^4.4.7",
    "immer": "^10.0.3",
    "react-toastify": "^9.1.3",
    "lodash-es": "^4.17.21"
  },
  "devDependencies": {
    "@types/react": "^18.2.39",
    "@types/react-dom": "^18.2.17",
    "@typescript-eslint/eslint-plugin": "^6.13.1",
    "@typescript-eslint/parser": "^6.13.1",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.2",
    "vite": "^5.0.5",
    "vitest": "^1.0.1",
    "@playwright/test": "^1.40.1",
    "eslint": "^8.54.0",
    "eslint-plugin-react": "^7.33.2",
    "eslint-plugin-react-hooks": "^4.6.0",
    "prettier": "^3.1.0",
    "husky": "^8.0.3",
    "lint-staged": "^15.2.0",
    "@storybook/react-vite": "^7.6.5"
  }
}
```

#### Additional Libraries
- **State Management**: Zustand (preferred) or Redux Toolkit
- **Forms**: React Hook Form with Yup validation and @hookform/resolvers
- **Async Data**: @tanstack/react-query for server state management
- **Charts**: Recharts or Chart.js
- **Code Editor**: @monaco-editor/react (VS Code editor)
- **Date Handling**: dayjs or date-fns
- **Notifications**: react-toastify or antd notifications
- **Keyboard Shortcuts**: react-hotkeys-hook
- **Head Management**: react-helmet-async

### Backend Requirements Updates

#### API Enhancements Needed
```python
# Additional FastAPI dependencies
fastapi-cors = "^0.4.0"          # CORS handling
fastapi-cache2 = "^0.2.0"        # Response caching
websockets = "^11.0.0"           # WebSocket support
python-multipart = "^0.0.6"     # File upload support
redis = "^4.5.0"                 # Session/cache storage
celery = "^5.2.0"                # Background task processing
```

#### New API Endpoints Required
1. **File Management**
   - Upload metadata files
   - Download generated files
   - Template management

2. **WebSocket Endpoints**
   - Real-time progress updates
   - Live notifications
   - Connection status monitoring

3. **User Preferences**
   - Save UI preferences
   - Recent connections/tables
   - Custom themes

### Development Environment Setup

#### Frontend Development Server
```bash
# Install Node.js dependencies
npm install

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint and format
npm run lint
npm run format
```

#### Integration Testing
- **End-to-End Testing**: Playwright or Cypress
- **Unit Testing**: Vitest or Jest
- **API Testing**: Integration with existing pytest suite

### Deployment Requirements

#### Docker Configuration
```dockerfile
# Frontend Dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose Integration
```yaml
# Updated docker-compose.yml
version: '3.8'
services:
  api:
    build: 
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - api
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

#### Production Deployment
- **Reverse Proxy**: Nginx configuration for serving frontend and proxying API
- **SSL/TLS**: Certificate management for HTTPS
- **CDN Integration**: Static asset delivery optimization
- **Environment Configuration**: Separate configs for dev/staging/prod

## Security Requirements

### Authentication and Authorization
- **JWT Token-based Authentication**
- **Role-based Access Control** (Admin, User, Viewer)
- **API Key Management** for LLM services
- **Secure credential storage** (encrypted in backend)

### Data Protection
- **Input Validation**: All form inputs sanitized
- **XSS Protection**: Content Security Policy implementation
- **CSRF Protection**: Token-based CSRF protection
- **Secure Headers**: Security headers configuration

## Integration Specifications

### API Communication
```typescript
// API service structure
class MetadataBuilderAPI {
  // Database operations
  async getDatabases(): Promise<Database[]>
  async createConnection(config: DatabaseConfig): Promise<Connection>
  async testConnection(config: DatabaseConfig): Promise<boolean>
  
  // Metadata operations
  async generateMetadata(request: MetadataRequest): Promise<MetadataResponse>
  async generateLookML(request: LookMLRequest): Promise<LookMLResponse>
  
  // File operations
  async downloadMetadata(format: 'json' | 'yaml'): Promise<Blob>
  async uploadMetadata(file: File): Promise<UploadResponse>
}
```

### Error Handling
- **Graceful Degradation**: Fallback UI when API is unavailable
- **Error Boundaries**: React error boundaries for component failures
- **User-Friendly Messages**: Clear error messages with suggested actions
- **Retry Mechanisms**: Automatic retry for transient failures

### Performance Optimization
- **Code Splitting**: Dynamic imports for large components
- **Bundle Optimization**: Tree shaking and minification
- **Image Optimization**: WebP support with fallbacks
- **Caching Strategy**: Service Worker for offline functionality

## Documentation Requirements

### User Documentation
- **User Guide**: Step-by-step usage instructions
- **Video Tutorials**: Screen recordings for common workflows
- **FAQ**: Common questions and troubleshooting
- **Keyboard Shortcuts**: Quick reference guide

### Developer Documentation
- **Component Documentation**: Storybook for component showcase
- **API Documentation**: OpenAPI/Swagger integration
- **Architecture Diagrams**: System architecture visualization
- **Contributing Guide**: Frontend development guidelines

## Timeline and Milestones

### Phase 1: Foundation (4-6 weeks)
- [ ] Project setup and configuration
- [ ] Basic layout and navigation
- [ ] Database connection management
- [ ] API integration layer

### Phase 2: Core Features (6-8 weeks)
- [ ] Schema and table explorer
- [ ] Metadata generation interface
- [ ] Results display and editing
- [ ] Basic analytics dashboard

### Phase 3: Advanced Features (4-6 weeks)
- [ ] LookML generation interface
- [ ] Advanced analytics and visualizations
- [ ] Real-time updates (WebSocket)
- [ ] File management system

### Phase 4: Polish and Optimization (2-4 weeks)
- [ ] Performance optimization
- [ ] Accessibility improvements
- [ ] Security hardening
- [ ] Documentation completion

## Success Metrics

### User Experience Metrics
- **Page Load Time**: < 2 seconds for initial load
- **Time to Interactive**: < 3 seconds
- **User Task Completion Rate**: > 95%
- **User Satisfaction Score**: > 4.5/5

### Technical Metrics
- **Test Coverage**: > 80%
- **Bundle Size**: < 1MB gzipped
- **API Response Time**: < 500ms for standard operations
- **Uptime**: > 99.9%

## Conclusion

This frontend UI will transform the metadata-builder from a CLI-only tool to a comprehensive, user-friendly platform. The requirements focus on creating a modern, accessible, and performant web application that seamlessly integrates with the existing FastAPI backend while providing an intuitive interface for all metadata generation and management tasks. 