import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';

const SchemaAttachmentModal = ({ isOpen, onClose, onAttach }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [activeTab, setActiveTab] = useState('tables');

  // Mock schema data
  const databases = [
    {
      id: 'ecommerce_prod',
      name: 'ecommerce_prod',
      type: 'postgresql',
      schemas: [
        {
          id: 'public',
          name: 'public',
          tables: [
            { id: 'users', name: 'users', columns: 12, rows: 50000 },
            { id: 'orders', name: 'orders', columns: 8, rows: 125000 },
            { id: 'products', name: 'products', columns: 15, rows: 2500 },
            { id: 'order_items', name: 'order_items', columns: 6, rows: 300000 }
          ]
        }
      ]
    },
    {
      id: 'analytics_db',
      name: 'analytics_db',
      type: 'bigquery',
      schemas: [
        {
          id: 'reporting',
          name: 'reporting',
          tables: [
            { id: 'customer_metrics', name: 'customer_metrics', columns: 20, rows: 45000 },
            { id: 'sales_summary', name: 'sales_summary', columns: 10, rows: 12000 }
          ]
        }
      ]
    }
  ];

  const connections = [
    { id: 'conn1', name: 'Production PostgreSQL', status: 'connected', type: 'postgresql' },
    { id: 'conn2', name: 'Analytics Warehouse', status: 'connected', type: 'bigquery' },
    { id: 'conn3', name: 'Development MySQL', status: 'disconnected', type: 'mysql' }
  ];

  const filteredTables = databases.flatMap(db =>
    db.schemas.flatMap(schema =>
      schema.tables
        .filter(table => 
          table.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          schema.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          db.name.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .map(table => ({
          ...table,
          database: db.name,
          schema: schema.name,
          fullPath: `${db.name}.${schema.name}.${table.name}`
        }))
    )
  );

  const filteredConnections = connections.filter(conn =>
    conn.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleItemToggle = (item) => {
    setSelectedItems(prev => {
      const exists = prev.find(selected => selected.id === item.id);
      if (exists) {
        return prev.filter(selected => selected.id !== item.id);
      } else {
        return [...prev, item];
      }
    });
  };

  const handleAttach = () => {
    onAttach(selectedItems);
    setSelectedItems([]);
    onClose();
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat().format(num);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-300 flex items-center justify-center p-4">
      <div className="bg-surface rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-text-primary">Attach Schema Objects</h2>
          <Button
            variant="ghost"
            onClick={onClose}
            className="p-2"
            aria-label="Close modal"
          >
            <Icon name="X" size={20} className="text-text-secondary" />
          </Button>
        </div>

        {/* Search */}
        <div className="p-6 border-b border-border">
          <Input
            type="search"
            placeholder="Search tables, schemas, or databases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setActiveTab('tables')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors duration-150 ${
              activeTab === 'tables' ?'text-accent border-b-2 border-accent bg-accent/5' :'text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
            }`}
          >
            Tables ({filteredTables.length})
          </button>
          <button
            onClick={() => setActiveTab('connections')}
            className={`flex-1 px-6 py-3 text-sm font-medium transition-colors duration-150 ${
              activeTab === 'connections' ?'text-accent border-b-2 border-accent bg-accent/5' :'text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
            }`}
          >
            Connections ({filteredConnections.length})
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'tables' && (
            <div className="space-y-3">
              {filteredTables.length === 0 ? (
                <div className="text-center py-8 text-text-muted">
                  <Icon name="Search" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>No tables found matching your search</p>
                </div>
              ) : (
                filteredTables.map((table) => {
                  const isSelected = selectedItems.find(item => item.id === table.id);
                  return (
                    <div
                      key={`${table.database}-${table.schema}-${table.id}`}
                      className={`p-4 rounded-lg border cursor-pointer transition-all duration-150 ${
                        isSelected
                          ? 'border-accent bg-accent/5' :'border-border hover:border-accent/50 hover:bg-surface-secondary'
                      }`}
                      onClick={() => handleItemToggle(table)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                            isSelected ? 'border-accent bg-accent' : 'border-border'
                          }`}>
                            {isSelected && (
                              <Icon name="Check" size={12} className="text-accent-foreground" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <Icon name="Table" size={16} className="text-accent" />
                              <span className="font-medium text-text-primary">{table.name}</span>
                            </div>
                            <div className="text-sm text-text-secondary">
                              {table.database}.{table.schema}
                            </div>
                          </div>
                        </div>
                        <div className="text-right text-sm text-text-muted">
                          <div>{table.columns} columns</div>
                          <div>{formatNumber(table.rows)} rows</div>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {activeTab === 'connections' && (
            <div className="space-y-3">
              {filteredConnections.length === 0 ? (
                <div className="text-center py-8 text-text-muted">
                  <Icon name="Database" size={48} className="mx-auto mb-4 opacity-50" />
                  <p>No connections found matching your search</p>
                </div>
              ) : (
                filteredConnections.map((connection) => {
                  const isSelected = selectedItems.find(item => item.id === connection.id);
                  return (
                    <div
                      key={connection.id}
                      className={`p-4 rounded-lg border cursor-pointer transition-all duration-150 ${
                        isSelected
                          ? 'border-accent bg-accent/5' :'border-border hover:border-accent/50 hover:bg-surface-secondary'
                      }`}
                      onClick={() => handleItemToggle(connection)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                            isSelected ? 'border-accent bg-accent' : 'border-border'
                          }`}>
                            {isSelected && (
                              <Icon name="Check" size={12} className="text-accent-foreground" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <Icon name="Database" size={16} className="text-accent" />
                              <span className="font-medium text-text-primary">{connection.name}</span>
                            </div>
                            <div className="text-sm text-text-secondary capitalize">
                              {connection.type}
                            </div>
                          </div>
                        </div>
                        <div className={`flex items-center space-x-1 ${
                          connection.status === 'connected' ? 'text-success' : 'text-error'
                        }`}>
                          <div className="w-2 h-2 rounded-full bg-current"></div>
                          <span className="text-sm font-medium capitalize">
                            {connection.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-border">
          <div className="text-sm text-text-muted">
            {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAttach}
              disabled={selectedItems.length === 0}
            >
              Attach Selected
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchemaAttachmentModal;