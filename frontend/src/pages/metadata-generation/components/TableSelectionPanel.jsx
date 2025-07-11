import React, { useState, useMemo, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';
import { metadataAPI } from '../../../services/api';

const TableSelectionPanel = ({ 
  databases, 
  selectedTables, 
  onTableSelectionChange,
  onSelectAll,
  onClearAll 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedDatabases, setExpandedDatabases] = useState(new Set());
  const [expandedSchemas, setExpandedSchemas] = useState(new Set());
  const [tablesWithMetadata, setTablesWithMetadata] = useState(new Set());

  // Load tables with metadata when databases change
  useEffect(() => {
    if (databases && databases.length > 0) {
      databases.forEach(database => {
        loadTablesWithMetadata(database.name);
      });
    }
  }, [databases]);

  // Listen for metadata generation events to refresh indicators
  useEffect(() => {
    const handleMetadataGenerated = (event) => {
      const { database, schema, table } = event.detail;
      const tableId = `${database}_${schema}_${table}`;
      
      // Add the new table to the set of tables with metadata
      setTablesWithMetadata(prev => new Set([...prev, tableId]));
      console.log(`Updated metadata indicator for ${tableId}`);
    };

    window.addEventListener('metadataGenerated', handleMetadataGenerated);
    
    return () => {
      window.removeEventListener('metadataGenerated', handleMetadataGenerated);
    };
  }, []);

  // Load list of tables that have stored metadata
  const loadTablesWithMetadata = async (databaseName) => {
    try {
      const response = await metadataAPI.listTablesWithMetadata(databaseName);
      const tables = response.data?.tables || [];
      
      // Create a set of table identifiers that have metadata
      const tableIds = new Set(
        tables.map(table => `${databaseName}_${table.schema_name}_${table.table_name}`)
      );
      
      setTablesWithMetadata(prev => new Set([...prev, ...tableIds]));
      console.log('Loaded tables with metadata:', tableIds);
    } catch (err) {
      console.warn('Error loading tables with metadata:', err);
      // Don't fail the whole operation if this fails
    }
  };

  const filteredDatabases = useMemo(() => {
    if (!searchQuery.trim()) return databases;
    
    return databases.map(db => ({
      ...db,
      schemas: db.schemas.map(schema => ({
        ...schema,
        tables: schema.tables.filter(table => 
          table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          schema.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          db.name.toLowerCase().includes(searchQuery.toLowerCase())
        )
      })).filter(schema => schema.tables.length > 0)
    })).filter(db => db.schemas.length > 0);
  }, [databases, searchQuery]);

  const totalTables = useMemo(() => {
    return databases.reduce((total, db) => 
      total + db.schemas.reduce((schemaTotal, schema) => 
        schemaTotal + schema.tables.length, 0), 0);
  }, [databases]);

  const selectedCount = selectedTables.length;

  const toggleDatabase = (dbId) => {
    const newExpanded = new Set(expandedDatabases);
    if (newExpanded.has(dbId)) {
      newExpanded.delete(dbId);
    } else {
      newExpanded.add(dbId);
    }
    setExpandedDatabases(newExpanded);
  };

  const toggleSchema = (schemaId) => {
    const newExpanded = new Set(expandedSchemas);
    if (newExpanded.has(schemaId)) {
      newExpanded.delete(schemaId);
    } else {
      newExpanded.add(schemaId);
    }
    setExpandedSchemas(newExpanded);
  };

  const isTableSelected = (tableId) => {
    return selectedTables.some(table => table.id === tableId);
  };

  const handleTableToggle = (table) => {
    onTableSelectionChange(table);
  };

  const getSchemaSelectedCount = (schema) => {
    return schema.tables.filter(table => isTableSelected(table.id)).length;
  };

  const isDatabaseFullySelected = (database) => {
    const allTables = database.schemas.flatMap(schema => schema.tables);
    return allTables.length > 0 && allTables.every(table => isTableSelected(table.id));
  };

  const isSchemaFullySelected = (schema) => {
    return schema.tables.length > 0 && schema.tables.every(table => isTableSelected(table.id));
  };

  return (
    <div className="bg-surface border border-border rounded-lg h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-text-primary">Table Selection</h3>
          <div className="text-sm text-text-secondary">
            {selectedCount} of {totalTables} selected
          </div>
        </div>
        
        {/* Search */}
        <div className="relative">
          <Icon 
            name="Search" 
            size={16} 
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-muted"
          />
          <Input
            type="search"
            placeholder="Search databases, schemas, tables..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Bulk Actions */}
        <div className="flex items-center space-x-2 mt-3">
          <Button
            variant="outline"
            onClick={onSelectAll}
            className="text-xs"
          >
            Select All
          </Button>
          <Button
            variant="outline"
            onClick={onClearAll}
            className="text-xs"
          >
            Clear All
          </Button>
        </div>
      </div>

      {/* Tree View */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredDatabases.length === 0 ? (
          <div className="text-center py-8 text-text-muted">
            <Icon name="Database" size={48} className="mx-auto mb-3 opacity-50" />
            <p>No tables found matching your search</p>
          </div>
        ) : (
          <div className="space-y-2">
            {filteredDatabases.map((database) => (
              <div key={database.id} className="border border-border rounded-lg">
                {/* Database Header */}
                <div 
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-secondary transition-colors"
                  onClick={() => toggleDatabase(database.id)}
                >
                  <div className="flex items-center space-x-3">
                    <Icon 
                      name="ChevronRight" 
                      size={16} 
                      className={`transition-transform ${
                        expandedDatabases.has(database.id) ? 'rotate-90' : ''
                      }`}
                    />
                    <Icon name="Database" size={18} className="text-primary" />
                    <div>
                      <div className="font-medium text-text-primary">{database.name}</div>
                      <div className="text-xs text-text-secondary">{database.type}</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      database.status === 'connected' ? 'bg-success' : 'bg-error'
                    }`}></div>
                    {isDatabaseFullySelected(database) && (
                      <Icon name="CheckCircle" size={16} className="text-success" />
                    )}
                  </div>
                </div>

                {/* Schemas */}
                {expandedDatabases.has(database.id) && (
                  <div className="border-t border-border bg-surface-secondary/50">
                    {database.schemas.map((schema) => (
                      <div key={schema.id} className="border-b border-border last:border-b-0">
                        {/* Schema Header */}
                        <div 
                          className="flex items-center justify-between p-3 pl-8 cursor-pointer hover:bg-surface-secondary transition-colors"
                          onClick={() => toggleSchema(schema.id)}
                        >
                          <div className="flex items-center space-x-3">
                            <Icon 
                              name="ChevronRight" 
                              size={14} 
                              className={`transition-transform ${
                                expandedSchemas.has(schema.id) ? 'rotate-90' : ''
                              }`}
                            />
                            <Icon name="Folder" size={16} className="text-accent" />
                            <span className="font-medium text-text-primary">{schema.name}</span>
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs text-text-secondary">
                              {getSchemaSelectedCount(schema)}/{schema.tables.length}
                            </span>
                            {isSchemaFullySelected(schema) && (
                              <Icon name="CheckCircle" size={14} className="text-success" />
                            )}
                          </div>
                        </div>

                        {/* Tables */}
                        {expandedSchemas.has(schema.id) && (
                          <div className="bg-surface">
                            {schema.tables.map((table) => (
                              <div 
                                key={table.id}
                                className="flex items-center justify-between p-3 pl-16 hover:bg-surface-secondary transition-colors cursor-pointer"
                                onClick={() => handleTableToggle(table)}
                              >
                                <div className="flex items-center space-x-3">
                                  <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                                    isTableSelected(table.id)
                                      ? 'bg-primary border-primary' :'border-border hover:border-primary'
                                  }`}>
                                    {isTableSelected(table.id) && (
                                      <Icon name="Check" size={12} className="text-primary-foreground" />
                                    )}
                                  </div>
                                  <Icon name="Table" size={16} className="text-text-muted" />
                                  <div>
                                    <div className="font-medium text-text-primary">{table.name}</div>
                                    <div className="text-xs text-text-secondary">
                                      {table.rowCount?.toLocaleString()} rows • {table.columnCount} columns
                                    </div>
                                  </div>
                                </div>
                                <div className="text-xs text-text-muted">
                                  {(() => {
                                    // Convert table.id format to metadata ID format
                                    // table.id is "schema.table", but metadata uses "database_schema_table"
                                    const metadataId = `${database.name}_${schema.name}_${table.name}`;
                                    return tablesWithMetadata.has(metadataId) ? (
                                      <div className="flex items-center space-x-1">
                                        <Icon name="Sparkles" size={12} className="text-accent" />
                                        <span className="text-accent font-medium">Analyzed</span>
                                      </div>
                                    ) : (
                                      'Not analyzed'
                                    );
                                  })()}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TableSelectionPanel;