import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import DatabaseTypeSelector from './components/DatabaseTypeSelector';
import ConnectionDetailsForm from './components/ConnectionDetailsForm';
import AuthenticationForm from './components/AuthenticationForm';
import ConnectionTester from './components/ConnectionTester';
import FormActions from './components/FormActions';
import Icon from '../../components/AppIcon';
import { databaseAPI, apiUtils } from '../../services/api';

const AddEditDatabaseConnection = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Check if we're in edit mode
  const isEditMode = location.state?.connection ? true : false;
  const existingConnection = location.state?.connection;

  // Form state
  const [selectedDatabaseType, setSelectedDatabaseType] = useState(null);
  const [formData, setFormData] = useState({
    connectionName: '',
    databaseName: '',
    host: '',
    port: '',
    username: '',
    password: '',
    schema: '',
    serviceAccountKey: '',
    sslEnabled: false,
    sslVerify: false,
    connectionTimeout: '',
    queryTimeout: '',
    additionalParams: '',
    predefinedSchemas: ''
  });
  const [errors, setErrors] = useState({});
  const [testResult, setTestResult] = useState(null);

  // Initialize form with existing data if editing
  useEffect(() => {
    if (isEditMode && existingConnection) {
      // Ensure selectedDatabaseType is an object with at least an 'id' field
      setSelectedDatabaseType(prev => {
        if (typeof existingConnection.type === 'string') {
          return { id: existingConnection.type };
        }
        return existingConnection.type;
      });
      setFormData({
        connectionName: existingConnection.name || '',
        databaseName: existingConnection.database || '',
        host: existingConnection.host || '',
        port: existingConnection.port || '',
        username: existingConnection.username || '',
        password: '', // Don't pre-fill password for security
        schema: existingConnection.schema || '',
        serviceAccountKey: '', // Don't pre-fill for security
        sslEnabled: existingConnection.sslEnabled || false,
        sslVerify: existingConnection.sslVerify || false,
        connectionTimeout: existingConnection.connectionTimeout || '',
        queryTimeout: existingConnection.queryTimeout || '',
        additionalParams: existingConnection.additionalParams || '',
        predefinedSchemas: existingConnection.predefinedSchemas || ''
      });
    }
  }, [isEditMode, existingConnection]);

  const breadcrumbItems = [
    { label: 'Connections', path: '/database-connections-dashboard' },
    { label: isEditMode ? 'Edit Connection' : 'Add Connection' }
  ];

  const handleSidebarToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleDatabaseTypeChange = (type) => {
    setSelectedDatabaseType(type);
    setHasUnsavedChanges(true);
    
    // Clear type-specific errors
    const newErrors = { ...errors };
    delete newErrors.databaseType;
    setErrors(newErrors);

    // Set default port if available
    if (type.defaultPort) {
      setFormData(prev => ({
        ...prev,
        port: type.defaultPort.toString()
      }));
    }
  };

  const handleFormDataChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setHasUnsavedChanges(true);
    
    // Clear field-specific error
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Database type validation
    if (!selectedDatabaseType) {
      newErrors.databaseType = 'Please select a database type';
    }

    // Connection name validation
    if (!formData.connectionName.trim()) {
      newErrors.connectionName = 'Connection name is required';
    } else if (formData.connectionName.length < 3) {
      newErrors.connectionName = 'Connection name must be at least 3 characters';
    }

    // Database name validation
    if (!formData.databaseName.trim()) {
      newErrors.databaseName = selectedDatabaseType?.id === 'bigquery' ?'Project ID is required' :'Database name is required';
    }

    // Type-specific validations
    if (selectedDatabaseType) {
      switch (selectedDatabaseType.id) {
        case 'sqlite': case'duckdb':
          // File path validation
          if (formData.databaseName && !formData.databaseName.includes('.')) {
            newErrors.databaseName = 'Please provide a valid file path with extension';
          }
          break;
          
        case 'bigquery':
          // Service account key validation
          if (!formData.serviceAccountKey.trim()) {
            newErrors.serviceAccountKey = 'Service account key is required';
          } else {
            try {
              JSON.parse(formData.serviceAccountKey);
            } catch {
              newErrors.serviceAccountKey = 'Invalid JSON format';
            }
          }
          break;
          
        default:
          // Standard database validations
          if (!formData.host.trim()) {
            newErrors.host = 'Host is required';
          }
          if (!formData.username.trim()) {
            newErrors.username = 'Username is required';
          }
          if (!formData.password.trim() && !isEditMode) {
            newErrors.password = 'Password is required';
          }
          if (formData.port && (isNaN(formData.port) || formData.port < 1 || formData.port > 65535)) {
            newErrors.port = 'Port must be a number between 1 and 65535';
          }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    
    try {
      // Build the connection request data
      const connectionRequestData = apiUtils.buildConnectionRequest({
        name: formData.connectionName,
        type: selectedDatabaseType.id,
        host: formData.host || null,
        port: formData.port ? parseInt(formData.port) : null,
        username: formData.username || null,
        password: formData.password || null,
        database: formData.databaseName || null,
        serviceName: formData.serviceName || null,
        sid: formData.sid || null,
        tnsName: formData.tnsName || null,
        projectId: selectedDatabaseType.id === 'bigquery' ? formData.databaseName : null,
        credentialsPath: selectedDatabaseType.id === 'bigquery' ? formData.serviceAccountKey : null,
        predefinedSchemas: formData.predefinedSchemas || null,
      });

      let response;
      if (isEditMode) {
        // For edit mode, we would need an update API endpoint
        // Since it's not in the swagger, we'll delete and recreate
        await databaseAPI.deleteConnection(existingConnection.name);
        response = await databaseAPI.createConnection(connectionRequestData);
      } else {
        response = await databaseAPI.createConnection(connectionRequestData);
      }

      console.log('Connection saved successfully:', response.data);
      
      // Navigate back to dashboard with success message
      navigate('/database-connections-dashboard', {
        state: {
          message: `Connection "${formData.connectionName}" ${isEditMode ? 'updated' : 'created'} successfully!`,
          type: 'success'
        }
      });
    } catch (error) {
      console.error('Error saving connection:', error);
      setErrors({
        submit: apiUtils.handleApiError(error)
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/database-connections-dashboard');
  };

  const handleTestComplete = (result) => {
    setTestResult(result);
  };

  const isFormValid = () => {
    return selectedDatabaseType && 
           formData.connectionName.trim() && 
           formData.databaseName.trim() &&
           Object.keys(errors).length === 0;
  };

  return (
    <div className="min-h-screen bg-background">
            <Header 
        onMenuToggle={handleSidebarToggle} 
        isMenuOpen={isSidebarOpen}
        isSidebarCollapsed={isSidebarCollapsed}
      />
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />

      <main className={`pt-16 ${isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
        <div className="p-6">
          {/* Page Header */}
          <div className="mb-6">
            <Breadcrumb items={breadcrumbItems} />
            <div className="mt-4 flex items-center space-x-3">
              <div className="p-2 bg-accent-100 rounded-lg">
                <Icon name="Database" size={24} className="text-accent-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-text-primary">
                  {isEditMode ? 'Edit Database Connection' : 'Add Database Connection'}
                </h1>
                <p className="text-text-secondary">
                  {isEditMode 
                    ? 'Modify the configuration for your database connection'
                    : 'Configure a new database connection for metadata generation'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Form Container */}
          <div className="max-w-6xl mx-auto">
            <div className="bg-surface rounded-lg shadow-sm border border-border">
              <div className="p-6">
                {/* Database Type Selection */}
                <div className="mb-8">
                  <DatabaseTypeSelector
                    value={selectedDatabaseType}
                    onChange={handleDatabaseTypeChange}
                    error={errors.databaseType}
                  />
                </div>

                {/* Main Form - Two Column Layout */}
                {selectedDatabaseType && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left Column - Connection Details */}
                    <div>
                      <ConnectionDetailsForm
                        formData={formData}
                        onChange={handleFormDataChange}
                        errors={errors}
                        databaseType={selectedDatabaseType}
                      />
                    </div>

                    {/* Right Column - Authentication & Testing */}
                    <div className="space-y-8">
                      <AuthenticationForm
                        formData={formData}
                        onChange={handleFormDataChange}
                        errors={errors}
                        databaseType={selectedDatabaseType}
                      />
                      
                      <ConnectionTester
                        formData={formData}
                        databaseType={selectedDatabaseType}
                        onTestComplete={handleTestComplete}
                      />
                    </div>
                  </div>
                )}

                {/* Submit Error */}
                {errors.submit && (
                  <div className="mt-6 p-4 bg-error-50 border border-error-200 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Icon name="AlertCircle" size={20} className="text-error-600" />
                      <span className="text-sm text-error-700">{errors.submit}</span>
                    </div>
                  </div>
                )}

                {/* Form Actions */}
                {selectedDatabaseType && (
                  <FormActions
                    onSave={handleSave}
                    onCancel={handleCancel}
                    isLoading={isLoading}
                    hasUnsavedChanges={hasUnsavedChanges}
                    isValid={isFormValid()}
                    isEditMode={isEditMode}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AddEditDatabaseConnection;