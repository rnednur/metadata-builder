import React, { useState, useEffect } from 'react';
import Icon from './AppIcon';
import SchemaFilterConfig from './SchemaFilterConfig';
import { databaseAPI } from '../services/api';

const SchemaFilterModal = ({ 
  isOpen, 
  onClose, 
  connectionName 
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [predefinedSchemas, setPredefinedSchemas] = useState({});
  const [availableSchemas, setAvailableSchemas] = useState([]);

  useEffect(() => {
    if (isOpen && connectionName) {
      loadSchemaConfiguration();
    }
  }, [isOpen, connectionName]);

  const loadSchemaConfiguration = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load both predefined schemas and available schemas
      const [predefinedResponse, availableResponse] = await Promise.all([
        databaseAPI.getPredefinedSchemas(connectionName),
        databaseAPI.getSchemas(connectionName)
      ]);

      setPredefinedSchemas(predefinedResponse.data.predefined_schemas || {});
      setAvailableSchemas(predefinedResponse.data.available_schemas || []);
      
    } catch (err) {
      console.error('Error loading schema configuration:', err);
      setError('Failed to load schema configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (newPredefinedSchemas) => {
    setLoading(true);
    setError(null);
    
    try {
      await databaseAPI.updatePredefinedSchemas(connectionName, newPredefinedSchemas);
      setPredefinedSchemas(newPredefinedSchemas);
      onClose(true); // Pass true to indicate changes were saved
    } catch (err) {
      console.error('Error saving schema configuration:', err);
      setError('Failed to save schema configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    onClose(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">
              Schema Filtering Configuration
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Configure schema and table filtering for {connectionName}
            </p>
          </div>
          <button
            onClick={() => onClose(false)}
            className="text-text-muted hover:text-text-primary"
            disabled={loading}
          >
            <Icon name="X" size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-8rem)]">
          {loading && (
            <div className="flex items-center justify-center p-12">
              <div className="flex items-center space-x-3">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
                <span className="text-text-muted">Loading schema configuration...</span>
              </div>
            </div>
          )}

          {error && (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <Icon name="AlertCircle" size={16} className="text-red-500" />
                  <span className="text-red-700 font-medium">Error</span>
                </div>
                <p className="text-red-600 mt-1">{error}</p>
                <button
                  onClick={loadSchemaConfiguration}
                  className="mt-3 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          {!loading && !error && (
            <div className="p-6">
              <SchemaFilterConfig
                connectionName={connectionName}
                initialConfig={predefinedSchemas}
                availableSchemas={availableSchemas}
                onSave={handleSave}
                onCancel={handleCancel}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchemaFilterModal;