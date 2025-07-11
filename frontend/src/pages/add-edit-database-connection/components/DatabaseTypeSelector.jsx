import React from 'react';
import Icon from '../../../components/AppIcon';

const DatabaseTypeSelector = ({ value, onChange, error }) => {
  const databaseTypes = [
    {
      id: 'postgresql',
      name: 'PostgreSQL',
      icon: 'Database',
      description: 'Open source relational database',
      defaultPort: 5432
    },
    {
      id: 'mysql',
      name: 'MySQL',
      icon: 'Database',
      description: 'Popular open source database',
      defaultPort: 3306
    },
    {
      id: 'sqlite',
      name: 'SQLite',
      icon: 'HardDrive',
      description: 'Lightweight file-based database',
      defaultPort: null
    },
    {
      id: 'oracle',
      name: 'Oracle',
      icon: 'Server',
      description: 'Enterprise database system',
      defaultPort: 1521
    },
    {
      id: 'bigquery',
      name: 'BigQuery',
      icon: 'Cloud',
      description: 'Google Cloud data warehouse',
      defaultPort: null
    },
    {
      id: 'kinetica',
      name: 'Kinetica',
      icon: 'Zap',
      description: 'GPU-accelerated analytics',
      defaultPort: 9191
    },
    {
      id: 'duckdb',
      name: 'DuckDB',
      icon: 'Database',
      description: 'In-process analytical database',
      defaultPort: null
    }
  ];

  const handleTypeSelect = (type) => {
    onChange(type);
  };

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-text-primary">
        Database Type <span className="text-error">*</span>
      </label>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {databaseTypes.map((type) => (
          <button
            key={type.id}
            type="button"
            onClick={() => handleTypeSelect(type)}
            className={`p-4 border-2 rounded-lg text-left transition-all duration-150 hover:border-accent hover:shadow-md ${
              value?.id === type.id
                ? 'border-accent bg-accent-50 shadow-md'
                : 'border-border bg-surface hover:bg-surface-secondary'
            }`}
          >
            <div className="flex items-start space-x-3">
              <div className={`p-2 rounded-lg ${
                value?.id === type.id
                  ? 'bg-accent text-accent-foreground'
                  : 'bg-secondary-100 text-secondary-600'
              }`}>
                <Icon name={type.icon} size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className={`font-medium text-sm ${
                  value?.id === type.id ? 'text-accent-700' : 'text-text-primary'
                }`}>
                  {type.name}
                </h3>
                <p className="text-xs text-text-muted mt-1 line-clamp-2">
                  {type.description}
                </p>
                {type.defaultPort && (
                  <p className="text-xs text-text-secondary mt-1">
                    Default port: {type.defaultPort}
                  </p>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
      
      {error && (
        <p className="text-sm text-error flex items-center space-x-1">
          <Icon name="AlertCircle" size={16} />
          <span>{error}</span>
        </p>
      )}
    </div>
  );
};

export default DatabaseTypeSelector;