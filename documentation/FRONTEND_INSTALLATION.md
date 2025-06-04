# Frontend Installation Guide

## Setup Script Options

You have **two setup script options** depending on your needs:

### Option 1: Standard Setup (Recommended)
```bash
./scripts/setup_frontend.sh
```
**Use this when:**
- You want the standard frontend setup
- You're setting up for the first time
- You want dependency conflict handling without legacy peer deps

### Option 2: Simple Setup (For Dependency Issues)
```bash
./scripts/setup_frontend_simple.sh
```
**Use this when:**
- You encounter React dependency conflicts
- You need legacy peer deps support
- The standard setup fails

## Quick Setup Guide

### 1. Prerequisites

- **Node.js 18+** and **npm 9+**
- **Git** for cloning the repository

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/rnednur/metadata-builder.git
cd metadata-builder

# Run the setup script (choose one)
./scripts/setup_frontend.sh              # Standard setup
# OR
./scripts/setup_frontend_simple.sh       # If you have dependency conflicts
```

### 3. Start Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Start Backend API (Required)

In another terminal:

```bash
# Install backend dependencies
pip install -e ".[frontend]"

# Start the API server
python -m metadata_builder.api.server
```

The API will be available at `http://localhost:8000`

## Alternative: Docker Setup

For a complete containerized setup:

```bash
# Use the full-stack Docker Compose
docker-compose -f docker/docker-compose.fullstack.yml up
```

This will start:
- Frontend at `http://localhost:3000`
- Backend API at `http://localhost:8000`
- Redis for caching
- Worker processes for background tasks

## Script Differences

### `setup_frontend.sh` (Standard)
- ✅ Creates complete package.json with all dependencies
- ✅ Uses standard npm install (no legacy peer deps)
- ✅ Sets up full TypeScript configuration
- ✅ Creates comprehensive React application structure
- ✅ Better for most users

### `setup_frontend_simple.sh` (Legacy Support)
- ✅ Handles React 18 dependency conflicts
- ✅ Uses `--legacy-peer-deps` flag
- ✅ Creates enhanced frontend structure
- ✅ Includes comprehensive development tools
- ✅ Better for environments with dependency issues

## Troubleshooting

### Common Issues and Solutions

#### 1. React Version Conflicts

**Error**: `ERESOLVE unable to resolve dependency tree`

**Solution**: Use the simple setup script:
```bash
./scripts/setup_frontend_simple.sh
```

#### 2. TypeScript Configuration Missing

**Error**: `tsconfig.node.json failed: Error: ENOENT: no such file or directory`

**Solution**: Both scripts create this automatically. If missing, re-run:
```bash
./scripts/setup_frontend.sh
```

#### 3. Vite Configuration Issues

**Error**: Vite build or dev server issues

**Solution**: Both scripts create proper vite.config.ts files automatically.

#### 4. Script Permission Issues

**Error**: `Permission denied`

**Solution**: Make scripts executable:
```bash
chmod +x scripts/setup_frontend.sh
chmod +x scripts/setup_frontend_simple.sh
```

#### 5. Wrong Directory

**Error**: Script fails to find files

**Solution**: Always run from the project root:
```bash
cd metadata-builder
./scripts/setup_frontend.sh
```

### Environment Variables

Both scripts create a `.env.local` file in the frontend directory:

```env
# Frontend Environment Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development
```

## Development Commands

```bash
# Development server
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run tests with UI
npm run test:ui

# Run E2E tests
npm run test:e2e

# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format

# Check formatting
npm run format:check

# Storybook (component documentation)
npm run storybook

# Build Storybook
npm run build-storybook

# Analyze bundle
npm run analyze
```

## Project Structure

After setup, your frontend directory will have:

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page components
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API services
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript type definitions
│   ├── styles/        # Global styles
│   ├── App.tsx        # Main App component
│   └── main.tsx       # Entry point
├── public/            # Static assets
├── package.json       # Dependencies and scripts
├── vite.config.ts     # Vite configuration
├── tsconfig.json      # TypeScript configuration
├── tsconfig.node.json # Node TypeScript configuration
├── .env.local         # Environment variables
└── index.html         # HTML template
```

## Next Steps

1. **Explore the UI**: Open `http://localhost:3000` to see the welcome page
2. **Check API Connection**: Make sure `http://localhost:8000/docs` shows the API documentation
3. **Start Development**: Begin building components in the `src/components` directory
4. **Read the Requirements**: Check `documentation/FRONTEND_REQUIREMENTS.md` for detailed feature specifications

## Getting Help

If you're still having issues:

1. **Check Node/npm versions**: `node -v` && `npm -v`
2. **Clear npm cache**: `npm cache clean --force`
3. **Delete node_modules**: `rm -rf frontend/node_modules frontend/package-lock.json && ./scripts/setup_frontend.sh`
4. **Check the logs**: Look for detailed error messages in the terminal
5. **Try the simple script**: `./scripts/setup_frontend_simple.sh`

## Production Deployment

For production deployment, see the Docker configuration in:
- `frontend/Dockerfile`
- `docker/docker-compose.fullstack.yml`
- `frontend/nginx.conf`

The production build includes:
- Optimized bundle with code splitting
- Nginx reverse proxy
- Security headers
- Health checks
- Multi-stage Docker build 