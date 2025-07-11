import axios from 'axios';
import authService from './authService.js';

// Create axios instance with base configuration
// Force API to use port 8000 for backend connection
let apiBaseURL = 'http://localhost:8000';

// Handle proxy environments (like rocket.new or similar services)
if (typeof window !== 'undefined') {
  const currentHost = window.location.hostname;
  const currentPort = window.location.port;
  
  // Always force API to use port 8000 for backend, regardless of frontend port
  apiBaseURL = `http://${currentHost}:8000`;
  
  console.log(`Frontend running on port ${currentPort}. Forcing API to backend at: ${apiBaseURL}`);
}

console.log('API Base URL:', apiBaseURL);

const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 120000, // Increased to 2 minutes for BigQuery operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging and auth
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    
    // Always fetch token directly from localStorage to survive page reloads
    const token = localStorage.getItem('auth_token') || authService.token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling and auth
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      console.warn('Authentication failed, logging out...');
      authService.logout();
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// Database Connection APIs
export const databaseAPI = {
  // List all database connections
  listConnections: () => api.get('/api/v1/database/connections'),

  // Create new database connection
  createConnection: (connectionData) => 
    api.post('/api/v1/database/connections', connectionData),

  // Get specific database connection
  getConnection: (connectionName) => 
    api.get(`/api/v1/database/connections/${connectionName}`),

  // Delete database connection
  deleteConnection: (connectionName) => 
    api.delete(`/api/v1/database/connections/${connectionName}`),

  // Test database connection
  testConnection: (connectionName) => 
    api.post(`/api/v1/database/connections/${connectionName}/test`),

  // Get database schemas
  getSchemas: (connectionName) => 
    api.get(`/api/v1/database/connections/${connectionName}/schemas`),

  // Get tables in a schema
  getTables: (connectionName, schemaName) => 
    api.get(`/api/v1/database/connections/${connectionName}/schemas/${schemaName}/tables`),

  // Get table information
  getTableInfo: (connectionName, schemaName, tableName) => 
    api.get(`/api/v1/database/connections/${connectionName}/schemas/${schemaName}/tables/${tableName}`),

  // Predefined Schema Management
  getPredefinedSchemas: (connectionName) =>
    api.get(`/api/v1/database/connections/${connectionName}/predefined-schemas`),

  updatePredefinedSchemas: (connectionName, predefinedSchemas) =>
    api.put(`/api/v1/database/connections/${connectionName}/predefined-schemas`, {
      predefined_schemas: predefinedSchemas
    }),

  addSchemaToConnection: (connectionName, schemaName, filterConfig) =>
    api.post(`/api/v1/database/connections/${connectionName}/predefined-schemas/${schemaName}`, filterConfig),

  removeSchemaFromConnection: (connectionName, schemaName) =>
    api.delete(`/api/v1/database/connections/${connectionName}/predefined-schemas/${schemaName}`),
};

// Metadata Generation APIs
export const metadataAPI = {
  // Generate metadata synchronously
  generateMetadataSync: (requestData) =>
    api.post('/api/v1/metadata/generate', requestData, {
      timeout: 300000 // 5 minutes
    }),

  // Generate metadata asynchronously
  generateMetadataAsync: (requestData) =>
    api.post('/api/v1/metadata/generate/async', requestData),

  // Generate LookML synchronously
  generateLookMLSync: (requestData) => 
    api.post('/api/v1/metadata/lookml/generate', requestData),

  // Generate LookML asynchronously
  generateLookMLAsync: (requestData) => 
    api.post('/api/v1/metadata/lookml/generate/async', requestData),

  // Get job status
  getJobStatus: (jobId) => 
    api.get(`/api/v1/metadata/jobs/${jobId}`),

  // Update metadata manually
  updateMetadata: (requestData) =>
    api.post('/api/v1/metadata/update', requestData),

  // Update metadata with AI assistance
  updateMetadataWithAI: (requestData) =>
    api.post('/api/v1/metadata/update/ai', requestData),

  // Get stored metadata for a table
  getStoredMetadata: (dbName, schemaName, tableName) =>
    api.get(`/api/v1/metadata/stored/${dbName}/${schemaName}/${tableName}`),

  // Check if metadata exists for a table and return it if available
  checkMetadataExists: (dbName, schemaName, tableName) =>
    api.get(`/api/v1/metadata/stored/${dbName}/${schemaName}/${tableName}`),

  // Save generated metadata (auto-called after generation)
  saveMetadata: (dbName, schemaName, tableName, metadata) =>
    api.post('/api/v1/metadata/store', {
      db_name: dbName,
      schema_name: schemaName,
      table_name: tableName,
      metadata: metadata,
      created_at: new Date().toISOString()
    }),

  // Get sample data for a table
  getSampleData: (dbName, schemaName, tableName, sampleSize = 100, numSamples = 2) =>
    api.get(`/api/v1/metadata/sample-data/${dbName}/${schemaName}/${tableName}`, {
      params: { sample_size: sampleSize, num_samples: numSamples }
    }),

  // Get test sample data for a table (fallback)
  getSampleDataTest: (dbName, schemaName, tableName, sampleSize = 100, numSamples = 2) =>
    api.get(`/api/v1/metadata/sample-data-test/${dbName}/${schemaName}/${tableName}`, {
      params: { sample_size: sampleSize, num_samples: numSamples }
    }),

  // Delete stored metadata
  deleteStoredMetadata: (dbName, schemaName, tableName) =>
    api.delete(`/api/v1/metadata/stored/${dbName}/${schemaName}/${tableName}`),

  // List all tables with stored metadata for a connection
  listTablesWithMetadata: (dbName) =>
    api.get(`/api/v1/metadata/tables/${dbName}`),

  // Bulk operations
  generateMetadataForMultipleTables: (dbName, tables, configuration) =>
    api.post('/api/v1/metadata/generate/bulk', {
      db_name: dbName,
      tables: tables,
      configuration: configuration
    }),

  // Enhanced generation with auto-save
  generateAndSaveMetadata: async (requestData) => {
    try {
      // Generate the metadata
      const response = await api.post('/api/v1/metadata/generate', requestData, {
        timeout: 300000 // 5 minutes
      });
      
      const metadata = response.data;
      
      // Auto-save the generated metadata
      if (metadata && requestData.db_name && requestData.schema_name && requestData.table_name) {
        try {
          await metadataAPI.saveMetadata(
            requestData.db_name,
            requestData.schema_name, 
            requestData.table_name,
            metadata
          );
          console.log('Metadata auto-saved successfully');
        } catch (saveError) {
          console.warn('Failed to auto-save metadata:', saveError);
          // Don't fail the whole operation if save fails
        }
      }
      
      return response;
    } catch (error) {
      console.error('Metadata generation failed:', error);
      throw error;
    }
  }
};

// AI Agent APIs
export const agentAPI = {
  // Chat with AI agent
  chat: (chatData) => 
    api.post('/api/v1/agent/chat', chatData),

  // Get agent status
  getStatus: () => 
    api.get('/api/v1/agent/status'),

  // Get conversation summary
  getConversationSummary: (userId, sessionId = null) => {
    const params = sessionId ? { session_id: sessionId } : {};
    return api.get(`/api/v1/agent/conversation/${userId}/summary`, { params });
  },

  // Clear conversation
  clearConversation: (userId, sessionId = null) => {
    const params = sessionId ? { session_id: sessionId } : {};
    return api.delete(`/api/v1/agent/conversation/${userId}`, { params });
  },

  // Create task from natural language
  createTaskFromNaturalLanguage: (taskData) => 
    api.post('/api/v1/agent/tasks/natural-language', taskData),

  // Get task queue
  getTaskQueue: () => 
    api.get('/api/v1/agent/tasks'),
};

// Health and Info APIs
export const systemAPI = {
  // Health check
  healthCheck: () => 
    api.get('/health'),

  // API info
  getApiInfo: () => 
    api.get('/api/v1/info'),
};

// Utility functions for common operations
export const apiUtils = {
  // Build metadata generation request
  buildMetadataRequest: ({
    dbName,
    tableName,
    schemaName = 'public',
    analysisSql = null,
    sampleSize = 100,
    numSamples = 5,
    maxPartitions = 10,
    customPrompt = null,
    includeRelationships = false,
    includeAggregationRules = true,
    includeQueryRules = false,
    includeDataQuality = true,
    includeQueryExamples = true,
    includeAdditionalInsights = false,
    includeBusinessRules = false,
    includeCategoricalDefinitions = true,
  }) => ({
    db_name: dbName,
    table_name: tableName,
    schema_name: schemaName,
    analysis_sql: analysisSql,
    sample_size: sampleSize,
    num_samples: numSamples,
    max_partitions: maxPartitions,
    additional_prompt: customPrompt,
    include_relationships: includeRelationships,
    include_aggregation_rules: includeAggregationRules,
    include_query_rules: includeQueryRules,
    include_data_quality: includeDataQuality,
    include_query_examples: includeQueryExamples,
    include_additional_insights: includeAdditionalInsights,
    include_business_rules: includeBusinessRules,
    include_categorical_definitions: includeCategoricalDefinitions,
  }),

  // Build LookML generation request
  buildLookMLRequest: ({
    dbName,
    tableNames,
    modelName,
    schemaName = 'public',
    includeDerivedTables = false,
    includeExplores = true,
    additionalPrompt = null,
    generationType = 'full',
    existingLookml = null,
    tokenThreshold = 8000,
  }) => ({
    db_name: dbName,
    table_names: tableNames,
    model_name: modelName,
    schema_name: schemaName,
    include_derived_tables: includeDerivedTables,
    include_explores: includeExplores,
    additional_prompt: additionalPrompt,
    generation_type: generationType,
    existing_lookml: existingLookml,
    token_threshold: tokenThreshold,
  }),

  // Build database connection request
  buildConnectionRequest: ({
    name,
    type,
    host = null,
    port = null,
    username = null,
    password = null,
    database = null,
    serviceName = null,
    sid = null,
    tnsName = null,
    projectId = null,
    credentialsPath = null,
    predefinedSchemas = null,
  }) => ({
    name,
    type,
    host,
    port,
    username,
    password,
    database,
    service_name: serviceName,
    sid,
    tns_name: tnsName,
    project_id: projectId,
    credentials_path: credentialsPath,
    predefined_schemas: predefinedSchemas,
  }),

  // Build chat request
  buildChatRequest: (userId, message, sessionId = null, context = {}) => ({
    user_id: userId,
    message,
    session_id: sessionId,
    context: {
      current_database: context.database,
      current_schema: context.schema,
      current_table: context.table,
      table_metadata: context.tableMetadata,
      database_type: context.databaseType,
      ...context
    }
  }),

  // Handle API errors with user-friendly messages
  handleApiError: (error) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      
      switch (status) {
        case 400:
          return data.detail || 'Invalid request. Please check your input.';
        case 401:
          return 'Authentication required. Please check your API credentials.';
        case 403:
          return 'Access denied. You do not have permission for this operation.';
        case 404:
          return 'Resource not found. Please check if the connection or table exists.';
        case 422:
          return data.detail || 'Validation error. Please check your input parameters.';
        case 500:
          return 'Server error. Please try again later or contact support.';
        default:
          return data.detail || `Server error (${status}). Please try again.`;
      }
    } else if (error.request) {
      // Network error
      return 'Network error. Please check your connection and try again.';
    } else {
      // Other error
      return error.message || 'An unexpected error occurred.';
    }
  },

  // Polling utility for job status
  pollJobStatus: async (jobId, onUpdate, intervalMs = 2000, maxAttempts = 100) => {
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const response = await metadataAPI.getJobStatus(jobId);
          const job = response.data;
          
          onUpdate(job);
          
          if (job.status === 'completed' || job.status === 'failed') {
            resolve(job);
          } else if (attempts >= maxAttempts) {
            reject(new Error('Polling timeout: Job did not complete within expected time'));
          } else {
            attempts++;
            setTimeout(poll, intervalMs);
          }
        } catch (error) {
          reject(error);
        }
      };
      
      poll();
    });
  },

  // Format table data for display
  formatTableData: (tableInfo) => ({
    id: `${tableInfo.schema_name}.${tableInfo.table_name}`,
    name: tableInfo.table_name,
    schema: tableInfo.schema_name,
    columnCount: tableInfo.column_count,
    rowCount: tableInfo.row_count,
    columns: tableInfo.columns,
  }),

  // Format connection data for display
  formatConnectionData: (connection) => ({
    id: connection.name,
    name: connection.name,
    type: connection.type,
    host: connection.host,
    port: connection.port,
    database: connection.database,
    status: connection.status || 'unknown',
    createdAt: new Date(connection.created_at),
  }),
};

// Export the configured axios instance for custom requests
export default api; 