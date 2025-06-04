// Database types
export interface DatabaseConnection {
  id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'sqlite' | 'oracle' | 'bigquery' | 'kinetica' | 'duckdb';
  host?: string;
  port?: number;
  username?: string;
  database?: string;
  schema?: string;
  status: 'connected' | 'disconnected' | 'error';
  created_at: string;
  last_used: string;
}

// Schema and table types
export interface Schema {
  name: string;
  tables: Table[];
}

export interface Table {
  name: string;
  schema: string;
  type: 'table' | 'view';
  row_count?: number;
  size?: string;
  last_modified?: string;
  columns?: Column[];
}

export interface Column {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
  default_value?: string;
  description?: string;
}

// Metadata types
export interface TableMetadata {
  id: string;
  table_name: string;
  schema_name: string;
  database_name: string;
  description?: string;
  business_context?: string;
  data_quality_score?: number;
  columns: ColumnMetadata[];
  relationships?: Relationship[];
  constraints?: Constraint[];
  statistics?: TableStatistics;
  created_at: string;
  updated_at: string;
  generated_by: 'manual' | 'llm' | 'hybrid';
}

export interface ColumnMetadata {
  name: string;
  type: string;
  description?: string;
  business_name?: string;
  data_classification?: 'public' | 'internal' | 'confidential' | 'restricted';
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
  unique: boolean;
  indexed: boolean;
  default_value?: string;
  constraints?: string[];
  statistics?: ColumnStatistics;
  categorical_values?: CategoricalValue[];
  quality_metrics?: QualityMetrics;
}

export interface Relationship {
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
  target_table: string;
  target_column: string;
  source_column: string;
  description?: string;
}

export interface Constraint {
  name: string;
  type: 'primary_key' | 'foreign_key' | 'unique' | 'check' | 'not_null';
  columns: string[];
  reference_table?: string;
  reference_columns?: string[];
  definition?: string;
}

export interface TableStatistics {
  row_count: number;
  size_bytes: number;
  last_analyzed: string;
  data_freshness?: string;
  growth_rate?: number;
}

export interface ColumnStatistics {
  distinct_count?: number;
  null_count?: number;
  min_value?: string | number;
  max_value?: string | number;
  avg_value?: number;
  median_value?: number;
  std_deviation?: number;
  percentiles?: Record<string, number>;
}

export interface CategoricalValue {
  value: string;
  count: number;
  percentage: number;
  description?: string;
}

export interface QualityMetrics {
  completeness: number;
  validity: number;
  uniqueness: number;
  consistency: number;
  accuracy?: number;
  issues?: string[];
}

// LookML types
export interface LookMLModel {
  id: string;
  name: string;
  table_name: string;
  schema_name: string;
  database_name: string;
  lookml_content: string;
  model_type: 'view' | 'explore' | 'dashboard';
  created_at: string;
  updated_at: string;
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Job and progress types
export interface Job {
  id: string;
  type: 'metadata_generation' | 'lookml_generation' | 'data_analysis';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: any;
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
}

// Filter and search types
export interface MetadataFilter {
  database?: string[];
  schema?: string[];
  table_type?: ('table' | 'view')[];
  data_quality_min?: number;
  has_description?: boolean;
  generated_by?: ('manual' | 'llm' | 'hybrid')[];
  created_after?: string;
  created_before?: string;
}

export interface SearchParams {
  query?: string;
  filters?: MetadataFilter;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  page?: number;
  size?: number;
} 