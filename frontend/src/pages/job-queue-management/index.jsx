import React, { useState, useEffect } from 'react';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import Icon from '../../components/AppIcon';
import Button from '../../components/ui/Button';
import QueueStatistics from './components/QueueStatistics';
import JobFilters from './components/JobFilters';
import BulkOperations from './components/BulkOperations';
import JobTable from './components/JobTable';
import JobDetailsModal from './components/JobDetailsModal';
import { useJobs } from '../../contexts/JobContext';

const JobQueueManagement = () => {
  const { jobs, getJobStats, removeJob, clearCompletedJobs } = useJobs();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState({ key: 'startTime', direction: 'desc' });
  const [filters, setFilters] = useState({
    status: '',
    jobType: '',
    priority: '',
    dateFrom: '',
    dateTo: '',
    search: ''
  });

  // Transform JobContext jobs to Monitor page format
  const transformJobForMonitor = (job) => ({
    id: job.jobId || job.id,
    type: "metadata_generation",
    targetObjects: job.tables || (job.tableProgress ? job.tableProgress.map(t => t.name) : []),
    status: job.status,
    priority: "medium", // Default priority since not stored in JobContext
    progress: job.progress || 0,
    createdAt: job.startTime,
    duration: job.duration || 0,
    error: job.error || null,
    configuration: {
      sampleSize: job.configuration?.sampleSize || 100,
      partitionLimit: job.configuration?.partitionLimit || 10,
      analysisType: "standard"
    },
    metrics: {
      cpuUsage: 0, // Not tracked yet
      memoryUsage: 0, // Not tracked yet
      recordsProcessed: 0, // Not tracked yet
      processingRate: 0, // Not tracked yet
      dataSize: "Unknown"
    },
    logs: job.logs || []
  });

  // Define helper function first
  const formatAverageDuration = (jobsWithDuration) => {
    if (jobsWithDuration.length === 0) return "0s";
    
    const totalSeconds = jobsWithDuration.reduce((sum, job) => sum + job.duration, 0);
    const avgSeconds = Math.floor(totalSeconds / jobsWithDuration.length);
    
    if (avgSeconds < 60) return `${avgSeconds}s`;
    if (avgSeconds < 3600) return `${Math.floor(avgSeconds / 60)}m ${avgSeconds % 60}s`;
    return `${Math.floor(avgSeconds / 3600)}h ${Math.floor((avgSeconds % 3600) / 60)}m`;
  };

  // Get real jobs from JobContext
  const realJobs = jobs.map(transformJobForMonitor);
  
  // Calculate real statistics
  const statistics = {
    totalJobs: realJobs.length,
    runningJobs: realJobs.filter(job => job.status === 'running').length,
    pendingJobs: realJobs.filter(job => job.status === 'pending').length,
    completedJobs: realJobs.filter(job => job.status === 'completed').length,
    failedJobs: realJobs.filter(job => job.status === 'failed').length,
    averageDuration: realJobs.length > 0 
      ? formatAverageDuration(realJobs.filter(job => job.duration > 0))
      : "0s"
  };

  const breadcrumbItems = [
    { label: 'Dashboard', path: '/database-connections-dashboard' },
    { label: 'Job Queue Management' }
  ];

  // Filter and sort jobs
  const filteredJobs = realJobs.filter(job => {
    if (filters.status && job.status !== filters.status) return false;
    if (filters.jobType && job.type !== filters.jobType) return false;
    if (filters.priority && job.priority !== filters.priority) return false;
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return job.id.toLowerCase().includes(searchLower) ||
             job.targetObjects.some(target => target.toLowerCase().includes(searchLower));
    }
    return true;
  });

  const sortedJobs = [...filteredJobs].sort((a, b) => {
    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];
    
    if (sortConfig.direction === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const handleMenuToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const handleJobSelect = (jobId) => {
    setSelectedJobs(prev => 
      prev.includes(jobId) 
        ? prev.filter(id => id !== jobId)
        : [...prev, jobId]
    );
  };

  const handleSelectAll = () => {
    setSelectedJobs(sortedJobs.map(job => job.id));
  };

  const handleDeselectAll = () => {
    setSelectedJobs([]);
  };

  const handleJobDetails = (job) => {
    setSelectedJob(job);
    setIsDetailsModalOpen(true);
  };

  const handleJobAction = (action, jobId) => {
    console.log(`${action} job:`, jobId);
    
    switch (action) {
      case 'cancel':
        // TODO: Implement cancel API call
        console.log('Cancel not yet implemented');
        break;
      case 'retry':
        // TODO: Implement retry API call
        console.log('Retry not yet implemented');
        break;
      case 'delete':
        removeJob(jobId);
        break;
      case 'pause':
        // TODO: Implement pause API call
        console.log('Pause not yet implemented');
        break;
      case 'resume':
        // TODO: Implement resume API call
        console.log('Resume not yet implemented');
        break;
      default:
        console.log('Unknown action:', action);
    }
  };

  const handleBulkAction = (action) => {
    console.log(`Bulk ${action}:`, selectedJobs);
    
    switch (action) {
      case 'delete':
        selectedJobs.forEach(jobId => removeJob(jobId));
        break;
      case 'clearCompleted':
        clearCompletedJobs();
        break;
      case 'cancel':
        // TODO: Implement bulk cancel
        console.log('Bulk cancel not yet implemented');
        break;
      case 'retry':
        // TODO: Implement bulk retry
        console.log('Bulk retry not yet implemented');
        break;
      default:
        console.log('Unknown bulk action:', action);
    }
    
    setSelectedJobs([]);
  };

  const handleSort = (column) => {
    setSortConfig(prev => ({
      key: column,
      direction: prev.key === column && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleClearFilters = () => {
    setFilters({
      status: '',
      jobType: '',
      priority: '',
      dateFrom: '',
      dateTo: '',
      search: ''
    });
  };

  const handleRefresh = () => {
    // Jobs are automatically refreshed via JobContext polling
    console.log('Jobs are auto-refreshed via JobContext');
  };

  const isAllSelected = selectedJobs.length === sortedJobs.length && sortedJobs.length > 0;

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onMenuToggle={handleMenuToggle} 
        isMenuOpen={isSidebarOpen}
        isSidebarCollapsed={isSidebarCollapsed}
      />
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={handleSidebarClose}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />
      
              <main className={`pt-16 ${isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
        <div className="p-6">
          {/* Page Header */}
          <div className="mb-6">
            <Breadcrumb items={breadcrumbItems} />
            <div className="flex items-center justify-between mt-4">
              <div>
                <h1 className="text-2xl font-semibold text-text-primary">
                  Job Queue Management
                </h1>
                <p className="text-text-secondary mt-1">
                  Monitor and manage background tasks and operations
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <Button
                  variant="outline"
                  iconName="Download"
                  iconSize={16}
                >
                  Export Report
                </Button>
                <Button
                  variant="primary"
                  iconName="Plus"
                  iconSize={16}
                >
                  New Job
                </Button>
              </div>
            </div>
          </div>

          {/* Queue Statistics */}
          <QueueStatistics statistics={statistics} />

          {/* Filters */}
          <JobFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
            onRefresh={handleRefresh}
          />

          {/* Bulk Operations */}
          <BulkOperations
            selectedJobs={selectedJobs}
            onSelectAll={handleSelectAll}
            onDeselectAll={handleDeselectAll}
            onBulkCancel={() => handleBulkAction('cancel')}
            onBulkRetry={() => handleBulkAction('retry')}
            onBulkDelete={() => handleBulkAction('delete')}
            totalJobs={sortedJobs.length}
            isAllSelected={isAllSelected}
          />

          {/* Jobs Table */}
          <JobTable
            jobs={sortedJobs}
            selectedJobs={selectedJobs}
            onJobSelect={handleJobSelect}
            onJobDetails={handleJobDetails}
            onJobAction={handleJobAction}
            sortConfig={sortConfig}
            onSort={handleSort}
          />

          {/* Empty State */}
          {sortedJobs.length === 0 && (
            <div className="bg-surface border border-border rounded-lg p-12 text-center">
              <Icon name="Briefcase" size={48} className="text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-medium text-text-primary mb-2">
                {realJobs.length === 0 ? 'No jobs yet' : 'No jobs found'}
              </h3>
              <p className="text-text-secondary mb-4">
                {realJobs.length === 0 
                  ? 'Start generating metadata to see jobs appear here. Go to the Generate page to create your first job.'
                  : 'No jobs match your current filters. Try adjusting your search criteria.'
                }
              </p>
              {realJobs.length > 0 ? (
                <Button
                  variant="outline"
                  onClick={handleClearFilters}
                  iconName="RotateCcw"
                  iconSize={16}
                >
                  Clear Filters
                </Button>
              ) : (
                <Button
                  variant="primary"
                  onClick={() => window.location.href = '/metadata-generation'}
                  iconName="Sparkles"
                  iconSize={16}
                >
                  Start Generating Metadata
                </Button>
              )}
            </div>
          )}

          {/* Pagination */}
          {sortedJobs.length > 0 && (
            <div className="flex items-center justify-between mt-6">
              <div className="text-sm text-text-secondary">
                Showing {sortedJobs.length} of {realJobs.length} jobs
              </div>
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm" disabled>
                  <Icon name="ChevronLeft" size={16} />
                </Button>
                <span className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded">
                  1
                </span>
                <Button variant="outline" size="sm" disabled>
                  <Icon name="ChevronRight" size={16} />
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Job Details Modal */}
      <JobDetailsModal
        job={selectedJob}
        isOpen={isDetailsModalOpen}
        onClose={() => {
          setIsDetailsModalOpen(false);
          setSelectedJob(null);
        }}
      />
    </div>
  );
};

export default JobQueueManagement;