import axios, { AxiosResponse } from 'axios';
import type {
  DatabaseConnection,
  Table,
  TableMetadata,
  LookMLModel,
  Job,
  ApiResponse,
  PaginatedResponse,
  SearchParams,
  Schema
} from '../types';
import { 
  mockTableMetadata, 
  mockDatabaseConnections, 
  mockLookMLModels, 
  mockJobs,
  createPaginatedResponse 
} from './mockData';

const API_BASE_URL = import.meta.env.REACT_APP_API_URL || 'http://localhost:8000';
const USE_MOCK_DATA = import.meta.env.REACT_APP_USE_MOCK_DATA === 'true';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Helper function to make API call with fallback to mock data
async function apiCallWithFallback<T>(
  apiCall: () => Promise<T>,
  mockData: T,
  delay: number = 500
): Promise<T> {
  if (USE_MOCK_DATA) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, delay));
    return mockData;
  }

  try {
    return await apiCall();
  } catch (error) {
    console.warn('API call failed, falling back to mock data:', error);
    // Simulate network delay even for fallback
    await new Promise(resolve => setTimeout(resolve, delay));
    return mockData;
  }
}

// Database Connections API
export const databaseApi = {
  // Get all database connections
  getConnections: async (): Promise<DatabaseConnection[]> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<DatabaseConnection[]>> = await apiClient.get('/api/v1/database/connections');
        return response.data.data || [];
      },
      mockDatabaseConnections
    );
  },

  // Create new database connection
  createConnection: async (connection: Omit<DatabaseConnection, 'id' | 'status' | 'created_at' | 'last_used'>): Promise<DatabaseConnection> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<DatabaseConnection>> = await apiClient.post('/api/v1/database/connections', connection);
        return response.data.data!;
      },
      {
        ...connection,
        id: Date.now().toString(),
        status: 'connected' as const,
        created_at: new Date().toISOString(),
        last_used: new Date().toISOString(),
      }
    );
  },

  // Test database connection
  testConnection: async (connectionId: string): Promise<{ success: boolean; message: string }> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<{ success: boolean; message: string }>> = await apiClient.post(`/api/v1/database/connections/${connectionId}/test`);
        return response.data.data!;
      },
      { success: true, message: 'Connection test successful (mock)' }
    );
  },

  // Delete database connection
  deleteConnection: async (connectionId: string): Promise<void> => {
    return apiCallWithFallback(
      async () => {
        await apiClient.delete(`/api/v1/database/connections/${connectionId}`);
      },
      undefined
    );
  },

  // Get database schemas
  getSchemas: async (connectionId: string): Promise<Schema[]> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<Schema[]>> = await apiClient.get(`/api/v1/database/connections/${connectionId}/schemas`);
        return response.data.data || [];
      },
      [
        {
          name: 'public',
          tables: [
            { name: 'users', schema: 'public', type: 'table', row_count: 125000 },
            { name: 'products', schema: 'public', type: 'table', row_count: 50000 },
            { name: 'orders', schema: 'public', type: 'table', row_count: 75000 },
          ],
        },
      ]
    );
  },

  // Get tables in schema
  getTables: async (connectionId: string, schemaName: string): Promise<Table[]> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<Table[]>> = await apiClient.get(`/api/v1/database/connections/${connectionId}/schemas/${schemaName}/tables`);
        return response.data.data || [];
      },
      [
        { name: 'users', schema: 'public', type: 'table', row_count: 125000, size: '45 MB' },
        { name: 'products', schema: 'public', type: 'table', row_count: 50000, size: '25 MB' },
        { name: 'orders', schema: 'public', type: 'table', row_count: 75000, size: '18 MB' },
        { name: 'order_items', schema: 'public', type: 'table', row_count: 200000, size: '60 MB' },
        { name: 'categories', schema: 'public', type: 'table', row_count: 25, size: '2 KB' },
      ]
    );
  },
};

// Metadata API
export const metadataApi = {
  // Get all metadata
  getMetadata: async (params?: SearchParams): Promise<PaginatedResponse<TableMetadata>> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<PaginatedResponse<TableMetadata>>> = await apiClient.get('/api/v1/metadata', { params });
        return response.data.data!;
      },
      createPaginatedResponse(
        mockTableMetadata.filter(item => {
          if (params?.query) {
            const query = params.query.toLowerCase();
            return (
              item.table_name.toLowerCase().includes(query) ||
              item.database_name.toLowerCase().includes(query) ||
              item.description?.toLowerCase().includes(query)
            );
          }
          return true;
        }),
        params?.page || 1,
        params?.size || 10
      )
    );
  },

  // Get metadata by ID
  getMetadataById: async (id: string): Promise<TableMetadata> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<TableMetadata>> = await apiClient.get(`/api/v1/metadata/${id}`);
        return response.data.data!;
      },
      mockTableMetadata.find(item => item.id === id) || mockTableMetadata[0]
    );
  },

  // Generate metadata for table
  generateMetadata: async (params: {
    database_name: string;
    schema_name: string;
    table_name: string;
    sample_size?: number;
    num_samples?: number;
    use_llm?: boolean;
  }): Promise<Job> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<Job>> = await apiClient.post('/api/v1/metadata/generate', params);
        return response.data.data!;
      },
      {
        id: Date.now().toString(),
        type: 'metadata_generation',
        status: 'pending',
        progress: 0,
        message: `Generating metadata for ${params.table_name}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    );
  },

  // Update metadata
  updateMetadata: async (id: string, metadata: Partial<TableMetadata>): Promise<TableMetadata> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<TableMetadata>> = await apiClient.put(`/api/v1/metadata/${id}`, metadata);
        return response.data.data!;
      },
      {
        ...mockTableMetadata.find(item => item.id === id)!,
        ...metadata,
        updated_at: new Date().toISOString(),
      }
    );
  },

  // Delete metadata
  deleteMetadata: async (id: string): Promise<void> => {
    return apiCallWithFallback(
      async () => {
        await apiClient.delete(`/api/v1/metadata/${id}`);
      },
      undefined
    );
  },

  // Export metadata
  exportMetadata: async (id: string, format: 'json' | 'yaml'): Promise<Blob> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<Blob> = await apiClient.get(`/api/v1/metadata/${id}/export`, {
          params: { format },
          responseType: 'blob',
        });
        return response.data;
      },
      new Blob([JSON.stringify(mockTableMetadata.find(item => item.id === id), null, 2)], {
        type: format === 'json' ? 'application/json' : 'application/yaml',
      })
    );
  },
};

// LookML API
export const lookmlApi = {
  // Get all LookML models
  getModels: async (params?: SearchParams): Promise<PaginatedResponse<LookMLModel>> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<PaginatedResponse<LookMLModel>>> = await apiClient.get('/api/v1/lookml', { params });
        return response.data.data!;
      },
      createPaginatedResponse(mockLookMLModels, params?.page || 1, params?.size || 10)
    );
  },

  // Get LookML model by ID
  getModelById: async (id: string): Promise<LookMLModel> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<LookMLModel>> = await apiClient.get(`/api/v1/lookml/${id}`);
        return response.data.data!;
      },
      mockLookMLModels.find(item => item.id === id) || mockLookMLModels[0]
    );
  },

  // Generate LookML model
  generateModel: async (params: {
    database_name: string;
    schema_name: string;
    table_name: string;
    model_name?: string;
    include_derives?: boolean;
    include_explores?: boolean;
    additional_context?: string;
  }): Promise<Job> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<Job>> = await apiClient.post('/api/v1/lookml/generate', params);
        return response.data.data!;
      },
      {
        id: Date.now().toString(),
        type: 'lookml_generation',
        status: 'pending',
        progress: 0,
        message: `Generating LookML model for ${params.table_name}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
    );
  },

  // Update LookML model
  updateModel: async (id: string, model: Partial<LookMLModel>): Promise<LookMLModel> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<LookMLModel>> = await apiClient.put(`/api/v1/lookml/${id}`, model);
        return response.data.data!;
      },
      {
        ...mockLookMLModels.find(item => item.id === id)!,
        ...model,
        updated_at: new Date().toISOString(),
      }
    );
  },

  // Delete LookML model
  deleteModel: async (id: string): Promise<void> => {
    return apiCallWithFallback(
      async () => {
        await apiClient.delete(`/api/v1/lookml/${id}`);
      },
      undefined
    );
  },

  // Download LookML model
  downloadModel: async (id: string): Promise<Blob> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<Blob> = await apiClient.get(`/api/v1/lookml/${id}/download`, {
          responseType: 'blob',
        });
        return response.data;
      },
      new Blob([mockLookMLModels.find(item => item.id === id)?.lookml_content || ''], {
        type: 'text/plain',
      })
    );
  },
};

// Jobs API
export const jobsApi = {
  // Get all jobs
  getJobs: async (params?: SearchParams): Promise<PaginatedResponse<Job>> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<PaginatedResponse<Job>>> = await apiClient.get('/api/v1/jobs', { params });
        return response.data.data!;
      },
      createPaginatedResponse(mockJobs, params?.page || 1, params?.size || 10)
    );
  },

  // Get job by ID
  getJobById: async (id: string): Promise<Job> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<Job>> = await apiClient.get(`/api/v1/jobs/${id}`);
        return response.data.data!;
      },
      mockJobs.find(item => item.id === id) || mockJobs[0]
    );
  },

  // Cancel job
  cancelJob: async (id: string): Promise<void> => {
    return apiCallWithFallback(
      async () => {
        await apiClient.post(`/api/v1/jobs/${id}/cancel`);
      },
      undefined
    );
  },

  // Get job result
  getJobResult: async (id: string): Promise<any> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<any>> = await apiClient.get(`/api/v1/jobs/${id}/result`);
        return response.data.data;
      },
      mockJobs.find(item => item.id === id)?.result || {}
    );
  },
};

// Analytics API
export const analyticsApi = {
  // Get dashboard data
  getDashboard: async (): Promise<{
    total_databases: number;
    total_tables: number;
    total_metadata: number;
    total_lookml_models: number;
    recent_activity: any[];
    data_quality_summary: any;
  }> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<any>> = await apiClient.get('/api/v1/analytics/dashboard');
        return response.data.data!;
      },
      {
        total_databases: 8,
        total_tables: 156,
        total_metadata: 89,
        total_lookml_models: 42,
        recent_activity: [],
        data_quality_summary: {
          average_score: 87,
          excellent: 35,
          good: 25,
          fair: 20,
          poor: 10,
          not_rated: 10,
        },
      }
    );
  },

  // Get data quality metrics
  getDataQuality: async (): Promise<any> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<ApiResponse<any>> = await apiClient.get('/api/v1/analytics/data-quality');
        return response.data.data!;
      },
      {
        overall_score: 87,
        by_database: {},
        issues: [],
        recommendations: [],
      }
    );
  },
};

// Health check
export const healthApi = {
  check: async (): Promise<{ status: string; version: string }> => {
    return apiCallWithFallback(
      async () => {
        const response: AxiosResponse<{ status: string; version: string }> = await apiClient.get('/health');
        return response.data;
      },
      { status: 'ok', version: '1.0.0' }
    );
  },
};

export default {
  database: databaseApi,
  metadata: metadataApi,
  lookml: lookmlApi,
  jobs: jobsApi,
  analytics: analyticsApi,
  health: healthApi,
}; 