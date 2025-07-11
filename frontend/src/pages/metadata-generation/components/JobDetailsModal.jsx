import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const JobDetailsModal = ({ job, isOpen, onClose, onDownloadResults, onRetryJob }) => {
  if (!isOpen || !job) return null;

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

  const formatDuration = (seconds) => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const ProgressBar = ({ progress, status }) => (
    <div className="w-full bg-secondary-100 rounded-full h-3">
      <div 
        className={`h-3 rounded-full transition-all duration-300 ${
          status === 'completed' ? 'bg-success' :
          status === 'failed' ? 'bg-error' :
          status === 'cancelled'? 'bg-secondary' : 'bg-primary'
        }`}
        style={{ width: `${Math.min(progress, 100)}%` }}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-300 flex items-center justify-center p-4">
      <div className="bg-surface rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center space-x-3">
            <Icon name="Activity" size={24} className="text-primary" />
            <div>
              <h2 className="text-xl font-semibold text-text-primary">Job Details</h2>
              <p className="text-sm text-text-secondary">ID: {job.id}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            onClick={onClose}
            className="p-2"
            aria-label="Close modal"
          >
            <Icon name="X" size={20} />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Job Overview */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-4">Job Overview</h3>
                
                {/* Status */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-text-secondary">Status</span>
                    <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(job.status)}`}>
                      <Icon name={getStatusIcon(job.status)} size={14} />
                      <span className="capitalize">{job.status}</span>
                    </div>
                  </div>

                  {/* Progress */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-secondary">Progress</span>
                      <span className="text-sm font-medium text-text-primary">{job.progress}%</span>
                    </div>
                    <ProgressBar progress={job.progress} status={job.status} />
                  </div>

                  {/* Timing */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-sm font-medium text-text-secondary block">Started</span>
                      <span className="text-sm text-text-primary">
                        {new Date(job.startTime).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-text-secondary block">Duration</span>
                      <span className="text-sm text-text-primary">
                        {formatDuration(job.duration)}
                      </span>
                    </div>
                  </div>

                  {job.estimatedTimeRemaining && job.status === 'running' && (
                    <div>
                      <span className="text-sm font-medium text-text-secondary block">Estimated Remaining</span>
                      <span className="text-sm text-text-primary">
                        {formatDuration(job.estimatedTimeRemaining)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Configuration */}
              <div>
                <h4 className="text-md font-semibold text-text-primary mb-3">Configuration</h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">LLM Model</span>
                    <span className="text-text-primary font-medium">{job.configuration.llmModel}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Analysis Depth</span>
                    <span className="text-text-primary font-medium capitalize">{job.configuration.analysisDepth}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Sample Size</span>
                    <span className="text-text-primary font-medium">{job.configuration.sampleSize.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Partition Limit</span>
                    <span className="text-text-primary font-medium">{job.configuration.partitionLimit}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Business Context</span>
                    <span className="text-text-primary font-medium">
                      {job.configuration.includeBusinessContext ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Generate LookML</span>
                    <span className="text-text-primary font-medium">
                      {job.configuration.generateLookML ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Tables and Progress */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-4">Target Tables</h3>
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {job.tableProgress?.map((table, index) => (
                    <div key={index} className="border border-border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <div className="font-medium text-text-primary text-sm">{table.name}</div>
                          <div className="text-xs text-text-secondary">{table.schema}</div>
                        </div>
                        <div className={`inline-flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(table.status)}`}>
                          <Icon name={getStatusIcon(table.status)} size={10} />
                          <span className="capitalize">{table.status}</span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span className="text-text-secondary">Progress</span>
                          <span className="text-text-primary">{table.progress}%</span>
                        </div>
                        <ProgressBar progress={table.progress} status={table.status} />
                      </div>
                      {table.error && (
                        <div className="mt-2 text-xs text-error bg-error-50 p-2 rounded">
                          {table.error}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Logs */}
              {job.logs && job.logs.length > 0 && (
                <div>
                  <h4 className="text-md font-semibold text-text-primary mb-3">Recent Logs</h4>
                  <div className="bg-surface-secondary rounded-lg p-3 max-h-40 overflow-y-auto">
                    <div className="space-y-2 font-mono text-xs">
                      {job.logs.slice(-10).map((log, index) => (
                        <div key={index} className="flex space-x-2">
                          <span className="text-text-muted">{log.timestamp}</span>
                          <span className={`${
                            log.level === 'error' ? 'text-error' :
                            log.level === 'warning'? 'text-warning' : 'text-text-primary'
                          }`}>
                            {log.message}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Error Details */}
          {job.status === 'failed' && job.error && (
            <div className="mt-6 p-4 bg-error-50 border border-error-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <Icon name="AlertCircle" size={20} className="text-error mt-0.5" />
                <div>
                  <h4 className="text-md font-semibold text-error mb-2">Error Details</h4>
                  <p className="text-sm text-error-700">{job.error}</p>
                  {job.errorDetails && (
                    <details className="mt-2">
                      <summary className="text-xs font-medium text-error cursor-pointer">Show technical details</summary>
                      <pre className="mt-2 text-xs bg-surface-tertiary p-3 rounded overflow-x-auto">
                        {job.errorDetails}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-border flex items-center justify-between">
          {job.status === 'completed' ? (
            <Button 
              variant="primary" 
              onClick={onDownloadResults}
              className="flex items-center space-x-2"
            >
              <Icon name="Download" size={16} />
              <span>Download Results</span>
            </Button>
          ) : job.status === 'failed' ? (
            <Button 
              variant="primary" 
              onClick={onRetryJob}
              className="flex items-center space-x-2"
            >
              <Icon name="RefreshCw" size={16} />
              <span>Retry Job</span>
            </Button>
          ) : (
            <div></div> // Empty div for spacing in running/queued states
          )}
          
          <Button 
            variant="secondary" 
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );
};

export default JobDetailsModal;