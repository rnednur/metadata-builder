import type { TableMetadata, DatabaseConnection, LookMLModel, Job } from '../types';

// Mock database connections
export const mockDatabaseConnections: DatabaseConnection[] = [
  {
    id: '1',
    name: 'Production PostgreSQL',
    type: 'postgresql',
    host: 'prod-postgres.company.com',
    port: 5432,
    username: 'app_user',
    database: 'ecommerce',
    status: 'connected',
    created_at: '2024-01-15T10:00:00Z',
    last_used: '2024-01-20T14:30:00Z',
  },
  {
    id: '2',
    name: 'Analytics BigQuery',
    type: 'bigquery',
    database: 'analytics-project',
    status: 'connected',
    created_at: '2024-01-16T09:00:00Z',
    last_used: '2024-01-20T13:45:00Z',
  },
  {
    id: '3',
    name: 'Development MySQL',
    type: 'mysql',
    host: 'dev-mysql.company.com',
    port: 3306,
    username: 'dev_user',
    database: 'dev_ecommerce',
    status: 'disconnected',
    created_at: '2024-01-17T11:00:00Z',
    last_used: '2024-01-19T16:20:00Z',
  },
];

// Mock table metadata
export const mockTableMetadata: TableMetadata[] = [
  {
    id: '1',
    table_name: 'users',
    schema_name: 'public',
    database_name: 'ecommerce',
    description: 'Customer user accounts and profile information. Contains personal details, authentication data, and account preferences.',
    business_context: 'Central customer entity used across all business processes. Critical for user analytics, marketing campaigns, and customer support.',
    data_quality_score: 92,
    columns: [
      {
        name: 'id',
        type: 'INTEGER',
        description: 'Unique identifier for each user account',
        business_name: 'User ID',
        data_classification: 'internal',
        nullable: false,
        primary_key: true,
        foreign_key: undefined,
        unique: true,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL', 'PRIMARY KEY'],
        statistics: {
          distinct_count: 125000,
          null_count: 0,
          min_value: 1,
          max_value: 125000,
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 100,
          consistency: 100,
        },
      },
      {
        name: 'email',
        type: 'VARCHAR(255)',
        description: 'User email address used for authentication and communication',
        business_name: 'Email Address',
        data_classification: 'confidential',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: true,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL', 'UNIQUE'],
        statistics: {
          distinct_count: 124850,
          null_count: 0,
        },
        quality_metrics: {
          completeness: 100,
          validity: 98.2,
          uniqueness: 99.9,
          consistency: 95.5,
          issues: ['150 duplicate emails found', 'Some invalid email formats'],
        },
      },
      {
        name: 'first_name',
        type: 'VARCHAR(100)',
        description: 'User first name for personalization',
        business_name: 'First Name',
        data_classification: 'confidential',
        nullable: true,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: false,
        default_value: undefined,
        constraints: [],
        statistics: {
          distinct_count: 8500,
          null_count: 250,
        },
        quality_metrics: {
          completeness: 99.8,
          validity: 95.0,
          uniqueness: 6.8,
          consistency: 90.0,
        },
      },
      {
        name: 'last_name',
        type: 'VARCHAR(100)',
        description: 'User last name for personalization',
        business_name: 'Last Name',
        data_classification: 'confidential',
        nullable: true,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: false,
        default_value: undefined,
        constraints: [],
        statistics: {
          distinct_count: 12000,
          null_count: 180,
        },
        quality_metrics: {
          completeness: 99.9,
          validity: 97.0,
          uniqueness: 9.6,
          consistency: 92.0,
        },
      },
      {
        name: 'created_at',
        type: 'TIMESTAMP',
        description: 'When the user account was created',
        business_name: 'Account Creation Date',
        data_classification: 'internal',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: true,
        default_value: 'CURRENT_TIMESTAMP',
        constraints: ['NOT NULL'],
        statistics: {
          null_count: 0,
          min_value: '2020-01-01T00:00:00Z',
          max_value: '2024-01-20T23:59:59Z',
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 85.0,
          consistency: 100,
        },
      },
    ],
    relationships: [
      {
        type: 'one-to-many',
        target_table: 'orders',
        target_column: 'user_id',
        source_column: 'id',
        description: 'User can have multiple orders',
      },
      {
        type: 'one-to-many',
        target_table: 'user_preferences',
        target_column: 'user_id',
        source_column: 'id',
        description: 'User can have multiple preferences',
      },
    ],
    constraints: [
      {
        name: 'users_pkey',
        type: 'primary_key',
        columns: ['id'],
      },
      {
        name: 'users_email_unique',
        type: 'unique',
        columns: ['email'],
      },
    ],
    statistics: {
      row_count: 125000,
      size_bytes: 45000000,
      last_analyzed: '2024-01-20T10:00:00Z',
      data_freshness: '< 1 hour',
      growth_rate: 150,
    },
    created_at: '2024-01-18T10:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
    generated_by: 'llm',
  },
  {
    id: '2',
    table_name: 'products',
    schema_name: 'public',
    database_name: 'ecommerce',
    description: 'Product catalog with item details, pricing, and inventory information.',
    business_context: 'Core product data driving e-commerce operations, used for catalog display, inventory management, and sales analytics.',
    data_quality_score: 78,
    columns: [
      {
        name: 'id',
        type: 'INTEGER',
        description: 'Unique product identifier',
        business_name: 'Product ID',
        data_classification: 'public',
        nullable: false,
        primary_key: true,
        foreign_key: undefined,
        unique: true,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL', 'PRIMARY KEY'],
        statistics: {
          distinct_count: 50000,
          null_count: 0,
          min_value: 1,
          max_value: 50000,
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 100,
          consistency: 100,
        },
      },
      {
        name: 'name',
        type: 'VARCHAR(200)',
        description: 'Product name/title',
        business_name: 'Product Name',
        data_classification: 'public',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL'],
        statistics: {
          distinct_count: 49800,
          null_count: 0,
        },
        quality_metrics: {
          completeness: 100,
          validity: 85.0,
          uniqueness: 99.6,
          consistency: 75.0,
          issues: ['Some products have inconsistent naming conventions'],
        },
      },
      {
        name: 'price',
        type: 'DECIMAL(10,2)',
        description: 'Product price in USD',
        business_name: 'Price',
        data_classification: 'public',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: false,
        default_value: undefined,
        constraints: ['NOT NULL', 'CHECK (price > 0)'],
        statistics: {
          null_count: 0,
          min_value: 0.99,
          max_value: 2999.99,
          avg_value: 124.50,
          median_value: 49.99,
          std_deviation: 245.30,
        },
        quality_metrics: {
          completeness: 100,
          validity: 98.5,
          uniqueness: 75.0,
          consistency: 90.0,
        },
      },
      {
        name: 'category_id',
        type: 'INTEGER',
        description: 'Reference to product category',
        business_name: 'Category',
        data_classification: 'public',
        nullable: true,
        primary_key: false,
        foreign_key: 'categories.id',
        unique: false,
        indexed: true,
        default_value: undefined,
        constraints: ['FOREIGN KEY'],
        statistics: {
          distinct_count: 25,
          null_count: 500,
        },
        quality_metrics: {
          completeness: 99.0,
          validity: 100,
          uniqueness: 0.05,
          consistency: 100,
        },
      },
    ],
    relationships: [
      {
        type: 'many-to-one',
        target_table: 'categories',
        target_column: 'id',
        source_column: 'category_id',
        description: 'Product belongs to a category',
      },
      {
        type: 'one-to-many',
        target_table: 'order_items',
        target_column: 'product_id',
        source_column: 'id',
        description: 'Product can appear in multiple order items',
      },
    ],
    constraints: [
      {
        name: 'products_pkey',
        type: 'primary_key',
        columns: ['id'],
      },
      {
        name: 'products_category_fkey',
        type: 'foreign_key',
        columns: ['category_id'],
        reference_table: 'categories',
        reference_columns: ['id'],
      },
      {
        name: 'products_price_check',
        type: 'check',
        columns: ['price'],
        definition: 'price > 0',
      },
    ],
    statistics: {
      row_count: 50000,
      size_bytes: 25000000,
      last_analyzed: '2024-01-19T15:00:00Z',
      data_freshness: '< 12 hours',
      growth_rate: 50,
    },
    created_at: '2024-01-17T09:00:00Z',
    updated_at: '2024-01-19T16:45:00Z',
    generated_by: 'hybrid',
  },
  {
    id: '3',
    table_name: 'orders',
    schema_name: 'public',
    database_name: 'ecommerce',
    description: 'Customer order records including status, dates, and totals.',
    business_context: 'Critical business transaction data used for revenue tracking, fulfillment, and customer service.',
    data_quality_score: 85,
    columns: [
      {
        name: 'id',
        type: 'INTEGER',
        description: 'Unique order identifier',
        business_name: 'Order ID',
        data_classification: 'internal',
        nullable: false,
        primary_key: true,
        foreign_key: undefined,
        unique: true,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL', 'PRIMARY KEY'],
        statistics: {
          distinct_count: 75000,
          null_count: 0,
          min_value: 1,
          max_value: 75000,
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 100,
          consistency: 100,
        },
      },
      {
        name: 'user_id',
        type: 'INTEGER',
        description: 'Reference to the customer who placed the order',
        business_name: 'Customer ID',
        data_classification: 'internal',
        nullable: false,
        primary_key: false,
        foreign_key: 'users.id',
        unique: false,
        indexed: true,
        default_value: undefined,
        constraints: ['NOT NULL', 'FOREIGN KEY'],
        statistics: {
          distinct_count: 25000,
          null_count: 0,
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 33.3,
          consistency: 100,
        },
      },
      {
        name: 'status',
        type: 'VARCHAR(20)',
        description: 'Current order status',
        business_name: 'Order Status',
        data_classification: 'internal',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: true,
        default_value: 'pending',
        constraints: ['NOT NULL'],
        categorical_values: [
          { value: 'pending', count: 15000, percentage: 20.0, description: 'Order placed but not processed' },
          { value: 'processing', count: 7500, percentage: 10.0, description: 'Order being prepared' },
          { value: 'shipped', count: 22500, percentage: 30.0, description: 'Order shipped to customer' },
          { value: 'delivered', count: 26250, percentage: 35.0, description: 'Order delivered successfully' },
          { value: 'cancelled', count: 3750, percentage: 5.0, description: 'Order cancelled' },
        ],
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 0.007,
          consistency: 100,
        },
      },
      {
        name: 'total_amount',
        type: 'DECIMAL(12,2)',
        description: 'Total order amount including tax and shipping',
        business_name: 'Order Total',
        data_classification: 'internal',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: false,
        default_value: undefined,
        constraints: ['NOT NULL', 'CHECK (total_amount >= 0)'],
        statistics: {
          null_count: 0,
          min_value: 5.99,
          max_value: 5999.99,
          avg_value: 185.75,
          median_value: 89.99,
          std_deviation: 425.60,
        },
        quality_metrics: {
          completeness: 100,
          validity: 99.8,
          uniqueness: 95.0,
          consistency: 98.0,
        },
      },
      {
        name: 'created_at',
        type: 'TIMESTAMP',
        description: 'When the order was placed',
        business_name: 'Order Date',
        data_classification: 'internal',
        nullable: false,
        primary_key: false,
        foreign_key: undefined,
        unique: false,
        indexed: true,
        default_value: 'CURRENT_TIMESTAMP',
        constraints: ['NOT NULL'],
        statistics: {
          null_count: 0,
          min_value: '2023-01-01T00:00:00Z',
          max_value: '2024-01-20T23:59:59Z',
        },
        quality_metrics: {
          completeness: 100,
          validity: 100,
          uniqueness: 98.5,
          consistency: 100,
        },
      },
    ],
    relationships: [
      {
        type: 'many-to-one',
        target_table: 'users',
        target_column: 'id',
        source_column: 'user_id',
        description: 'Order belongs to a user',
      },
      {
        type: 'one-to-many',
        target_table: 'order_items',
        target_column: 'order_id',
        source_column: 'id',
        description: 'Order contains multiple items',
      },
    ],
    constraints: [
      {
        name: 'orders_pkey',
        type: 'primary_key',
        columns: ['id'],
      },
      {
        name: 'orders_user_fkey',
        type: 'foreign_key',
        columns: ['user_id'],
        reference_table: 'users',
        reference_columns: ['id'],
      },
      {
        name: 'orders_total_check',
        type: 'check',
        columns: ['total_amount'],
        definition: 'total_amount >= 0',
      },
    ],
    statistics: {
      row_count: 75000,
      size_bytes: 18000000,
      last_analyzed: '2024-01-20T08:00:00Z',
      data_freshness: '< 2 hours',
      growth_rate: 200,
    },
    created_at: '2024-01-16T14:00:00Z',
    updated_at: '2024-01-20T12:15:00Z',
    generated_by: 'llm',
  },
];

// Mock LookML models
export const mockLookMLModels: LookMLModel[] = [
  {
    id: '1',
    name: 'users_model',
    table_name: 'users',
    schema_name: 'public',
    database_name: 'ecommerce',
    lookml_content: `view: users {
  sql_table_name: public.users ;;
  
  dimension: id {
    primary_key: yes
    type: number
    sql: \${TABLE}.id ;;
  }
  
  dimension: email {
    type: string
    sql: \${TABLE}.email ;;
  }
  
  dimension: first_name {
    type: string
    sql: \${TABLE}.first_name ;;
  }
  
  dimension: last_name {
    type: string
    sql: \${TABLE}.last_name ;;
  }
  
  dimension_group: created {
    type: time
    timeframes: [raw, time, date, week, month, quarter, year]
    sql: \${TABLE}.created_at ;;
  }
  
  measure: count {
    type: count
    drill_fields: [id, first_name, last_name, email]
  }
}`,
    model_type: 'view',
    created_at: '2024-01-18T11:00:00Z',
    updated_at: '2024-01-18T11:00:00Z',
  },
  {
    id: '2',
    name: 'products_model',
    table_name: 'products',
    schema_name: 'public',
    database_name: 'ecommerce',
    lookml_content: `view: products {
  sql_table_name: public.products ;;
  
  dimension: id {
    primary_key: yes
    type: number
    sql: \${TABLE}.id ;;
  }
  
  dimension: name {
    type: string
    sql: \${TABLE}.name ;;
  }
  
  dimension: price {
    type: number
    value_format_name: usd
    sql: \${TABLE}.price ;;
  }
  
  dimension: category_id {
    type: number
    sql: \${TABLE}.category_id ;;
  }
  
  measure: count {
    type: count
    drill_fields: [id, name, price]
  }
  
  measure: average_price {
    type: average
    sql: \${price} ;;
    value_format_name: usd
  }
}`,
    model_type: 'view',
    created_at: '2024-01-17T10:00:00Z',
    updated_at: '2024-01-17T10:00:00Z',
  },
];

// Mock jobs
export const mockJobs: Job[] = [
  {
    id: '1',
    type: 'metadata_generation',
    status: 'completed',
    progress: 100,
    message: 'Metadata generation completed successfully',
    result: { metadata_id: '1' },
    created_at: '2024-01-20T14:00:00Z',
    updated_at: '2024-01-20T14:30:00Z',
  },
  {
    id: '2',
    type: 'lookml_generation',
    status: 'running',
    progress: 65,
    message: 'Generating LookML model for products table',
    created_at: '2024-01-20T15:00:00Z',
    updated_at: '2024-01-20T15:15:00Z',
    estimated_completion: '2024-01-20T15:25:00Z',
  },
  {
    id: '3',
    type: 'metadata_generation',
    status: 'failed',
    progress: 0,
    message: 'Failed to connect to database',
    created_at: '2024-01-20T13:00:00Z',
    updated_at: '2024-01-20T13:05:00Z',
  },
];

// Helper function to create paginated response
export function createPaginatedResponse<T>(
  items: T[],
  page: number = 1,
  size: number = 10
) {
  const startIndex = (page - 1) * size;
  const endIndex = startIndex + size;
  const paginatedItems = items.slice(startIndex, endIndex);
  
  return {
    items: paginatedItems,
    total: items.length,
    page,
    size,
    pages: Math.ceil(items.length / size),
  };
} 