import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import SchemaTree from '../schema-explorer/components/SchemaTree';
import ConfigurationPanel from './components/ConfigurationPanel';
import JobMonitoringPanel from './components/JobMonitoringPanel';
import JobDetailsModal from './components/JobDetailsModal';
import { useJobs } from '../../contexts/JobContext';
import { databaseAPI, metadataAPI, apiUtils } from '../../services/api';

const MetadataGeneration = () => {
  const navigate = useNavigate();
  const { jobs, addJob, removeJob, updateJobWithRealId, updateJobStatus, clearCompletedJobs, totalJobs, hasActiveJobs } = useJobs();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [selectedTables, setSelectedTables] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [isJobDetailsOpen, setIsJobDetailsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  // Remove these as they're handled by SchemaTree now
  const [error, setError] = useState(null);

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const [configuration, setConfiguration] = useState({
    sampleSize: 100,
    numSamples: 5,
    maxPartitions: 10,
    partitionLimit: 10,
    // Using default model from backend configuration (same as Explore page)
    customPrompt: '',
    generateLookML: false,
    enableParallelProcessing: false,
    saveIntermediateResults: false,
    // Essential Only preset - default configuration
    dataQuality: false,
    categoricalValues: true,
    queryExamples: false,
    queryRules: false,
    businessRules: false,
    relationships: false,
    aggregationRules: false,
    additionalInsights: false,
    // Legacy field mappings for backwards compatibility
    includeRelationships: false,
    includeAggregationRules: false,
    includeQueryRules: false,
    includeDataQuality: false,
    includeQueryExamples: false,
    includeAdditionalInsights: false,
    includeBusinessRules: false,
    includeCategoricalDefinitions: true,
  });

  // Database loading now handled by SchemaTree component

  const loadDatabasesWithSchemas = async () => {
    try {
      setIsLoadingDatabases(true);
      setError(null);

      // Get all database connections
      const connectionsResponse = await databaseAPI.listConnections();
      const connections = connectionsResponse.data;

      // Load schemas for each connection
      const databasesWithSchemas = await Promise.allSettled(
        connections.map(async (connection) => {
          try {
            const schemasResponse = await databaseAPI.getSchemas(connection.name);
            const schemasData = schemasResponse.data;

            // Load tables for each schema
            const schemasWithTables = await Promise.allSettled(
              schemasData.schemas.map(async (schema) => {
                try {
                  const tablesResponse = await databaseAPI.getTables(connection.name, schema.schema_name);
                  return {
                    id: schema.schema_name,
                    name: schema.schema_name,
                    tables: tablesResponse.data.tables.map(table => ({
                      id: `${schema.schema_name}.${table.table_name}`,
                      name: table.table_name,
                      rowCount: table.row_count || 0,
                      columnCount: table.column_count || 0,
                    }))
                  };
                } catch (err) {
                  console.warn(`Failed to load tables for schema ${schema.schema_name}:`, err);
                  return {
                    id: schema.schema_name,
                    name: schema.schema_name,
                    tables: []
                  };
                }
              })
            );

            return {
              id: connection.name,
              name: connection.name,
              type: connection.type,
              status: connection.status || 'unknown',
              schemas: schemasWithTables
                .filter(result => result.status === 'fulfilled')
                .map(result => result.value)
            };
          } catch (err) {
            console.warn(`Failed to load schemas for connection ${connection.name}:`, err);
            return {
              id: connection.name,
              name: connection.name,
              type: connection.type,
              status: 'disconnected',
              schemas: []
            };
          }
        })
      );

      const validDatabases = databasesWithSchemas
        .filter(result => result.status === 'fulfilled')
        .map(result => result.value);

      setDatabases(validDatabases);
    } catch (err) {
      setError(apiUtils.handleApiError(err));
      console.error('Failed to load databases:', err);
    } finally {
      setIsLoadingDatabases(false);
    }
  };

  // All database data now loaded from real API via loadDatabasesWithSchemas()

  // Initialize with empty jobs - will be populated by real API calls when metadata generation starts

  // Real-time job updates now handled by API polling in pollJobProgress() function

  const breadcrumbItems = [
    { label: 'Dashboard', path: '/database-connections-dashboard' },
    { label: 'Metadata Generation' }
  ];

  const handleTableSelectionChange = (table) => {
    setSelectedTables(prev => {
      const isSelected = prev.some(t => t.id === table.id);
      if (isSelected) {
        return prev.filter(t => t.id !== table.id);
      } else {
        return [...prev, table];
      }
    });
  };

  const handleSelectAllTables = () => {
    const allTables = databases.flatMap(db => 
      db.schemas.flatMap(schema => 
        schema.tables.map(table => ({
          ...table,
          database: db.name,
          schema: schema.name
        }))
      )
    );
    setSelectedTables(allTables);
  };

  const handleClearAllTables = () => {
    setSelectedTables([]);
  };

  const handleStartGeneration = async () => {
    if (selectedTables.length === 0) return;

    setIsGenerating(true);
    setError(null);
    
    try {
      // Create jobs immediately for instant UI feedback
      const immediateJobs = selectedTables.map(table => ({
        id: `temp_${Date.now()}_${table.name}`,
        tables: [table.name],
        progress: 0,
        status: 'pending',
        startTime: new Date().toISOString(),
        duration: 0,
        estimatedTimeRemaining: null,
        configuration: { ...configuration },
        tableProgress: [{
          name: table.name,
          schema: table.schema,
          database: table.database,
          progress: 0,
          status: 'pending'
        }],
        logs: [
          { 
            timestamp: new Date().toLocaleTimeString(), 
            level: 'info', 
            message: `Submitting metadata generation for ${table.name}` 
          }
        ],
        jobId: null // Will be updated when API responds
      }));

      // Add jobs to UI immediately
      console.log('Adding immediate jobs for instant feedback:', immediateJobs);
      immediateJobs.forEach(job => addJob(job));

      // Process each table separately for metadata generation
      const jobPromises = selectedTables.map(async (table, index) => {
        try {
          const metadataRequest = apiUtils.buildMetadataRequest({
            dbName: table.database,
            tableName: table.name,
            schemaName: table.schema,
            sampleSize: configuration.sampleSize,
            numSamples: configuration.numSamples,
            maxPartitions: configuration.maxPartitions,
            customPrompt: configuration.customPrompt || '',
            // Map new configuration field names to legacy API field names
            includeRelationships: configuration.relationships || configuration.includeRelationships || false,
            includeAggregationRules: configuration.aggregationRules || configuration.includeAggregationRules || false,
            includeQueryRules: configuration.queryRules || configuration.includeQueryRules || false,
            includeDataQuality: configuration.dataQuality || configuration.includeDataQuality || false,
            includeQueryExamples: configuration.queryExamples || configuration.includeQueryExamples || false,
            includeAdditionalInsights: configuration.additionalInsights || configuration.includeAdditionalInsights || false,
            includeBusinessRules: configuration.businessRules || configuration.includeBusinessRules || false,
            includeCategoricalDefinitions: configuration.categoricalValues || configuration.includeCategoricalDefinitions || true,
          });

          // Use async API for better user experience
          const response = await metadataAPI.generateMetadataAsync(metadataRequest);
          const jobData = response.data;

          // Update the immediate job with real job ID
          const tempJob = immediateJobs[index];
          updateJobWithRealId(tempJob.id, jobData);
          
          console.log('Updated job with real ID:', jobData.job_id);
          return jobData;
        } catch (err) {
          console.error(`Failed to start job for table ${table.name}:`, err);
          
          // Update the immediate job to failed status
          const tempJob = immediateJobs[index];
          updateJobStatus(tempJob.id, {
            status: 'failed',
            error: apiUtils.handleApiError(err),
            logs: [
              ...tempJob.logs,
              { 
                timestamp: new Date().toLocaleTimeString(), 
                level: 'error', 
                message: `Failed to start metadata generation: ${apiUtils.handleApiError(err)}` 
              }
            ]
          });
          
          return null; // Return null for failed jobs
        }
      });

      const newJobs = await Promise.all(jobPromises);
      
      // Jobs are already added to context immediately above
      console.log('API job creation completed:', newJobs);
      setSelectedTables([]);

    } catch (err) {
      setError(apiUtils.handleApiError(err));
      console.error('Failed to start metadata generation:', err);
    } finally {
      setIsGenerating(false);
    }
  };


  const handleCancelJob = (jobId) => {
    // TODO: Implement actual job cancellation API call
    console.log('Cancel job not yet implemented:', jobId);
  };

  const handleViewJobDetails = (job) => {
    setSelectedJob(job);
    setIsJobDetailsOpen(true);
  };

  const handleRetryJob = (jobId) => {
    // TODO: Implement actual job retry API call
    console.log('Retry job not yet implemented:', jobId);
  };

  const handleDownloadResults = (jobId) => {
    // Simulate download
    const job = jobs.find(j => j.id === jobId);
    if (job) {
      const blob = new Blob([JSON.stringify(job, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `metadata_${jobId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const handleRemoveJob = (jobId) => {
    removeJob(jobId);
  };

  const handleClearCompletedJobs = () => {
    clearCompletedJobs();
  };

  const handleViewInExplore = (job) => {
    // Navigate to schema explorer with the specific table selected
    if (job.tableProgress && job.tableProgress[0]) {
      const { database, schema, name } = job.tableProgress[0];
      // Navigate to schema explorer with query parameters to auto-select the table
      navigate(`/schema-explorer?database=${encodeURIComponent(database)}&schema=${encodeURIComponent(schema)}&table=${encodeURIComponent(name)}`);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header
        onMenuToggle={() => setIsSidebarOpen(!isSidebarOpen)}
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
          {/* Breadcrumb */}
          <div className="mb-6">
            <Breadcrumb items={breadcrumbItems} />
          </div>

          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-text-primary mb-2">
              Metadata Generation
            </h1>
            <p className="text-text-secondary">
              Generate AI-powered metadata analysis for your database tables with multi-selection and real-time job monitoring.
            </p>
            {totalJobs > 0 && (
              <div className="mt-3 text-sm text-accent">
                📋 {totalJobs} job{totalJobs !== 1 ? 's' : ''} in progress or completed
                {hasActiveJobs && 
                  ` • ${jobs.filter(job => job.status === 'running' || job.status === 'pending').length} active`
                }
              </div>
            )}
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-red-800 font-medium">Error</p>
                  <p className="text-red-700">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto p-1 text-red-500 hover:text-red-700"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Three-Panel Layout (like Explore) */}
          <div className="flex h-[calc(100vh-200px)] gap-6">
            {/* Left Panel - Schema Tree with Multi-Select */}
            <div className="w-80 flex flex-col">
              <SchemaTree
                onTableSelect={(table) => {
                  // Toggle table selection for multi-select
                  setSelectedTables(prev => {
                    const isSelected = prev.some(t => t.id === table.id);
                    if (isSelected) {
                      return prev.filter(t => t.id !== table.id);
                    } else {
                      return [...prev, table];
                    }
                  });
                }}
                selectedTables={selectedTables}
                enableMultiSelect={true}
              />
            </div>

            {/* Center Panel - Job Monitoring */}
            <div className="flex-1">
              <JobMonitoringPanel
                jobs={jobs}
                onCancelJob={handleCancelJob}
                onViewDetails={handleViewJobDetails}
                onRetryJob={handleRetryJob}
                onDownloadResults={handleDownloadResults}
                onViewInExplore={handleViewInExplore}
                onRemoveJob={handleRemoveJob}
                onClearCompleted={handleClearCompletedJobs}
              />
            </div>

            {/* Right Panel - Configuration */}
            <div className="w-80">
              <ConfigurationPanel
                configuration={configuration}
                onConfigurationChange={setConfiguration}
                onStartGeneration={handleStartGeneration}
                isGenerating={isGenerating}
                hasValidSelection={selectedTables.length > 0}
              />
            </div>
          </div>
        </div>
      </main>

      {/* Job Details Modal */}
      <JobDetailsModal
        job={selectedJob}
        isOpen={isJobDetailsOpen}
        onClose={() => {
          setIsJobDetailsOpen(false);
          setSelectedJob(null);
        }}
        onDownloadResults={handleDownloadResults}
        onRetryJob={handleRetryJob}
      />
    </div>
  );
};

export default MetadataGeneration;