import React from 'react';
import Input from '../../../components/ui/Input';
import Icon from '../../../components/AppIcon';

const ConnectionDetailsForm = ({ 
  formData, 
  onChange, 
  errors, 
  databaseType 
}) => {
  const handleInputChange = (field, value) => {
    onChange(field, value);
  };

  const getPortPlaceholder = () => {
    if (!databaseType) return 'Port';
    switch (databaseType.id) {
      case 'postgresql': return '5432';
      case 'mysql': return '3306';
      case 'oracle': return '1521';
      case 'kinetica': return '9191';
      default: return 'Port';
    }
  };

  const shouldShowField = (field) => {
    if (!databaseType) return false;
    
    const hiddenFields = {
      'sqlite': ['host', 'port', 'username', 'password'],
      'bigquery': ['host', 'port', 'username', 'password'],
      'duckdb': ['host', 'port']
    };
    
    return !hiddenFields[databaseType.id]?.includes(field);
  };

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-text-primary flex items-center space-x-2">
          <Icon name="Settings" size={20} className="text-accent" />
          <span>Connection Details</span>
        </h3>
        
        {/* Connection Name */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Connection Name <span className="text-error">*</span>
          </label>
          <Input
            type="text"
            placeholder="Enter a descriptive name for this connection"
            value={formData.connectionName || ''}
            onChange={(e) => handleInputChange('connectionName', e.target.value)}
            className={errors.connectionName ? 'border-error' : ''}
          />
          {errors.connectionName && (
            <p className="text-sm text-error mt-1 flex items-center space-x-1">
              <Icon name="AlertCircle" size={16} />
              <span>{errors.connectionName}</span>
            </p>
          )}
        </div>

        {/* Database Name */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            {databaseType?.id === 'bigquery' ? 'Project ID' : 
             databaseType?.id === 'sqlite' ? 'Database File Path' :
             databaseType?.id === 'duckdb'? 'Database File Path' : 'Database Name'} <span className="text-error">*</span>
          </label>
          <Input
            type="text"
            placeholder={
              databaseType?.id === 'bigquery' ? 'your-project-id' :
              databaseType?.id === 'sqlite' ? '/path/to/database.db' :
              databaseType?.id === 'duckdb'? '/path/to/database.duckdb' : 'Database name'
            }
            value={formData.databaseName || ''}
            onChange={(e) => handleInputChange('databaseName', e.target.value)}
            className={errors.databaseName ? 'border-error' : ''}
          />
          {errors.databaseName && (
            <p className="text-sm text-error mt-1 flex items-center space-x-1">
              <Icon name="AlertCircle" size={16} />
              <span>{errors.databaseName}</span>
            </p>
          )}
        </div>

        {/* Predefined Schemas - Available for all database types */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Predefined Schemas/Datasets
          </label>
          <Input
            type="text"
            placeholder={
              databaseType?.id === 'bigquery' 
                ? "usa_names,census_bureau_usa,covid19_usafacts,baseball,stackoverflow"
                : databaseType?.id === 'postgresql'
                ? "public,analytics,reporting"
                : databaseType?.id === 'mysql'
                ? "app_db,analytics,logs"
                : "schema1,schema2,schema3"
            }
            value={formData.predefinedSchemas || ''}
            onChange={(e) => handleInputChange('predefinedSchemas', e.target.value)}
            className={errors.predefinedSchemas ? 'border-error' : ''}
          />
          <p className="text-sm text-text-secondary mt-1">
            Comma-separated list of specific schemas to display. When configured, only these schemas will be shown instead of auto-discovery. Leave empty to use auto-discovery.
          </p>
          {errors.predefinedSchemas && (
            <p className="text-sm text-error mt-1 flex items-center space-x-1">
              <Icon name="AlertCircle" size={16} />
              <span>{errors.predefinedSchemas}</span>
            </p>
          )}
        </div>

        {/* Host */}
        {shouldShowField('host') && (
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Host <span className="text-error">*</span>
            </label>
            <Input
              type="text"
              placeholder="localhost or IP address"
              value={formData.host || ''}
              onChange={(e) => handleInputChange('host', e.target.value)}
              className={errors.host ? 'border-error' : ''}
            />
            {errors.host && (
              <p className="text-sm text-error mt-1 flex items-center space-x-1">
                <Icon name="AlertCircle" size={16} />
                <span>{errors.host}</span>
              </p>
            )}
          </div>
        )}

        {/* Port */}
        {shouldShowField('port') && (
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Port
            </label>
            <Input
              type="number"
              placeholder={getPortPlaceholder()}
              value={formData.port || ''}
              onChange={(e) => handleInputChange('port', e.target.value)}
              className={errors.port ? 'border-error' : ''}
            />
            {errors.port && (
              <p className="text-sm text-error mt-1 flex items-center space-x-1">
                <Icon name="AlertCircle" size={16} />
                <span>{errors.port}</span>
              </p>
            )}
          </div>
        )}

        {/* Schema (for some databases) */}
        {(databaseType?.id === 'postgresql' || databaseType?.id === 'oracle') && (
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Default Schema
            </label>
            <Input
              type="text"
              placeholder={databaseType.id === 'postgresql' ? 'public' : 'schema_name'}
              value={formData.schema || ''}
              onChange={(e) => handleInputChange('schema', e.target.value)}
            />
            <p className="text-xs text-text-muted mt-1">
              Optional: Specify a default schema to use for this connection
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConnectionDetailsForm;