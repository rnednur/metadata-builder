import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';
import { databaseAPI, metadataAPI } from '../../../services/api';

const SchemaTree = ({ onTableSelect, selectedTable, selectedTables, searchQuery, onSearchChange, selectedConnection, onToggleCollapse, enableMultiSelect = false }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [loadingNodes, setLoadingNodes] = useState(new Set());
  const [databases, setDatabases] = useState([]);
  const [schemasCache, setSchemasCache] = useState({});
  const [tablesCache, setTablesCache] = useState({});
  const [tablesWithMetadata, setTablesWithMetadata] = useState(new Set());
  const [predefinedSchemasDbs, setPredefinedSchemasDbs] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load database connections on component mount and when selectedConnection changes
  useEffect(() => {
    loadDatabases();
  }, [selectedConnection]);

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

  const loadDatabases = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await databaseAPI.listConnections();
      const connections = response.data || response; // Handle both axios response and direct data
      
      console.log('Loaded connections:', connections); // Debug log
      
      // Transform connections to database format
      let dbList = connections.map(conn => ({
        id: conn.name,
        name: conn.name,
        type: conn.type,
        schemas: null // Will be loaded on demand
      }));
      
      // Filter to selected connection if specified
      if (selectedConnection) {
        dbList = dbList.filter(db => db.name === selectedConnection);
        
        // If the selected connection is found, auto-expand it and load metadata info
        if (dbList.length > 0) {
          const connectionId = dbList[0].id;
          // Auto-expand the selected connection
          setTimeout(() => {
            setExpandedNodes(prev => new Set([...prev, connectionId]));
            loadSchemas(dbList[0].name);
            loadTablesWithMetadata(dbList[0].name);
          }, 100);
        }
      }
      
      setDatabases(dbList);
    } catch (err) {
      console.error('Error loading databases:', err);
      setError(`Failed to load database connections: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

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

  const loadSchemas = async (databaseName) => {
    try {
      setLoadingNodes(prev => new Set(prev).add(databaseName));
      
      const response = await databaseAPI.getSchemas(databaseName);
      const schemasData = response.data || response;
      
      console.log('Loaded schemas for', databaseName, ':', schemasData); // Debug log
      console.log('Schema response type:', typeof schemasData, 'Array?', Array.isArray(schemasData));
      console.log('Schema source:', schemasData.schema_source, 'Predefined:', schemasData.uses_predefined_schemas);
      
      // Handle DatabaseSchemaResponse format
      let schemas = [];
      if (schemasData.schemas && Array.isArray(schemasData.schemas)) {
        // Response is DatabaseSchemaResponse with schemas array of SchemaInfo objects
        schemas = schemasData.schemas.map(schemaInfo => ({
          id: `${databaseName}_${schemaInfo.schema_name}`,
          name: schemaInfo.schema_name,
          databaseName: databaseName,
          tableCount: schemaInfo.table_count,
          tables: schemaInfo.tables || null // Pre-loaded table names, if available
        }));
      } else if (Array.isArray(schemasData)) {
        // Fallback: Direct array of schema names
        schemas = schemasData.map(schemaName => ({
          id: `${databaseName}_${schemaName}`,
          name: schemaName,
          databaseName: databaseName,
          tables: null
        }));
      } else {
        console.warn('Unexpected schema response format:', schemasData);
        schemas = [];
      }
      
      // If no schemas were found, provide helpful feedback
      if (schemas.length === 0) {
        console.log('No schemas found for', databaseName);
        if (schemasData.total_tables === 0) {
          console.log('This might be due to:');
          console.log('1. No schemas available in the database');
          console.log('2. Insufficient permissions to list schemas');
          console.log('3. Need to configure predefined schemas in connection settings');
        }
      }
      
      setSchemasCache(prev => ({
        ...prev,
        [databaseName]: schemas
      }));
      
      // Track if this database is using predefined schemas
      if (schemasData.uses_predefined_schemas) {
        setPredefinedSchemasDbs(prev => new Set([...prev, databaseName]));
      } else {
        setPredefinedSchemasDbs(prev => {
          const newSet = new Set(prev);
          newSet.delete(databaseName);
          return newSet;
        });
      }
      
      // Load metadata status for this database whenever schemas are loaded
      loadTablesWithMetadata(databaseName);
      
      return schemas;
    } catch (err) {
      console.error('Error loading schemas:', err);
      setError(`Failed to load schemas for ${databaseName}: ${err.message}`);
      return [];
    } finally {
      setLoadingNodes(prev => {
        const newLoading = new Set(prev);
        newLoading.delete(databaseName);
        return newLoading;
      });
    }
  };

  const loadTables = async (databaseName, schemaName) => {
    try {
      const cacheKey = `${databaseName}_${schemaName}`;
      setLoadingNodes(prev => new Set(prev).add(cacheKey));
      
      const response = await databaseAPI.getTables(databaseName, schemaName);
      const tablesData = response.data || response;
      
      console.log('Loaded tables for', databaseName, schemaName, ':', tablesData); // Debug log
      
      // Handle TableListResponse format
      let tables = [];
      if (tablesData.tables && Array.isArray(tablesData.tables)) {
        // Response is TableListResponse with tables array of TableInfo objects
        tables = tablesData.tables.map(tableInfo => ({
          id: `${databaseName}_${schemaName}_${tableInfo.table_name}`,
          name: tableInfo.table_name,
          type: 'table', // Could be enhanced to detect views
          databaseName: databaseName,
          schemaName: schemaName,
          rowCount: tableInfo.row_count,
          columnCount: tableInfo.column_count,
          columns: tableInfo.columns || {}
        }));
      } else if (Array.isArray(tablesData)) {
        // Fallback: Direct array of table names
        tables = tablesData.map(tableName => ({
          id: `${databaseName}_${schemaName}_${tableName}`,
          name: tableName,
          type: 'table',
          databaseName: databaseName,
          schemaName: schemaName,
          rowCount: null
        })); 
      } else {
        console.warn('Unexpected tables response format:', tablesData);
        tables = [];
      }
      
      setTablesCache(prev => ({
        ...prev,
        [cacheKey]: tables
      }));
      
      return tables;
    } catch (err) {
      console.error('Error loading tables:', err);
      setError(`Failed to load tables for ${databaseName}.${schemaName}: ${err.message}`);
      return [];
    } finally {
      setLoadingNodes(prev => {
        const newLoading = new Set(prev);
        newLoading.delete(`${databaseName}_${schemaName}`);
        return newLoading;
      });
    }
  };

  const toggleNode = async (nodeId, nodeType, nodeMeta = {}) => {
    if (nodeType === 'table') {
      onTableSelect({
        id: nodeId,
        name: nodeMeta.name,
        database: nodeMeta.databaseName,
        schema: nodeMeta.schemaName
      });
      return;
    }

    if (expandedNodes.has(nodeId)) {
      const newExpanded = new Set(expandedNodes);
      newExpanded.delete(nodeId);
      setExpandedNodes(newExpanded);
    } else {
      if (nodeType === 'database') {
        await loadSchemas(nodeMeta.name);
      } else if (nodeType === 'schema') {
        await loadTables(nodeMeta.databaseName, nodeMeta.name);
      }
      
      setExpandedNodes(prev => new Set(prev).add(nodeId));
    }
  };

  const filterTables = (tables, query) => {
    if (!query || !tables) return tables || [];
    return tables.filter(table => 
      table.name.toLowerCase().includes(query.toLowerCase())
    );
  };

  const getNodeIcon = (type, isExpanded) => {
    switch (type) {
      case 'database':
        return 'Database';
      case 'schema':
        return isExpanded ? 'FolderOpen' : 'Folder';
      case 'table':
        return 'Table';
      case 'view':
        return 'Eye';
      default:
        return 'Circle';
    }
  };

  const TreeNode = ({ node, level = 0, type, meta = {} }) => {
    const isExpanded = expandedNodes.has(node.id);
    const isLoading = loadingNodes.has(node.id) || loadingNodes.has(meta.name);
    const isSelected = enableMultiSelect 
      ? selectedTables?.some(t => t.id === node.id) || false
      : selectedTable?.id === node.id;
    
    // Determine if node has children
    let hasChildren = false;
    let children = [];
    
    if (type === 'database') {
      hasChildren = true;
      children = schemasCache[node.name] || [];
    } else if (type === 'schema') {
      hasChildren = true;
      children = tablesCache[`${meta.databaseName}_${node.name}`] || [];
    }

    // Get connection status for database nodes
    const isConnected = type === 'database'; // You can enhance this with actual status checking

    if (type === 'database') {
      return (
        <div className="border border-border rounded-lg mb-2">
          {/* Database Header */}
          <div 
            className={`flex items-center justify-between p-3 cursor-pointer hover:bg-surface-secondary transition-colors ${
              isSelected ? 'bg-accent/10' : ''
            }`}
            onClick={() => toggleNode(node.id, type, { ...meta, name: node.name })}
          >
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 flex items-center justify-center">
                {isLoading ? (
                  <div className="w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Icon 
                    name="ChevronRight" 
                    size={16} 
                    className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  />
                )}
              </div>
              <Icon name="Database" size={18} className="text-primary" />
              <div>
                <div className="font-medium text-text-primary">{node.name}</div>
                <div className="text-xs text-text-secondary">{node.type}</div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {predefinedSchemasDbs.has(node.name) && (
                <div className="flex items-center" title="Using predefined schemas">
                  <Icon name="Settings" size={14} className="text-accent" />
                </div>
              )}
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-success' : 'bg-error'
              }`}></div>
            </div>
          </div>

          {/* Schemas */}
          {isExpanded && (
            <div className="border-t border-border bg-surface-secondary/50">
              {children.map((schema) => (
                <TreeNode 
                  key={schema.id}
                  node={schema} 
                  level={level + 1} 
                  type="schema" 
                  meta={{ databaseName: node.name }}
                />
              ))}
            </div>
          )}
        </div>
      );
    }

    if (type === 'schema') {
      const schemaChildren = tablesCache[`${meta.databaseName}_${node.name}`] || [];
      const filteredTables = filterTables(schemaChildren, searchQuery);
      
      return (
        <div className="border-b border-border last:border-b-0">
          {/* Schema Header */}
          <div 
            className={`flex items-center justify-between p-3 pl-8 cursor-pointer hover:bg-surface-secondary transition-colors ${
              isSelected ? 'bg-accent/10' : ''
            }`}
            onClick={() => toggleNode(node.id, type, { ...meta, name: node.name })}
          >
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 flex items-center justify-center">
                {isLoading ? (
                  <div className="w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Icon 
                    name="ChevronRight" 
                    size={14} 
                    className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  />
                )}
              </div>
              <Icon name="Folder" size={16} className="text-accent" />
              <span className="font-medium text-text-primary">{node.name}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-text-secondary">
                {node.tableCount || filteredTables.length}
              </span>
            </div>
          </div>

          {/* Tables */}
          {isExpanded && (
            <div className="bg-surface">
              {filteredTables.map((table) => (
                <TreeNode 
                  key={table.id} 
                  node={table} 
                  level={level + 1} 
                  type={table.type}
                  meta={{ databaseName: meta.databaseName, schemaName: node.name }}
                />
              ))}
            </div>
          )}
        </div>
      );
    }

    // Table node
    const hasStoredMetadata = tablesWithMetadata.has(node.id);
    
    return (
      <div 
        className={`flex items-center justify-between p-3 pl-16 hover:bg-surface-secondary transition-colors cursor-pointer ${
          isSelected ? 'bg-accent/10 border-l-2 border-accent' : ''
        }`}
        onClick={() => toggleNode(node.id, type, { ...meta, name: node.name })}
      >
        <div className="flex items-center space-x-3">
          {enableMultiSelect && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleNode(node.id, type, { ...meta, name: node.name })}
              onClick={(e) => e.stopPropagation()}
              className="rounded"
            />
          )}
          <Icon name="Table" size={16} className="text-text-muted" />
          <div>
            <div className={`font-medium text-text-primary ${isSelected ? 'text-accent' : ''}`}>
              {node.name}
            </div>
            {(node.rowCount !== undefined || node.columnCount) && (
              <div className="text-xs text-text-secondary">
                {node.rowCount !== undefined && node.rowCount !== null 
                  ? `${node.rowCount.toLocaleString()} rows`
                  : 'Unknown rows'
                } • {node.columnCount || 'Unknown'} columns
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {hasStoredMetadata && (
            <div className="flex items-center space-x-1">
              <Icon name="Sparkles" size={12} className="text-accent" />
              <span className="text-xs text-accent font-medium">Analyzed</span>
            </div>
          )}
          {!hasStoredMetadata && (
            <div className="text-xs text-text-muted">
              Not analyzed
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-surface border-r border-border">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading database connections...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-surface border-r border-border">
        <div className="text-center p-4">
          <Icon name="AlertCircle" size={48} className="text-error mx-auto mb-4" />
          <p className="text-error text-sm mb-4">{error}</p>
          <Button onClick={loadDatabases} variant="outline" size="sm">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-surface border-r border-border">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-text-primary">
            {selectedConnection ? selectedConnection : 'Schema Explorer'}
          </h3>
          <div className="flex items-center space-x-1">
            <Button
              variant="ghost"
              iconName="RefreshCw"
              className="p-2"
              onClick={loadDatabases}
              aria-label="Refresh schemas"
            />
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="p-2 text-text-muted hover:text-text-primary hover:bg-surface-secondary rounded-lg transition-colors"
                title="Collapse Schema Explorer"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
            )}
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
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Tree Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {databases.length === 0 ? (
          <div className="text-center py-8 text-text-muted">
            <Icon name="Database" size={48} className="mx-auto mb-3 opacity-50" />
            <p className="text-text-secondary text-sm">
              {selectedConnection 
                ? `Connection "${selectedConnection}" not found or unavailable`
                : 'No database connections found'
              }
            </p>
            <p className="text-text-muted text-xs mt-2">
              {selectedConnection 
                ? 'Please check if the connection is properly configured'
                : 'Add connections in the Database Connections dashboard'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {databases.map(database => (
              <TreeNode 
                key={database.id} 
                node={database} 
                level={0} 
                type="database"
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SchemaTree;