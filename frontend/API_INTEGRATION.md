# API Integration Documentation

## Overview

The frontend has been fully integrated with the backend APIs using a comprehensive service layer. This document explains the integration points and how to configure them.

## Configuration

### Environment Variables

Create a `.env` file in the frontend directory with the following variables:

```bash
# API Configuration (Vite uses VITE_ prefix)
VITE_API_URL=http://localhost:8000

# For production, update this to your actual backend URL
# VITE_API_URL=https://your-production-api.com

# Development Settings
VITE_ENV=development

# Feature Flags
VITE_ENABLE_DEBUG_LOGS=true
VITE_ENABLE_POLLING=true
VITE_POLLING_INTERVAL=2000
```

### Backend Requirements

Make sure your backend server is running on the configured URL (default: `http://localhost:8000`) with the following endpoints available:

- **Database Connections**: `/api/v1/database/connections`
- **Metadata Generation**: `/api/v1/metadata/generate`
- **AI Agent**: `/api/v1/agent/chat`
- **Health Check**: `/health`

## API Service Layer

### File Structure

```
frontend/src/services/
└── api.js                    # Main API service layer
```

### API Modules

The API service is organized into several modules:

#### Database API (`databaseAPI`)
- `listConnections()` - Get all database connections
- `createConnection(data)` - Create new connection
- `getConnection(name)` - Get specific connection
- `deleteConnection(name)` - Delete connection
- `testConnection(name)` - Test connection
- `getSchemas(name)` - Get database schemas
- `getTables(name, schema)` - Get tables in schema
- `getTableInfo(name, schema, table)` - Get table details

#### Metadata API (`metadataAPI`)
- `generateMetadataSync(request)` - Generate metadata synchronously
- `generateMetadataAsync(request)` - Generate metadata asynchronously
- `generateLookMLSync(request)` - Generate LookML synchronously
- `generateLookMLAsync(request)` - Generate LookML asynchronously
- `getJobStatus(jobId)` - Get background job status

#### AI Agent API (`agentAPI`)
- `chat(chatData)` - Send chat message to AI agent
- `getStatus()` - Get agent status
- `getConversationSummary(userId, sessionId)` - Get conversation summary
- `clearConversation(userId, sessionId)` - Clear conversation
- `createTaskFromNaturalLanguage(taskData)` - Create task from natural language
- `getTaskQueue()` - Get task queue status

#### System API (`systemAPI`)
- `healthCheck()` - Check system health
- `getApiInfo()` - Get API information

### Utility Functions (`apiUtils`)

The service layer includes utility functions for:

- **Request Building**: Helper functions to build properly formatted requests
- **Error Handling**: Convert API errors to user-friendly messages
- **Data Formatting**: Transform API responses for frontend consumption
- **Job Polling**: Utility for polling background job status

## Integration Points

### Database Connections Dashboard

**File**: `frontend/src/pages/database-connections-dashboard/index.jsx`

**Features**:
- Loads connections from `/api/v1/database/connections`
- Tests connections using `/api/v1/database/connections/{name}/test`
- Creates/deletes connections via API
- Real-time connection status updates
- Error handling with user-friendly messages

### Add/Edit Database Connection

**File**: `frontend/src/pages/add-edit-database-connection/index.jsx`

**Features**:
- Creates new connections via `/api/v1/database/connections`
- Validates and tests connections before saving
- Supports all database types from the backend
- Proper error handling and validation

### Metadata Generation

**File**: `frontend/src/pages/metadata-generation/index.jsx`

**Features**:
- Loads database schemas and tables dynamically
- Starts metadata generation jobs via `/api/v1/metadata/generate/async`
- Real-time job monitoring with polling
- Configurable generation parameters
- Background job status tracking

### AI Chat Interface

**File**: `frontend/src/pages/ai-chat-interface/index.jsx`

**Features**:
- Real-time chat with AI agent via `/api/v1/agent/chat`
- Message status tracking
- Error handling for failed messages
- Intent and entity extraction display

## Error Handling

The frontend implements comprehensive error handling:

### Error Display Components
- Red error banners with dismiss functionality
- Specific error messages based on HTTP status codes
- Fallback error messages for network issues

### Error Types Handled
- **400**: Invalid request - validation errors
- **401**: Authentication required
- **403**: Access denied
- **404**: Resource not found
- **422**: Validation errors with details
- **500**: Server errors
- **Network**: Connection issues

### Error Recovery
- Automatic retry mechanisms for polling
- Graceful fallbacks when APIs are unavailable
- Clear user feedback on error states

## Loading States

The frontend provides loading indicators for:

- **Connection Lists**: Spinner while loading connections
- **Schema Loading**: Progressive loading of database schemas
- **Job Monitoring**: Real-time progress updates
- **Chat Messages**: Typing indicators and message status

## Real-time Features

### Job Polling
- Automatic polling of background job status
- Configurable polling intervals
- Automatic cleanup when jobs complete

### Connection Status
- Real-time connection testing
- Status updates without page refresh
- Health monitoring integration

## Testing the Integration

### Prerequisites
1. Backend server running on configured URL
2. Database connections configured in backend
3. OpenAI API key configured for AI features

### Basic Testing Steps

1. **Connection Management**:
   ```bash
   # Visit database connections dashboard
   http://localhost:3000/database-connections-dashboard
   
   # Add a new connection
   http://localhost:3000/add-edit-database-connection
   ```

2. **Metadata Generation**:
   ```bash
   # Visit metadata generation page
   http://localhost:3000/metadata-generation
   ```

3. **AI Chat**:
   ```bash
   # Visit AI chat interface
   http://localhost:3000/ai-chat-interface
   ```

### Debugging

Enable debug logging by setting `VITE_ENABLE_DEBUG_LOGS=true`. This will log:
- All API requests and responses
- Error details
- Job polling status
- Component state changes

## Production Considerations

### Environment Configuration
- Update `VITE_API_URL` to production backend URL
- Configure proper CORS settings on backend
- Set up SSL/TLS for secure communication

### Performance Optimization
- Implement request caching where appropriate
- Use pagination for large datasets
- Optimize polling intervals based on usage

### Security
- Implement proper authentication tokens
- Validate all user inputs
- Use HTTPS in production
- Handle sensitive data appropriately

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Ensure backend allows frontend origin
   - Check CORS configuration on backend

2. **Connection Timeouts**:
   - Verify backend server is running
   - Check network connectivity
   - Increase timeout values if needed

3. **Authentication Errors**:
   - Verify API keys are configured
   - Check authentication headers

4. **Polling Issues**:
   - Check backend job endpoints
   - Verify job IDs are valid
   - Monitor for memory leaks in polling

### Debug Tools

Use browser developer tools to:
- Monitor network requests in Network tab
- Check console for error logs
- Inspect API responses
- Monitor WebSocket connections (if implemented)

## Future Enhancements

### WebSocket Integration
Consider implementing WebSocket connections for:
- Real-time job updates
- Live chat with AI agent
- Connection status changes

### Caching Strategy
Implement intelligent caching for:
- Database schemas
- Connection status
- Job results

### Offline Support
Add service workers for:
- Offline functionality
- Background sync
- Cached responses 