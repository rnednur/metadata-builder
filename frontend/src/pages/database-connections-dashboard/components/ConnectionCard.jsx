import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ConnectionCard = ({ connection, onConnect, onEdit, onDelete, onConfigureSchemas }) => {
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

  return (
    <div className="bg-surface border border-border rounded-lg p-6 hover:shadow-md transition-all duration-200 hover-lift">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
            <Icon 
              name={getDatabaseIcon(connection.type)} 
              size={20} 
              className="text-primary"
            />
          </div>
          <div>
            <h3 className="font-semibold text-text-primary text-lg">{connection.name}</h3>
            <p className="text-sm text-text-secondary capitalize">{connection.type}</p>
          </div>
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(connection.status)}`}>
          {connection.status}
        </span>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-text-secondary">
          <Icon name="Server" size={14} className="mr-2" />
          <span className="truncate">{connection.host}:{connection.port}</span>
        </div>
        <div className="flex items-center text-sm text-text-secondary">
          <Icon name="Database" size={14} className="mr-2" />
          <span className="truncate">{connection.database}</span>
        </div>
        <div className="flex items-center text-sm text-text-secondary">
          <Icon name="Clock" size={14} className="mr-2" />
          <span>Last used: {formatLastUsed(connection.lastUsed)}</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="flex space-x-2">
          <Button
            variant="primary"
            onClick={() => onConnect(connection)}
            disabled={connection.status === 'connecting'}
            className="text-sm px-3 py-1.5"
          >
            {connection.status === 'connecting' ? 'Connecting...' : 'Connect'}
          </Button>
          <Button
            variant="ghost"
            onClick={() => onConfigureSchemas(connection)}
            className="text-sm px-3 py-1.5"
            title="Configure Schema Filtering"
          >
            <Icon name="Filter" size={14} />
          </Button>
          <Button
            variant="ghost"
            onClick={() => onEdit(connection)}
            className="text-sm px-3 py-1.5"
          >
            <Icon name="Edit" size={14} />
          </Button>
        </div>
        <Button
          variant="ghost"
          onClick={() => onDelete(connection)}
          className="text-sm px-3 py-1.5 text-error hover:bg-error/10"
        >
          <Icon name="Trash2" size={14} />
        </Button>
      </div>
    </div>
  );
};

export default ConnectionCard;