import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import JobStatusBadge from './JobStatusBadge';
import JobProgressBar from './JobProgressBar';

const JobTable = ({ 
  jobs, 
  selectedJobs, 
  onJobSelect, 
  onJobDetails, 
  onJobAction,
  sortConfig,
  onSort 
}) => {
  const [expandedRows, setExpandedRows] = useState(new Set());

  const toggleRowExpansion = (jobId) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedRows(newExpanded);
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getSortIcon = (column) => {
    if (sortConfig.key !== column) {
      return <Icon name="ArrowUpDown" size={14} className="text-text-muted" />;
    }
    return sortConfig.direction === 'asc' 
      ? <Icon name="ArrowUp" size={14} className="text-accent" />
      : <Icon name="ArrowDown" size={14} className="text-accent" />;
  };

  const handleSort = (column) => {
    onSort(column);
  };

  const getJobTypeIcon = (type) => {
    switch (type) {
      case 'metadata_generation':
        return 'Database';
      case 'lookml_creation':
        return 'FileCode';
      case 'schema_analysis':
        return 'Search';
      case 'data_profiling':
        return 'BarChart3';
      case 'system_maintenance':
        return 'Settings';
      default:
        return 'Briefcase';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'text-error';
      case 'medium':
        return 'text-warning';
      case 'low':
        return 'text-success';
      default:
        return 'text-text-muted';
    }
  };

  const canCancelJob = (status) => ['pending', 'running'].includes(status);
  const canRetryJob = (status) => ['failed', 'cancelled'].includes(status);

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      {/* Desktop Table */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-secondary border-b border-border">
            <tr>
              <th className="w-12 px-4 py-3">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-accent border-border rounded focus:ring-accent/20"
                  onChange={() => {}} // Handled by parent
                />
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('id')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Job ID</span>
                  {getSortIcon('id')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('type')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Type</span>
                  {getSortIcon('type')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-sm font-medium text-text-secondary">Target Objects</span>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('status')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Status</span>
                  {getSortIcon('status')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('priority')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Priority</span>
                  {getSortIcon('priority')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('createdAt')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Created</span>
                  {getSortIcon('createdAt')}
                </button>
              </th>
              <th className="px-4 py-3 text-left">
                <button
                  onClick={() => handleSort('duration')}
                  className="flex items-center space-x-1 text-sm font-medium text-text-secondary hover:text-text-primary"
                >
                  <span>Duration</span>
                  {getSortIcon('duration')}
                </button>
              </th>
              <th className="px-4 py-3 text-center">
                <span className="text-sm font-medium text-text-secondary">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {jobs.map((job) => (
              <React.Fragment key={job.id}>
                <tr className="hover:bg-surface-secondary transition-colors">
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedJobs.includes(job.id)}
                      onChange={() => onJobSelect(job.id)}
                      className="w-4 h-4 text-accent border-border rounded focus:ring-accent/20"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toggleRowExpansion(job.id)}
                        className="p-1 hover:bg-surface-secondary rounded"
                      >
                        <Icon 
                          name="ChevronRight" 
                          size={14} 
                          className={`text-text-muted transition-transform ${
                            expandedRows.has(job.id) ? 'rotate-90' : ''
                          }`}
                        />
                      </button>
                      <span className="text-sm font-mono text-text-primary">
                        {job.id}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <Icon 
                        name={getJobTypeIcon(job.type)} 
                        size={16} 
                        className="text-accent"
                      />
                      <span className="text-sm text-text-primary">
                        {job.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {job.targetObjects.slice(0, 2).map((target, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 text-xs bg-accent-100 text-accent-700 rounded"
                        >
                          {target}
                        </span>
                      ))}
                      {job.targetObjects.length > 2 && (
                        <span className="text-xs text-text-muted">
                          +{job.targetObjects.length - 2} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="space-y-1">
                      <JobStatusBadge status={job.status} size="sm" />
                      {job.status === 'running' && (
                        <JobProgressBar 
                          progress={job.progress} 
                          status={job.status} 
                          size="sm" 
                        />
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Icon 
                      name="Circle" 
                      size={8} 
                      className={`${getPriorityColor(job.priority)} mr-2`}
                    />
                    <span className={`text-sm capitalize ${getPriorityColor(job.priority)}`}>
                      {job.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-primary">
                      {formatDateTime(job.createdAt)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-primary">
                      {formatDuration(job.duration)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onJobDetails(job)}
                        iconName="Eye"
                        iconSize={14}
                      />
                      {canCancelJob(job.status) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onJobAction('cancel', job.id)}
                          iconName="Square"
                          iconSize={14}
                        />
                      )}
                      {canRetryJob(job.status) && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onJobAction('retry', job.id)}
                          iconName="RotateCcw"
                          iconSize={14}
                        />
                      )}
                    </div>
                  </td>
                </tr>
                
                {/* Expanded Row Details */}
                {expandedRows.has(job.id) && (
                  <tr>
                    <td colSpan="9" className="px-4 py-3 bg-surface-secondary">
                      <div className="space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h4 className="text-sm font-medium text-text-primary mb-2">
                              Configuration
                            </h4>
                            <div className="text-xs text-text-secondary space-y-1">
                              <div>Sample Size: {job.configuration.sampleSize}</div>
                              <div>Partition Limit: {job.configuration.partitionLimit}</div>
                              <div>Analysis Type: {job.configuration.analysisType}</div>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-sm font-medium text-text-primary mb-2">
                              Resource Usage
                            </h4>
                            <div className="text-xs text-text-secondary space-y-1">
                              <div>CPU: {job.metrics.cpuUsage}%</div>
                              <div>Memory: {job.metrics.memoryUsage}%</div>
                              <div>Records: {job.metrics.recordsProcessed.toLocaleString()}</div>
                            </div>
                          </div>
                        </div>
                        {job.error && (
                          <div>
                            <h4 className="text-sm font-medium text-error mb-2">
                              Error Details
                            </h4>
                            <p className="text-xs text-error bg-error-50 p-2 rounded">
                              {job.error}
                            </p>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card Layout */}
      <div className="lg:hidden space-y-4 p-4">
        {jobs.map((job) => (
          <div key={job.id} className="border border-border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedJobs.includes(job.id)}
                  onChange={() => onJobSelect(job.id)}
                  className="w-4 h-4 text-accent border-border rounded focus:ring-accent/20"
                />
                <span className="text-sm font-mono text-text-primary">
                  {job.id}
                </span>
              </div>
              <JobStatusBadge status={job.status} size="sm" />
            </div>
            
            <div className="flex items-center space-x-2">
              <Icon 
                name={getJobTypeIcon(job.type)} 
                size={16} 
                className="text-accent"
              />
              <span className="text-sm text-text-primary">
                {job.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
              <span className={`text-xs ${getPriorityColor(job.priority)}`}>
                • {job.priority}
              </span>
            </div>
            
            {job.status === 'running' && (
              <JobProgressBar 
                progress={job.progress} 
                status={job.status} 
                size="md" 
              />
            )}
            
            <div className="flex flex-wrap gap-1">
              {job.targetObjects.slice(0, 3).map((target, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 text-xs bg-accent-100 text-accent-700 rounded"
                >
                  {target}
                </span>
              ))}
              {job.targetObjects.length > 3 && (
                <span className="text-xs text-text-muted">
                  +{job.targetObjects.length - 3} more
                </span>
              )}
            </div>
            
            <div className="flex items-center justify-between text-xs text-text-secondary">
              <span>{formatDateTime(job.createdAt)}</span>
              <span>{formatDuration(job.duration)}</span>
            </div>
            
            <div className="flex items-center justify-end space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onJobDetails(job)}
                iconName="Eye"
                iconSize={14}
              >
                Details
              </Button>
              {canCancelJob(job.status) && (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onJobAction('cancel', job.id)}
                  iconName="Square"
                  iconSize={14}
                >
                  Cancel
                </Button>
              )}
              {canRetryJob(job.status) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onJobAction('retry', job.id)}
                  iconName="RotateCcw"
                  iconSize={14}
                >
                  Retry
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default JobTable;