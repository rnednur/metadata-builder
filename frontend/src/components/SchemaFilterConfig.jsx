import React, { useState, useEffect } from 'react';
import Icon from './AppIcon';
import Input from './ui/Input';

const SchemaFilterConfig = ({ 
  connectionName, 
  onSave, 
  onCancel, 
  initialConfig = null,
  availableSchemas = []
}) => {
  const [predefinedSchemas, setPredefinedSchemas] = useState(initialConfig || {});
  const [selectedSchema, setSelectedSchema] = useState('');
  const [showAddSchema, setShowAddSchema] = useState(false);

  // Initialize with available schemas if no predefined config exists
  useEffect(() => {
    if (!initialConfig && availableSchemas.length > 0) {
      const newConfig = {};
      availableSchemas.forEach(schema => {
        newConfig[schema] = {
          enabled: true,
          tables: [],
          excluded_tables: [],
          table_patterns: [],
          excluded_patterns: [],
          description: ''
        };
      });
      setPredefinedSchemas(newConfig);
    }
  }, [initialConfig, availableSchemas]);

  const handleSchemaConfigChange = (schemaName, field, value) => {
    setPredefinedSchemas(prev => ({
      ...prev,
      [schemaName]: {
        ...prev[schemaName],
        [field]: value
      }
    }));
  };

  const handleArrayFieldChange = (schemaName, field, index, value) => {
    const currentArray = predefinedSchemas[schemaName]?.[field] || [];
    const newArray = [...currentArray];
    
    if (value === '') {
      // Remove empty entries
      newArray.splice(index, 1);
    } else {
      newArray[index] = value;
    }
    
    handleSchemaConfigChange(schemaName, field, newArray);
  };

  const addArrayItem = (schemaName, field) => {
    const currentArray = predefinedSchemas[schemaName]?.[field] || [];
    handleSchemaConfigChange(schemaName, field, [...currentArray, '']);
  };

  const addNewSchema = () => {
    if (selectedSchema && !predefinedSchemas[selectedSchema]) {
      setPredefinedSchemas(prev => ({
        ...prev,
        [selectedSchema]: {
          enabled: true,
          tables: [],
          excluded_tables: [],
          table_patterns: [],
          excluded_patterns: [],
          description: ''
        }
      }));
      setSelectedSchema('');
      setShowAddSchema(false);
    }
  };

  const removeSchema = (schemaName) => {
    setPredefinedSchemas(prev => {
      const newConfig = { ...prev };
      delete newConfig[schemaName];
      return newConfig;
    });
  };

  const renderArrayField = (schemaName, field, label, placeholder) => {
    const array = predefinedSchemas[schemaName]?.[field] || [];
    
    return (
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium text-text-primary">{label}</label>
          <button
            onClick={() => addArrayItem(schemaName, field)}
            className="text-xs text-accent hover:text-accent-hover flex items-center space-x-1"
          >
            <Icon name="Plus" size={12} />
            <span>Add</span>
          </button>
        </div>
        <div className="space-y-1">
          {array.map((item, index) => (
            <div key={index} className="flex items-center space-x-2">
              <Input
                value={item}
                onChange={(e) => handleArrayFieldChange(schemaName, field, index, e.target.value)}
                placeholder={placeholder}
                className="flex-1 text-xs"
              />
              <button
                onClick={() => handleArrayFieldChange(schemaName, field, index, '')}
                className="text-red-500 hover:text-red-700"
              >
                <Icon name="X" size={14} />
              </button>
            </div>
          ))}
          {array.length === 0 && (
            <div className="text-xs text-text-muted italic">No {label.toLowerCase()} configured</div>
          )}
        </div>
      </div>
    );
  };

  const renderSchemaConfig = (schemaName, config) => {
    return (
      <div key={schemaName} className="border border-border rounded-lg p-4 space-y-4">
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={config.enabled}
              onChange={(e) => handleSchemaConfigChange(schemaName, 'enabled', e.target.checked)}
              className="rounded"
            />
            <div>
              <h3 className="font-medium text-text-primary">{schemaName}</h3>
              <p className="text-xs text-text-muted">
                {config.enabled ? 'Enabled for metadata generation' : 'Disabled'}
              </p>
            </div>
          </div>
          <button
            onClick={() => removeSchema(schemaName)}
            className="text-red-500 hover:text-red-700"
          >
            <Icon name="Trash2" size={16} />
          </button>
        </div>

        {config.enabled && (
          <div className="space-y-4 pl-6">
            {/* Description */}
            <div>
              <label className="text-sm font-medium text-text-primary">Description</label>
              <Input
                value={config.description || ''}
                onChange={(e) => handleSchemaConfigChange(schemaName, 'description', e.target.value)}
                placeholder="Optional description for this schema"
                className="mt-1"
              />
            </div>

            {/* Specific Tables */}
            {renderArrayField(schemaName, 'tables', 'Specific Tables', 'table_name')}

            {/* Table Patterns */}
            {renderArrayField(schemaName, 'table_patterns', 'Include Patterns (Regex)', 'user_.*')}

            {/* Excluded Tables */}
            {renderArrayField(schemaName, 'excluded_tables', 'Excluded Tables', 'temp_table')}

            {/* Excluded Patterns */}
            {renderArrayField(schemaName, 'excluded_patterns', 'Exclude Patterns (Regex)', '.*_temp')}

            {/* Help Text */}
            <div className="text-xs text-text-muted bg-secondary/10 p-3 rounded">
              <p className="font-medium mb-1">Filtering Logic:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>If specific tables are listed, only include those</li>
                <li>Apply include patterns (regex) for dynamic matching</li>
                <li>Remove tables from excluded tables list</li>
                <li>Remove tables matching exclude patterns</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    );
  };

  const availableToAdd = availableSchemas.filter(schema => !predefinedSchemas[schema]);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold text-text-primary">
            Schema Filtering Configuration
          </h2>
          <p className="text-sm text-text-muted">
            Configure which schemas and tables to include in metadata generation for {connectionName}
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={onCancel}
            className="px-3 py-1.5 text-sm border border-border rounded hover:bg-secondary/10"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(predefinedSchemas)}
            className="px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent-hover"
          >
            Save Configuration
          </button>
        </div>
      </div>

      {/* Add New Schema */}
      {availableToAdd.length > 0 && (
        <div className="border border-dashed border-border rounded-lg p-4">
          {!showAddSchema ? (
            <button
              onClick={() => setShowAddSchema(true)}
              className="text-accent hover:text-accent-hover flex items-center space-x-2"
            >
              <Icon name="Plus" size={16} />
              <span>Add Schema</span>
            </button>
          ) : (
            <div className="flex items-center space-x-3">
              <select
                value={selectedSchema}
                onChange={(e) => setSelectedSchema(e.target.value)}
                className="px-3 py-1.5 border border-border rounded text-sm"
              >
                <option value="">Select a schema...</option>
                {availableToAdd.map(schema => (
                  <option key={schema} value={schema}>{schema}</option>
                ))}
              </select>
              <button
                onClick={addNewSchema}
                disabled={!selectedSchema}
                className="px-3 py-1.5 text-sm bg-accent text-white rounded hover:bg-accent-hover disabled:opacity-50"
              >
                Add
              </button>
              <button
                onClick={() => {
                  setShowAddSchema(false);
                  setSelectedSchema('');
                }}
                className="text-text-muted hover:text-text-primary"
              >
                <Icon name="X" size={16} />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Schema Configurations */}
      <div className="space-y-4">
        {Object.entries(predefinedSchemas).map(([schemaName, config]) =>
          renderSchemaConfig(schemaName, config)
        )}
      </div>

      {Object.keys(predefinedSchemas).length === 0 && (
        <div className="text-center py-12 text-text-muted">
          <Icon name="Database" size={48} className="mx-auto mb-4 opacity-50" />
          <p>No schemas configured. Add schemas to enable filtering.</p>
        </div>
      )}

      {/* Configuration Summary */}
      {Object.keys(predefinedSchemas).length > 0 && (
        <div className="bg-secondary/10 p-4 rounded-lg">
          <h3 className="font-medium text-text-primary mb-2">Configuration Summary</h3>
          <div className="text-sm text-text-muted space-y-1">
            <p>
              <strong>{Object.keys(predefinedSchemas).length}</strong> schemas configured
            </p>
            <p>
              <strong>{Object.values(predefinedSchemas).filter(c => c.enabled).length}</strong> schemas enabled
            </p>
            <p>
              <strong>{Object.values(predefinedSchemas).filter(c => c.enabled && c.tables.length > 0).length}</strong> schemas with specific table lists
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchemaFilterConfig;