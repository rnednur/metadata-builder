import React, { useState, useEffect } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import TableSelectionPanel from './components/TableSelectionPanel';
import ConfigurationPanel from './components/ConfigurationPanel';
import JobMonitoringPanel from './components/JobMonitoringPanel';
import JobDetailsModal from './components/JobDetailsModal';
import { databaseAPI, metadataAPI, apiUtils } from '../../services/api';

const MetadataGeneration = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [selectedTables, setSelectedTables] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [isJobDetailsOpen, setIsJobDetailsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);
  const [error, setError] = useState(null);

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const [configuration, setConfiguration] = useState({
    sampleSize: 100,
    numSamples: 5,
    maxPartitions: 10,
    includeRelationships: false,
    includeAggregationRules: true,
    includeQueryRules: false,
    includeDataQuality: true,
    includeQueryExamples: true,
    includeAdditionalInsights: false,
    includeBusinessRules: false,
    includeCategoricalDefinitions: true,
    generateLookML: false,
  });

  // Load databases and their schemas on component mount
  useEffect(() => {
    loadDatabasesWithSchemas();
  }, []);

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
      // Process each table separately for metadata generation
      const jobPromises = selectedTables.map(async (table) => {
        try {
          const metadataRequest = apiUtils.buildMetadataRequest({
            dbName: table.database,
            tableName: table.name,
            schemaName: table.schema,
            sampleSize: configuration.sampleSize,
            numSamples: configuration.numSamples,
            maxPartitions: configuration.maxPartitions,
            includeRelationships: configuration.includeRelationships,
            includeAggregationRules: configuration.includeAggregationRules,
            includeQueryRules: configuration.includeQueryRules,
            includeDataQuality: configuration.includeDataQuality,
            includeQueryExamples: configuration.includeQueryExamples,
            includeAdditionalInsights: configuration.includeAdditionalInsights,
            includeBusinessRules: configuration.includeBusinessRules,
            includeCategoricalDefinitions: configuration.includeCategoricalDefinitions,
          });

          // Use async API for better user experience
          const response = await metadataAPI.generateMetadataAsync(metadataRequest);
          const jobData = response.data;

          return {
            id: jobData.job_id,
            tables: [table.name],
            progress: 0,
            status: jobData.status,
            startTime: jobData.created_at,
            duration: 0,
            estimatedTimeRemaining: null,
            configuration: { ...configuration },
            tableProgress: [{
              name: table.name,
              schema: table.schema,
              database: table.database,
              progress: 0,
              status: jobData.status
            }],
            logs: [
              { 
                timestamp: new Date().toLocaleTimeString(), 
                level: 'info', 
                message: `Started metadata generation for ${table.name}` 
              }
            ],
            jobId: jobData.job_id
          };
        } catch (err) {
          console.error(`Failed to start job for table ${table.name}:`, err);
          return {
            id: `job_${Date.now()}_${table.name}`,
            tables: [table.name],
            progress: 0,
            status: 'failed',
            startTime: new Date().toISOString(),
            duration: 0,
            estimatedTimeRemaining: null,
            configuration: { ...configuration },
            tableProgress: [{
              name: table.name,
              schema: table.schema,
              database: table.database,
              progress: 0,
              status: 'failed'
            }],
            logs: [
              { 
                timestamp: new Date().toLocaleTimeString(), 
                level: 'error', 
                message: `Failed to start metadata generation: ${apiUtils.handleApiError(err)}` 
              }
            ],
            error: apiUtils.handleApiError(err)
          };
        }
      });

      const newJobs = await Promise.all(jobPromises);
      setJobs(prev => [...newJobs, ...prev]);
      setSelectedTables([]);

      // Start polling for job updates
      newJobs.forEach(job => {
        if (job.jobId && job.status !== 'failed') {
          pollJobProgress(job.jobId);
        }
      });

    } catch (err) {
      setError(apiUtils.handleApiError(err));
      console.error('Failed to start metadata generation:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const pollJobProgress = async (jobId) => {
    try {
      await apiUtils.pollJobStatus(
        jobId,
        (updatedJob) => {
          // Update job status in the list
          setJobs(prev => prev.map(job => 
            job.jobId === jobId 
              ? {
                  ...job,
                  status: updatedJob.status,
                  progress: updatedJob.progress || 0,
                  duration: new Date() - new Date(job.startTime),
                  tableProgress: job.tableProgress.map(table => ({
                    ...table,
                    status: updatedJob.status,
                    progress: updatedJob.progress || 0
                  })),
                  result: updatedJob.result,
                  error: updatedJob.error
                }
              : job
          ));

          // Dispatch event when job completes successfully
          if (updatedJob.status === 'completed') {
            const currentJob = jobs.find(j => j.jobId === jobId);
            if (currentJob && currentJob.tableProgress[0]) {
              const database = currentJob.tableProgress[0].database;
              const schema = currentJob.tableProgress[0].schema;
              const table = currentJob.tableProgress[0].name;
              
              const refreshEvent = new CustomEvent('metadataGenerated', {
                detail: {
                  database: database,
                  schema: schema,
                  table: table
                }
              });
              window.dispatchEvent(refreshEvent);
              console.log(`Dispatched metadataGenerated event for ${database}.${schema}.${table}`);
            }
          }
        }
      );
    } catch (err) {
      console.error(`Polling failed for job ${jobId}:`, err);
      setJobs(prev => prev.map(job => 
        job.jobId === jobId 
          ? {
              ...job,
              status: 'failed',
              error: apiUtils.handleApiError(err)
            }
          : job
      ));
    }
  };

  const handleCancelJob = (jobId) => {
    setJobs(prev => 
      prev.map(job => 
        job.id === jobId 
          ? { ...job, status: 'cancelled', estimatedTimeRemaining: null }
          : job
      )
    );
  };

  const handleViewJobDetails = (job) => {
    setSelectedJob(job);
    setIsJobDetailsOpen(true);
  };

  const handleRetryJob = (jobId) => {
    setJobs(prev => 
      prev.map(job => 
        job.id === jobId 
          ? { 
              ...job, 
              status: 'running', 
              progress: 0, 
              estimatedTimeRemaining: job.tables.length * 300,
              error: null,
              errorDetails: null,
              tableProgress: job.tableProgress.map(table => ({
                ...table,
                progress: 0,
                status: 'queued',
                error: null
              }))
            }
          : job
      )
    );
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
              Generate AI-powered metadata analysis for your database tables with comprehensive configuration options and real-time monitoring.
            </p>
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

          {/* Main Content */}
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-6 h-[calc(100vh-200px)]">
            {/* Configuration Panel - Left 40% */}
            <div className="xl:col-span-2 space-y-6">
              {/* Table Selection */}
              <div className="h-1/2">
                <TableSelectionPanel
                  databases={databases}
                  selectedTables={selectedTables}
                  onTableSelectionChange={handleTableSelectionChange}
                  onSelectAll={handleSelectAllTables}
                  onClearAll={handleClearAllTables}
                  isLoading={isLoadingDatabases}
                />
              </div>

              {/* Configuration */}
              <div className="h-1/2">
                <ConfigurationPanel
                  configuration={configuration}
                  onConfigurationChange={setConfiguration}
                  onStartGeneration={handleStartGeneration}
                  isGenerating={isGenerating}
                  hasValidSelection={selectedTables.length > 0}
                />
              </div>
            </div>

            {/* Job Monitoring Panel - Right 60% */}
            <div className="xl:col-span-3">
              <JobMonitoringPanel
                jobs={jobs}
                onCancelJob={handleCancelJob}
                onViewDetails={handleViewJobDetails}
                onRetryJob={handleRetryJob}
                onDownloadResults={handleDownloadResults}
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