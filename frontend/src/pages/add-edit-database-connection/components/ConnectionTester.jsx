import React, { useState } from 'react';
import Button from '../../../components/ui/Button';
import Icon from '../../../components/AppIcon';

const ConnectionTester = ({ formData, databaseType, onTestComplete }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [responseTime, setResponseTime] = useState(null);

  const handleTestConnection = async () => {
    if (!databaseType) {
      setTestResult({
        success: false,
        message: 'Please select a database type first'
      });
      return;
    }

    setIsLoading(true);
    setTestResult(null);
    setResponseTime(null);

    const startTime = Date.now();

    try {
      // Simulate connection test with mock data
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      setResponseTime(duration);

      // Mock validation logic
      const isValid = validateConnectionData();
      
      if (isValid) {
        const result = {
          success: true,
          message: 'Connection successful! Database is reachable and credentials are valid.',
          details: {
            serverVersion: getServerVersionMock(),
            responseTime: duration,
            features: getFeaturesMock()
          }
        };
        setTestResult(result);
        onTestComplete?.(result);
      } else {
        const result = {
          success: false,
          message: 'Connection failed. Please check your credentials and network connectivity.',
          error: 'Authentication failed or database unreachable'
        };
        setTestResult(result);
        onTestComplete?.(result);
      }
    } catch (error) {
      const result = {
        success: false,
        message: 'Connection test failed due to network error.',
        error: error.message
      };
      setTestResult(result);
      onTestComplete?.(result);
    } finally {
      setIsLoading(false);
    }
  };

  const validateConnectionData = () => {
    // Mock validation - in real app this would be more sophisticated
    const requiredFields = getRequiredFields();
    return requiredFields.every(field => formData[field]);
  };

  const getRequiredFields = () => {
    switch (databaseType?.id) {
      case 'sqlite': case'duckdb':
        return ['connectionName', 'databaseName'];
      case 'bigquery':
        return ['connectionName', 'databaseName', 'serviceAccountKey'];
      default:
        return ['connectionName', 'databaseName', 'host', 'username', 'password'];
    }
  };

  const getServerVersionMock = () => {
    const versions = {
      'postgresql': 'PostgreSQL 15.4',
      'mysql': 'MySQL 8.0.35',
      'sqlite': 'SQLite 3.43.0',
      'oracle': 'Oracle Database 19c',
      'bigquery': 'BigQuery Standard SQL',
      'kinetica': 'Kinetica 7.1.8',
      'duckdb': 'DuckDB 0.9.1'
    };
    return versions[databaseType?.id] || 'Unknown';
  };

  const getFeaturesMock = () => {
    const features = {
      'postgresql': ['Transactions', 'JSON Support', 'Full Text Search'],
      'mysql': ['Transactions', 'Replication', 'Partitioning'],
      'sqlite': ['Lightweight', 'Embedded', 'ACID Compliant'],
      'oracle': ['Enterprise Features', 'Advanced Analytics', 'High Availability'],
      'bigquery': ['Serverless', 'Machine Learning', 'Real-time Analytics'],
      'kinetica': ['GPU Acceleration', 'Real-time Analytics', 'Geospatial'],
      'duckdb': ['Analytical Queries', 'Columnar Storage', 'In-Process']
    };
    return features[databaseType?.id] || [];
  };

  const canTest = () => {
    if (!databaseType) return false;
    const requiredFields = getRequiredFields();
    return requiredFields.every(field => formData[field]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-text-primary flex items-center space-x-2">
          <Icon name="Zap" size={20} className="text-accent" />
          <span>Connection Test</span>
        </h3>
        
        <Button
          variant="primary"
          onClick={handleTestConnection}
          disabled={!canTest() || isLoading}
          loading={isLoading}
          iconName="Play"
          iconPosition="left"
        >
          {isLoading ? 'Testing...' : 'Test Connection'}
        </Button>
      </div>

      {!canTest() && !isLoading && (
        <div className="p-4 bg-warning-50 border border-warning-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Icon name="AlertTriangle" size={20} className="text-warning-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-warning-800">Required Fields Missing</h4>
              <p className="text-sm text-warning-700 mt-1">
                Please fill in all required fields before testing the connection.
              </p>
              <ul className="text-sm text-warning-700 mt-2 list-disc list-inside">
                {getRequiredFields().filter(field => !formData[field]).map(field => (
                  <li key={field}>
                    {field.charAt(0).toUpperCase() + field.slice(1).replace(/([A-Z])/g, ' $1')}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {testResult && (
        <div className={`p-4 border rounded-lg ${
          testResult.success 
            ? 'bg-success-50 border-success-200' :'bg-error-50 border-error-200'
        }`}>
          <div className="flex items-start space-x-3">
            <Icon 
              name={testResult.success ? 'CheckCircle' : 'XCircle'} 
              size={20} 
              className={`flex-shrink-0 mt-0.5 ${
                testResult.success ? 'text-success-600' : 'text-error-600'
              }`}
            />
            <div className="flex-1">
              <h4 className={`font-medium ${
                testResult.success ? 'text-success-800' : 'text-error-800'
              }`}>
                {testResult.success ? 'Connection Successful' : 'Connection Failed'}
              </h4>
              <p className={`text-sm mt-1 ${
                testResult.success ? 'text-success-700' : 'text-error-700'
              }`}>
                {testResult.message}
              </p>
              
              {testResult.success && testResult.details && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center space-x-4 text-sm text-success-700">
                    <span>Server: {testResult.details.serverVersion}</span>
                    {responseTime && (
                      <span>Response: {responseTime}ms</span>
                    )}
                  </div>
                  {testResult.details.features.length > 0 && (
                    <div className="text-sm text-success-700">
                      <span className="font-medium">Features: </span>
                      {testResult.details.features.join(', ')}
                    </div>
                  )}
                </div>
              )}
              
              {!testResult.success && testResult.error && (
                <div className="mt-2 text-sm text-error-700 font-mono bg-error-100 p-2 rounded">
                  {testResult.error}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionTester;