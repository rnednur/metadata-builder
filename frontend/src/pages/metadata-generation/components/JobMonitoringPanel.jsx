import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const JobMonitoringPanel = ({ 
  jobs, 
  onCancelJob, 
  onViewDetails, 
  onRetryJob,
  onDownloadResults,
  onViewInExplore,
  onRemoveJob,
  onClearCompleted 
}) => {
  const [sortField, setSortField] = useState('startTime');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterStatus, setFilterStatus] = useState('all');

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-success bg-success-50 border-success-200';
      case 'running':
        return 'text-primary bg-primary-50 border-primary-200';
      case 'failed':
        return 'text-error bg-error-50 border-error-200';
      case 'cancelled':
        return 'text-secondary bg-secondary-50 border-secondary-200';
      case 'queued':
        return 'text-warning bg-warning-50 border-warning-200';
      default:
        return 'text-text-muted bg-surface-secondary border-border';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return 'CheckCircle';
      case 'running':
        return 'Play';
      case 'failed':
        return 'XCircle';
      case 'cancelled':
        return 'StopCircle';
      case 'queued':
        return 'Clock';
      default:
        return 'Circle';
    }
  };

  const formatDuration = (durationInSeconds) => {
    if (!durationInSeconds || durationInSeconds < 0) return '0s';
    
    const seconds = Math.floor(durationInSeconds);
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatEstimatedTime = (seconds) => {
    if (!seconds) return 'Unknown';
    return formatDuration(seconds);
  };

  const filteredJobs = jobs.filter(job => {
    if (filterStatus === 'all') return true;
    return job.status === filterStatus;
  });

  const sortedJobs = [...filteredJobs].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];
    
    if (sortField === 'startTime') {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    }
    
    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    }
    return aValue < bValue ? 1 : -1;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSummaryStats = () => {
    const total = jobs.length;
    const completed = jobs.filter(job => job.status === 'completed').length;
    const running = jobs.filter(job => job.status === 'running').length;
    const failed = jobs.filter(job => job.status === 'failed').length;
    
    const totalEstimatedTime = jobs
      .filter(job => job.status === 'running' || job.status === 'queued')
      .reduce((sum, job) => sum + (job.estimatedTimeRemaining || 0), 0);
    
    return { total, completed, running, failed, totalEstimatedTime };
  };

  const stats = getSummaryStats();

  const ProgressBar = ({ progress, status }) => (
    <div className="w-full bg-secondary-100 rounded-full h-2">
      <div 
        className={`h-2 rounded-full transition-all duration-300 ${
          status === 'completed' ? 'bg-success' :
          status === 'failed' ? 'bg-error' :
          status === 'cancelled'? 'bg-secondary' : 'bg-primary'
        }`}
        style={{ width: `${Math.min(progress, 100)}%` }}
      />
    </div>
  );

  return (
    <div className="bg-surface border border-border rounded-lg h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Job Monitoring</h3>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div className="bg-surface-secondary rounded-lg p-3">
            <div className="text-2xl font-bold text-text-primary">{stats.total}</div>
            <div className="text-sm text-text-secondary">Total Jobs</div>
          </div>
          <div className="bg-success-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-success">{stats.completed}</div>
            <div className="text-sm text-success-700">Completed</div>
          </div>
          <div className="bg-primary-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-primary">{stats.running}</div>
            <div className="text-sm text-primary-700">Running</div>
          </div>
          <div className="bg-warning-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-warning">
              {formatEstimatedTime(stats.totalEstimatedTime)}
            </div>
            <div className="text-sm text-warning-700">Est. Remaining</div>
          </div>
        </div>

        {/* Filters and Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-text-primary">Filter:</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-1 border border-border rounded text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              >
                <option value="all">All Status</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="queued">Queued</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
          
          {/* Job Management Actions */}
          <div className="flex items-center space-x-2">
            {jobs.some(job => job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
              <Button
                variant="ghost"
                onClick={onClearCompleted}
                className="text-sm px-3 py-1"
                title="Clear completed, failed, and cancelled jobs"
              >
                <Icon name="Trash2" size={14} className="mr-1" />
                Clear Completed
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="flex-1 overflow-auto">
        {sortedJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-muted">
            <Icon name="Activity" size={48} className="mb-3 opacity-50" />
            <p className="text-lg font-medium mb-2">No jobs found</p>
            <p className="text-sm">
              {filterStatus === 'all' ?'Start a metadata generation job to see progress here'
                : `No jobs with status "${filterStatus}"`
              }
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-surface-secondary border-b border-border sticky top-0">
                <tr>
                  <th 
                    className="text-left p-4 font-medium text-text-primary cursor-pointer hover:bg-secondary-100 transition-colors"
                    onClick={() => handleSort('id')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Job ID</span>
                      {sortField === 'id' && (
                        <Icon 
                          name={sortDirection === 'asc' ? 'ChevronUp' : 'ChevronDown'} 
                          size={14} 
                        />
                      )}
                    </div>
                  </th>
                  <th className="text-left p-4 font-medium text-text-primary">Tables</th>
                  <th className="text-left p-4 font-medium text-text-primary">Progress</th>
                  <th 
                    className="text-left p-4 font-medium text-text-primary cursor-pointer hover:bg-secondary-100 transition-colors"
                    onClick={() => handleSort('startTime')}
                  >
                    <div className="flex items-center space-x-1">
                      <span>Started</span>
                      {sortField === 'startTime' && (
                        <Icon 
                          name={sortDirection === 'asc' ? 'ChevronUp' : 'ChevronDown'} 
                          size={14} 
                        />
                      )}
                    </div>
                  </th>
                  <th className="text-left p-4 font-medium text-text-primary">Duration</th>
                  <th className="text-left p-4 font-medium text-text-primary">Status</th>
                  <th className="text-left p-4 font-medium text-text-primary">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedJobs.map((job) => (
                  <tr key={job.id} className="border-b border-border hover:bg-surface-secondary/50 transition-colors">
                    <td className="p-4">
                      <div className="font-mono text-sm text-text-primary">{job.id}</div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm text-text-primary">
                        {job.tables.length === 1 
                          ? job.tables[0] 
                          : `${job.tables.length} tables`
                        }
                      </div>
                      {job.tables.length > 1 && (
                        <div className="text-xs text-text-muted">
                          {job.tables.slice(0, 2).join(', ')}
                          {job.tables.length > 2 && ` +${job.tables.length - 2} more`}
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-text-primary">{job.progress}%</span>
                          {job.status === 'running' && job.estimatedTimeRemaining && (
                            <span className="text-text-muted text-xs">
                              {formatEstimatedTime(job.estimatedTimeRemaining)} left
                            </span>
                          )}
                        </div>
                        <ProgressBar progress={job.progress} status={job.status} />
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm text-text-secondary">
                        {new Date(job.startTime).toLocaleString()}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-sm text-text-secondary">
                        {formatDuration(job.duration)}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}>
                        <Icon name={getStatusIcon(job.status)} size={12} />
                        <span className="capitalize">{job.status}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          onClick={() => onViewDetails(job)}
                          className="p-1"
                          aria-label="View details"
                        >
                          <Icon name="Eye" size={16} />
                        </Button>
                        
                        {job.status === 'running' && (
                          <Button
                            variant="ghost"
                            onClick={() => onCancelJob(job.id)}
                            className="p-1 text-error hover:text-error"
                            aria-label="Cancel job"
                          >
                            <Icon name="X" size={16} />
                          </Button>
                        )}
                        
                        {job.status === 'failed' && (
                          <Button
                            variant="ghost"
                            onClick={() => onRetryJob(job.id)}
                            className="p-1 text-warning hover:text-warning"
                            aria-label="Retry job"
                          >
                            <Icon name="RotateCcw" size={16} />
                          </Button>
                        )}
                        
                        {job.status === 'completed' && (
                          <>
                            <Button
                              variant="ghost"
                              onClick={() => onViewInExplore(job)}
                              className="p-1 text-accent hover:text-accent"
                              aria-label="View in Explore"
                              title="View metadata in Schema Explorer"
                            >
                              <Icon name="ExternalLink" size={16} />
                            </Button>
                            <Button
                              variant="ghost"
                              onClick={() => onDownloadResults(job.id)}
                              className="p-1 text-success hover:text-success"
                              aria-label="Download results"
                            >
                              <Icon name="Download" size={16} />
                            </Button>
                          </>
                        )}
                        
                        {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                          <Button
                            variant="ghost"
                            onClick={() => onRemoveJob(job.jobId)}
                            className="p-1 text-text-muted hover:text-error"
                            aria-label="Remove job"
                            title="Remove job from list"
                          >
                            <Icon name="X" size={16} />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobMonitoringPanel;