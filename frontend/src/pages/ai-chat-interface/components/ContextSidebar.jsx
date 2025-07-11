import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ContextSidebar = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('context');

  // Mock data for referenced objects
  const referencedTables = [
    {
      id: 1,
      database: 'ecommerce_prod',
      schema: 'public',
      table: 'users',
      columns: ['id', 'email', 'created_at', 'last_login'],
      lastReferenced: new Date(Date.now() - 300000)
    },
    {
      id: 2,
      database: 'ecommerce_prod',
      schema: 'public',
      table: 'orders',
      columns: ['id', 'user_id', 'total_amount', 'status'],
      lastReferenced: new Date(Date.now() - 600000)
    },
    {
      id: 3,
      database: 'analytics_db',
      schema: 'reporting',
      table: 'customer_metrics',
      columns: ['customer_id', 'lifetime_value', 'churn_risk'],
      lastReferenced: new Date(Date.now() - 900000)
    }
  ];

  const activeConnections = [
    {
      id: 1,
      name: 'Production PostgreSQL',
      type: 'postgresql',
      status: 'connected',
      databases: ['ecommerce_prod', 'user_analytics'],
      lastActivity: new Date(Date.now() - 120000)
    },
    {
      id: 2,
      name: 'Analytics Warehouse',
      type: 'bigquery',
      status: 'connected',
      databases: ['analytics_db', 'ml_features'],
      lastActivity: new Date(Date.now() - 300000)
    },
    {
      id: 3,
      name: 'Development MySQL',
      type: 'mysql',
      status: 'disconnected',
      databases: ['dev_ecommerce'],
      lastActivity: new Date(Date.now() - 3600000)
    }
  ];

  const conversationHistory = [
    {
      id: 1,
      title: 'User table analysis',
      timestamp: new Date(Date.now() - 1800000),
      messageCount: 12,
      isBookmarked: true
    },
    {
      id: 2,
      title: 'Order processing workflow',
      timestamp: new Date(Date.now() - 3600000),
      messageCount: 8,
      isBookmarked: false
    },
    {
      id: 3,
      title: 'Customer segmentation queries',
      timestamp: new Date(Date.now() - 7200000),
      messageCount: 15,
      isBookmarked: true
    }
  ];

  const formatTimestamp = (date) => {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const getConnectionStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'text-success';
      case 'connecting':
        return 'text-warning';
      case 'disconnected':
        return 'text-error';
      default:
        return 'text-text-muted';
    }
  };

  const getConnectionIcon = (type) => {
    const iconMap = {
      postgresql: 'Database',
      mysql: 'Database',
      bigquery: 'Cloud',
      sqlite: 'HardDrive',
      oracle: 'Server'
    };
    return iconMap[type] || 'Database';
  };

  const handleTableClick = (table) => {
    navigate('/schema-explorer', { 
      state: { 
        database: table.database, 
        schema: table.schema, 
        table: table.table 
      } 
    });
  };

  const handleConnectionClick = (connection) => {
    navigate('/database-connections-dashboard');
  };

  const tabs = [
    { id: 'context', label: 'Context', icon: 'Layers' },
    { id: 'connections', label: 'Connections', icon: 'Database' },
    { id: 'history', label: 'History', icon: 'Clock' }
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-150 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-16 right-0 h-[calc(100vh-4rem)] w-80 bg-surface border-l border-border z-200
        transform transition-transform duration-300 ease-out
        lg:relative lg:top-0 lg:h-full lg:translate-x-0 lg:z-auto
        ${isOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border">
            <h2 className="text-lg font-semibold text-text-primary">Context</h2>
            <Button
              variant="ghost"
              onClick={onClose}
              className="p-2 lg:hidden"
              aria-label="Close context sidebar"
            >
              <Icon name="X" size={20} className="text-text-secondary" />
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-border">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 text-sm font-medium transition-colors duration-150 ${
                  activeTab === tab.id
                    ? 'text-accent border-b-2 border-accent bg-accent/5' :'text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
                }`}
              >
                <Icon name={tab.icon} size={16} />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'context' && (
              <div className="p-4 space-y-6">
                {/* Referenced Tables */}
                <div>
                  <h3 className="text-sm font-medium text-text-primary mb-3">Referenced Tables</h3>
                  <div className="space-y-3">
                    {referencedTables.map((table) => (
                      <div
                        key={table.id}
                        className="p-3 bg-surface-secondary rounded-lg border border-border hover:border-accent/50 transition-colors duration-150 cursor-pointer"
                        onClick={() => handleTableClick(table)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <Icon name="Table" size={14} className="text-accent" />
                            <span className="text-sm font-medium text-text-primary">
                              {table.table}
                            </span>
                          </div>
                          <span className="text-xs text-text-muted">
                            {formatTimestamp(table.lastReferenced)}
                          </span>
                        </div>
                        <div className="text-xs text-text-secondary mb-2">
                          {table.database}.{table.schema}
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {table.columns.slice(0, 3).map((column) => (
                            <span
                              key={column}
                              className="px-2 py-1 text-xs bg-accent/10 text-accent rounded"
                            >
                              {column}
                            </span>
                          ))}
                          {table.columns.length > 3 && (
                            <span className="px-2 py-1 text-xs bg-secondary-100 text-text-muted rounded">
                              +{table.columns.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div>
                  <h3 className="text-sm font-medium text-text-primary mb-3">Quick Actions</h3>
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      onClick={() => navigate('/schema-explorer')}
                      className="w-full justify-start"
                      iconName="Search"
                      iconPosition="left"
                    >
                      Explore Schema
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => navigate('/metadata-generation')}
                      className="w-full justify-start"
                      iconName="Sparkles"
                      iconPosition="left"
                    >
                      Generate Metadata
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'connections' && (
              <div className="p-4">
                <div className="space-y-3">
                  {activeConnections.map((connection) => (
                    <div
                      key={connection.id}
                      className="p-3 bg-surface-secondary rounded-lg border border-border hover:border-accent/50 transition-colors duration-150 cursor-pointer"
                      onClick={() => handleConnectionClick(connection)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Icon 
                            name={getConnectionIcon(connection.type)} 
                            size={14} 
                            className="text-accent" 
                          />
                          <span className="text-sm font-medium text-text-primary">
                            {connection.name}
                          </span>
                        </div>
                        <div className={`flex items-center space-x-1 ${getConnectionStatusColor(connection.status)}`}>
                          <div className="w-2 h-2 rounded-full bg-current"></div>
                          <span className="text-xs font-medium capitalize">
                            {connection.status}
                          </span>
                        </div>
                      </div>
                      <div className="text-xs text-text-secondary mb-2">
                        {connection.databases.join(', ')}
                      </div>
                      <div className="text-xs text-text-muted">
                        Last activity: {formatTimestamp(connection.lastActivity)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'history' && (
              <div className="p-4">
                <div className="space-y-3">
                  {conversationHistory.map((conversation) => (
                    <div
                      key={conversation.id}
                      className="p-3 bg-surface-secondary rounded-lg border border-border hover:border-accent/50 transition-colors duration-150 cursor-pointer"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-text-primary truncate">
                          {conversation.title}
                        </span>
                        <Button
                          variant="ghost"
                          className="p-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Toggle bookmark
                          }}
                        >
                          <Icon 
                            name={conversation.isBookmarked ? 'Bookmark' : 'BookmarkPlus'} 
                            size={14} 
                            className={conversation.isBookmarked ? 'text-warning' : 'text-text-muted'}
                          />
                        </Button>
                      </div>
                      <div className="flex items-center justify-between text-xs text-text-muted">
                        <span>{conversation.messageCount} messages</span>
                        <span>{formatTimestamp(conversation.timestamp)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};

export default ContextSidebar;