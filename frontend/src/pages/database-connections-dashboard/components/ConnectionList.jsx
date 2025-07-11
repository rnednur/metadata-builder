import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ConnectionList = ({ connections, onConnect, onEdit, onDelete, onConfigureSchemas }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'bg-success text-success-foreground';
      case 'disconnected':
        return 'bg-error text-error-foreground';
      case 'connecting':
        return 'bg-warning text-warning-foreground';
      default:
        return 'bg-secondary text-secondary-foreground';
    }
  };

  const getDatabaseIcon = (type) => {
    const iconMap = {
      postgresql: 'Database',
      mysql: 'Database',
      sqlite: 'HardDrive',
      oracle: 'Server',
      bigquery: 'Cloud',
      kinetica: 'Zap',
      duckdb: 'Database'
    };
    return iconMap[type] || 'Database';
  };

  const formatLastUsed = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  if (connections.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-8 text-center">
        <Icon name="Database" size={48} className="text-text-muted mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-text-primary mb-2">No connections found</h3>
        <p className="text-text-secondary">Create your first database connection to get started.</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      {/* Table Header */}
      <div className="bg-surface-secondary border-b border-border px-6 py-3">
        <div className="grid grid-cols-12 gap-4 text-sm font-medium text-text-secondary">
          <div className="col-span-4">Connection</div>
          <div className="col-span-2">Type</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Last Used</div>
          <div className="col-span-2">Actions</div>
        </div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-border">
        {connections.map((connection) => (
          <div key={connection.id} className="px-6 py-4 hover:bg-surface-secondary transition-colors duration-150">
            <div className="grid grid-cols-12 gap-4 items-center">
              {/* Connection Info */}
              <div className="col-span-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Icon 
                      name={getDatabaseIcon(connection.type)} 
                      size={16} 
                      className="text-primary"
                    />
                  </div>
                  <div className="min-w-0">
                    <h3 className="font-medium text-text-primary truncate">{connection.name}</h3>
                    <p className="text-sm text-text-secondary truncate">
                      {connection.host}:{connection.port}/{connection.database}
                    </p>
                  </div>
                </div>
              </div>

              {/* Type */}
              <div className="col-span-2">
                <span className="text-sm text-text-secondary capitalize">{connection.type}</span>
              </div>

              {/* Status */}
              <div className="col-span-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
                  {connection.status}
                </span>
              </div>

              {/* Last Used */}
              <div className="col-span-2">
                <span className="text-sm text-text-secondary">{formatLastUsed(connection.lastUsed)}</span>
              </div>

              {/* Actions */}
              <div className="col-span-2">
                <div className="flex items-center space-x-2">
                  <Button
                    variant="primary"
                    onClick={() => onConnect(connection)}
                    disabled={connection.status === 'connecting'}
                    className="text-xs px-3 py-1.5"
                  >
                    {connection.status === 'connecting' ? 'Connecting...' : 'Connect'}
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => onConfigureSchemas(connection)}
                    className="text-xs px-2 py-1.5"
                    title="Configure Schema Filtering"
                  >
                    <Icon name="Filter" size={14} />
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => onEdit(connection)}
                    className="text-xs px-2 py-1.5"
                  >
                    <Icon name="Edit" size={14} />
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => onDelete(connection)}
                    className="text-xs px-2 py-1.5 text-error hover:bg-error/10"
                  >
                    <Icon name="Trash2" size={14} />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConnectionList;