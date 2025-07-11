import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import JobStatusBadge from './JobStatusBadge';
import JobProgressBar from './JobProgressBar';

const JobDetailsModal = ({ job, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');

  if (!isOpen || !job) return null;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: 'Info' },
    { id: 'logs', label: 'Logs', icon: 'FileText' },
    { id: 'metrics', label: 'Metrics', icon: 'BarChart3' },
    { id: 'config', label: 'Configuration', icon: 'Settings' }
  ];

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Job ID
            </label>
            <p className="text-sm font-mono text-text-primary bg-surface-secondary px-3 py-2 rounded">
              {job.id}
            </p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Status
            </label>
            <JobStatusBadge status={job.status} />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Progress
            </label>
            <JobProgressBar progress={job.progress} status={job.status} size="lg" />
          </div>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Type
            </label>
            <p className="text-sm text-text-primary">{job.type}</p>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Priority
            </label>
            <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
              job.priority === 'high' ? 'bg-error-100 text-error-700' :
              job.priority === 'medium'? 'bg-warning-100 text-warning-700' : 'bg-success-100 text-success-700'
            }`}>
              {job.priority}
            </span>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Duration
            </label>
            <p className="text-sm text-text-primary">{formatDuration(job.duration)}</p>
          </div>
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          Target Objects
        </label>
        <div className="bg-surface-secondary rounded-lg p-3">
          <div className="flex flex-wrap gap-2">
            {job.targetObjects.map((target, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-1 text-xs bg-accent-100 text-accent-700 rounded"
              >
                {target}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      {job.error && (
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Error Details
          </label>
          <div className="bg-error-50 border border-error-200 rounded-lg p-3">
            <p className="text-sm text-error-700">{job.error}</p>
          </div>
        </div>
      )}
    </div>
  );

  const renderLogs = () => (
    <div className="space-y-4">
      <div className="bg-surface-secondary rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
        {job.logs.map((log, index) => (
          <div key={index} className="mb-2 last:mb-0">
            <span className="text-text-muted">[{log.timestamp}]</span>
            <span className={`ml-2 ${
              log.level === 'error' ? 'text-error' :
              log.level === 'warning' ? 'text-warning' :
              log.level === 'info'? 'text-accent' : 'text-text-primary'
            }`}>
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="space-y-4">
        <h4 className="font-medium text-text-primary">Resource Usage</h4>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-secondary">CPU Usage</span>
              <span className="text-text-primary">{job.metrics.cpuUsage}%</span>
            </div>
            <div className="w-full bg-secondary-100 rounded-full h-2">
              <div 
                className="bg-accent h-2 rounded-full" 
                style={{ width: `${job.metrics.cpuUsage}%` }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-text-secondary">Memory Usage</span>
              <span className="text-text-primary">{job.metrics.memoryUsage}%</span>
            </div>
            <div className="w-full bg-secondary-100 rounded-full h-2">
              <div 
                className="bg-warning h-2 rounded-full" 
                style={{ width: `${job.metrics.memoryUsage}%` }}
              />
            </div>
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        <h4 className="font-medium text-text-primary">Performance</h4>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-text-secondary">Records Processed</span>
            <span className="text-sm text-text-primary">{job.metrics.recordsProcessed.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-text-secondary">Processing Rate</span>
            <span className="text-sm text-text-primary">{job.metrics.processingRate}/sec</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-text-secondary">Data Size</span>
            <span className="text-sm text-text-primary">{job.metrics.dataSize}</span>
          </div>
        </div>
      </div>
    </div>
  );

  const renderConfiguration = () => (
    <div className="space-y-4">
      <div className="bg-surface-secondary rounded-lg p-4">
        <pre className="text-sm text-text-primary whitespace-pre-wrap">
          {JSON.stringify(job.configuration, null, 2)}
        </pre>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'logs':
        return renderLogs();
      case 'metrics':
        return renderMetrics();
      case 'config':
        return renderConfiguration();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-200 flex items-center justify-center p-4">
      <div className="bg-surface rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">
              Job Details
            </h2>
            <p className="text-sm text-text-secondary mt-1">
              {job.type} • Created {job.createdAt}
            </p>
          </div>
          <Button
            variant="ghost"
            onClick={onClose}
            iconName="X"
            iconSize={20}
          />
        </div>

        {/* Tabs */}
        <div className="border-b border-border">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-accent text-accent' :'border-transparent text-text-secondary hover:text-text-primary'
                }`}
              >
                <Icon name={tab.icon} size={16} />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {renderTabContent()}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-border">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          {job.status === 'running' && (
            <Button variant="danger" iconName="Square">
              Cancel Job
            </Button>
          )}
          {job.status === 'failed' && (
            <Button variant="primary" iconName="RotateCcw">
              Retry Job
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobDetailsModal;