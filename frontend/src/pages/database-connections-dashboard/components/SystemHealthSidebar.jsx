import React from 'react';
import Icon from '../../../components/AppIcon';

const SystemHealthSidebar = ({ isCollapsed, onToggle, healthMetrics }) => {
  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-success';
      case 'warning':
        return 'text-warning';
      case 'error':
        return 'text-error';
      default:
        return 'text-text-muted';
    }
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'healthy':
        return 'CheckCircle';
      case 'warning':
        return 'AlertTriangle';
      case 'error':
        return 'XCircle';
      default:
        return 'Circle';
    }
  };

  if (isCollapsed) {
    return (
      <div className="fixed top-20 right-4 z-50">
        <button
          onClick={onToggle}
          className="bg-surface border border-border rounded-lg p-3 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          <Icon name="BarChart3" size={20} className="text-text-secondary" />
        </button>
      </div>
    );
  }

  return (
    <div className="fixed top-20 right-4 w-80 bg-surface border border-border rounded-lg shadow-lg z-50 max-h-[calc(100vh-6rem)] overflow-y-auto">
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-text-primary">System Health</h3>
          <button
            onClick={onToggle}
            className="p-1 hover:bg-secondary-100 rounded transition-colors duration-150"
          >
            <Icon name="X" size={16} className="text-text-secondary" />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Active Connections */}
        <div className="bg-surface-secondary rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text-primary">Active Connections</span>
            <div className={`flex items-center space-x-1 ${getHealthColor(healthMetrics.connections.status)}`}>
              <Icon name={getHealthIcon(healthMetrics.connections.status)} size={14} />
              <span className="text-sm font-medium">
                {healthMetrics.connections.active}/{healthMetrics.connections.total}
              </span>
            </div>
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div 
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${(healthMetrics.connections.active / healthMetrics.connections.total) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="bg-surface-secondary rounded-lg p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-text-primary">Recent Jobs</span>
            <span className="text-xs text-text-secondary">{healthMetrics.jobs.length} jobs</span>
          </div>
          <div className="space-y-2">
            {healthMetrics.jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Icon 
                    name={getHealthIcon(job.status)} 
                    size={12} 
                    className={getHealthColor(job.status)}
                  />
                  <span className="text-xs text-text-secondary truncate max-w-32">
                    {job.name}
                  </span>
                </div>
                <span className="text-xs text-text-muted">{job.duration}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Status */}
        <div className="bg-surface-secondary rounded-lg p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-text-primary">Agent Status</span>
            <div className={`flex items-center space-x-1 ${getHealthColor(healthMetrics.agents.status)}`}>
              <div className="w-2 h-2 rounded-full bg-current"></div>
              <span className="text-xs font-medium">{healthMetrics.agents.status}</span>
            </div>
          </div>
          <div className="space-y-2">
            {healthMetrics.agents.list.map((agent) => (
              <div key={agent.id} className="flex items-center justify-between">
                <span className="text-xs text-text-secondary">{agent.name}</span>
                <div className="flex items-center space-x-1">
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    agent.status === 'online' ? 'bg-success' : 'bg-error'
                  }`}></div>
                  <span className="text-xs text-text-muted">{agent.responseTime}ms</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Resources */}
        <div className="bg-surface-secondary rounded-lg p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-text-primary">System Resources</span>
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-secondary">CPU Usage</span>
                <span className="text-xs text-text-muted">{healthMetrics.resources.cpu}%</span>
              </div>
              <div className="w-full bg-border rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    healthMetrics.resources.cpu > 80 ? 'bg-error' : 
                    healthMetrics.resources.cpu > 60 ? 'bg-warning' : 'bg-success'
                  }`}
                  style={{ width: `${healthMetrics.resources.cpu}%` }}
                ></div>
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-text-secondary">Memory Usage</span>
                <span className="text-xs text-text-muted">{healthMetrics.resources.memory}%</span>
              </div>
              <div className="w-full bg-border rounded-full h-1.5">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    healthMetrics.resources.memory > 80 ? 'bg-error' : 
                    healthMetrics.resources.memory > 60 ? 'bg-warning' : 'bg-success'
                  }`}
                  style={{ width: `${healthMetrics.resources.memory}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemHealthSidebar;