import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import SchemaTree from './components/SchemaTree';
import TableDetails from './components/TableDetails';
import MetadataPanel from './components/MetadataPanel';

const SchemaExplorer = () => {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMainSidebarCollapsed, setIsMainSidebarCollapsed] = useState(false);
  const [selectedTable, setSelectedTable] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activePanel, setActivePanel] = useState('details'); // 'details' or 'metadata'
  const [metadataPanelWidth, setMetadataPanelWidth] = useState(400); // pixels
  const [isMetadataPanelCollapsed, setIsMetadataPanelCollapsed] = useState(false);
  const [schemaPanelWidth, setSchemaPanelWidth] = useState(320); // pixels
  const [isSchemaPanelCollapsed, setIsSchemaPanelCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [resizeType, setResizeType] = useState(null); // 'schema' or 'metadata'
  
  // Enhanced table data with metadata integration
  const [enhancedTableData, setEnhancedTableData] = useState(null);
  
  // Get selected connection from navigation state (when coming from connection dashboard)
  const selectedConnection = location.state?.connectionName || null;
  
  // Parse URL parameters for auto-selection
  const urlParams = new URLSearchParams(location.search);
  const urlDatabase = urlParams.get('database');
  const urlSchema = urlParams.get('schema');
  const urlTable = urlParams.get('table');

  // Function to merge generated metadata with table data
  const handleMetadataGenerated = (generatedMetadata) => {
    if (!selectedTable || !generatedMetadata) return;

    console.log('Raw generated metadata:', generatedMetadata);

    // Notify schema tree to refresh metadata indicators
    const refreshEvent = new CustomEvent('metadataGenerated', {
      detail: {
        database: selectedTable.database,
        schema: selectedTable.schema, 
        table: selectedTable.name
      }
    });
    window.dispatchEvent(refreshEvent);

    // Extract the actual metadata from the response structure
    const actualMetadata = generatedMetadata.metadata || generatedMetadata;
    console.log('Processing generated metadata for enhancement:', actualMetadata);

    // Create enhanced data structure directly from the generated metadata
    // This approach doesn't rely on existing table data state since we can construct it from metadata
    const enhancedData = createEnhancedDataFromMetadata(actualMetadata);
    
    console.log('Enhanced data created from metadata:', enhancedData);
    setEnhancedTableData(enhancedData);
  };

  // Function to create enhanced data structure directly from generated metadata
  const createEnhancedDataFromMetadata = (metadata) => {
    if (!metadata || !metadata.columns) {
      console.warn('Invalid metadata structure:', metadata);
      return null;
    }

    // Convert metadata columns object to enhanced columns array
    const enhancedColumns = Object.entries(metadata.columns).map(([columnName, columnData]) => ({
      name: columnName,
      type: columnData.data_type, // For backward compatibility
      data_type: columnData.data_type,
      is_nullable: columnData.is_nullable,
      // Enhanced fields from metadata
      businessName: columnData.business_name || '',
      purpose: columnData.purpose || '',
      description: columnData.description || columnData.definition || '',
      dataQuality: columnData.data_quality_score,
      statistics: columnData.statistics || {},
      categoricalValues: columnData.categorical_values,
      businessRules: columnData.business_rules || columnData.constraints || [],
      format: columnData.format || '',
      dataClassification: columnData.data_classification || '',
      constraints: columnData.constraints || [],
      is_categorical: columnData.is_categorical || false,
      is_numerical: columnData.is_numerical || false,
      metadata: true, // Flag to indicate enhanced metadata is available
      hasMetadata: true // Alternative flag name
    }));

    // Extract table insights
    const tableInsights = metadata.table_insights || {};

    // Create enhanced table data structure
    const enhancedData = {
      database: metadata.database_name,
      schema: metadata.schema_name,
      table: metadata.table_name,
      columns: enhancedColumns,
      // Table-level metadata from generated insights
      description: tableInsights.description || metadata.description || '',
      domain: tableInsights.domain,
      category: tableInsights.category,
      purpose: tableInsights.purpose,
      usage_patterns: tableInsights.usage_patterns || [],
      business_use_cases: tableInsights.usage_patterns || metadata.table_description?.business_use_cases || [],
      data_lifecycle: tableInsights.data_lifecycle,
      special_handling: tableInsights.special_handling || [],
      // Additional metadata fields
      table_insights: tableInsights,
      table_description: metadata.table_description || {},
      businessContext: metadata.table_description?.business_context,
      dataQuality: metadata.data_quality,
      businessRules: metadata.business_rules,
      relationships: metadata.relationships || [],
      categorical_definitions: metadata.categorical_definitions,
      indexes: metadata.indexes || [],
      constraints: metadata.constraints || {},
      partition_info: metadata.partition_info || {},
      processing_stats: metadata.processing_stats || {},
      metadata: metadata, // Store full metadata for reference
      hasStoredMetadata: true, // Mark as having metadata
      enhanced: true // Flag for enhanced data
    };

    return enhancedData;
  };

  // Auto-select table from URL parameters
  useEffect(() => {
    if (urlDatabase && urlSchema && urlTable && !selectedTable) {
      // Auto-select the table based on URL parameters
      const autoSelectedTable = {
        id: `${urlDatabase}_${urlSchema}_${urlTable}`,
        name: urlTable,
        database: urlDatabase,
        schema: urlSchema
      };
      console.log('Auto-selecting table from URL:', autoSelectedTable);
      setSelectedTable(autoSelectedTable);
      
      // Set active panel to metadata since this is coming from metadata generation
      setActivePanel('metadata');
    }
  }, [urlDatabase, urlSchema, urlTable, selectedTable]);

  // Reset enhanced data when table changes
  useEffect(() => {
    if (selectedTable) {
      setEnhancedTableData(null);
    }
  }, [selectedTable]);

  // Build dynamic breadcrumb based on selected connection and table
  const buildBreadcrumbs = () => {
    let items = [];
    
    if (selectedConnection) {
      items.push({ label: 'Connections', path: '/database-connections-dashboard' });
      items.push({ label: selectedConnection, path: '/schema-explorer' });
      
      if (selectedTable) {
        if (selectedTable.schema) {
          items.push({ label: selectedTable.schema, path: '/schema-explorer' });
        }
        items.push({ label: selectedTable.name, path: '/schema-explorer' });
      }
    } else {
      items.push({ label: 'Schema Explorer', path: '/schema-explorer' });
    }
    
    return items;
  };

  const breadcrumbItems = buildBreadcrumbs();

  const handleTableSelect = (tableData) => {
    setSelectedTable(tableData);
  };

  const handleSidebarToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  const toggleMainSidebarCollapse = () => {
    setIsMainSidebarCollapsed(!isMainSidebarCollapsed);
  };

  const handleSearchChange = (query) => {
    setSearchQuery(query);
  };

  const handleMouseDown = (e, type) => {
    setIsResizing(true);
    setResizeType(type);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!isResizing || !resizeType) return;
    
    // Find the main content container
    const container = document.querySelector('.lg\\:flex.flex-1.relative');
    if (!container) return;
    
    const containerRect = container.getBoundingClientRect();
    
    if (resizeType === 'schema') {
      // For schema panel, calculate from left edge
      const newWidth = e.clientX - containerRect.left;
      const minWidth = 200;
      const maxWidth = containerRect.width * 0.6; // Max 60% of container
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setSchemaPanelWidth(newWidth);
      }
    } else if (resizeType === 'metadata') {
      // For metadata panel, calculate from right edge
      const newWidth = containerRect.right - e.clientX;
      const minWidth = 300;
      const maxWidth = containerRect.width * 0.7; // Max 70% of container
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setMetadataPanelWidth(newWidth);
      }
    }
  };

  const handleMouseUp = () => {
    setIsResizing(false);
    setResizeType(null);
  };

  const toggleMetadataPanel = () => {
    setIsMetadataPanelCollapsed(!isMetadataPanelCollapsed);
  };

  const toggleSchemaPanel = () => {
    setIsSchemaPanelCollapsed(!isSchemaPanelCollapsed);
  };

  useEffect(() => {
    if (isResizing && resizeType) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // Prevent text selection during resize
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
      };
    }
  }, [isResizing, resizeType]);

  return (
    <>
      <Helmet>
        <title>Schema Explorer - Metadata Builder</title>
        <meta name="description" content="Explore database schemas, tables, and columns with detailed metadata analysis and AI-powered insights." />
      </Helmet>

      <div className="min-h-screen bg-background">
              <Header 
        onMenuToggle={handleSidebarToggle} 
        isMenuOpen={isSidebarOpen}
        isSidebarCollapsed={isMainSidebarCollapsed}
      />
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={handleSidebarClose}
        isCollapsed={isMainSidebarCollapsed}
        onToggleCollapse={toggleMainSidebarCollapse}
      />
        
        <main className={`pt-16 ${isMainSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
          {/* Page Header */}
          <div className="bg-surface border-b border-border px-6 py-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h1 className="text-2xl font-semibold text-text-primary">
                  {selectedConnection ? `${selectedConnection} - Schema Explorer` : 'Schema Explorer'}
                </h1>
                <p className="text-text-secondary">
                  {selectedConnection 
                    ? `Explore schemas and tables in ${selectedConnection} database`
                    : 'Browse and analyze database schemas with AI-powered insights'
                  }
                </p>
              </div>
              
              {/* Mobile Panel Toggle */}
              <div className="lg:hidden">
                <button
                  onClick={() => setActivePanel(activePanel === 'details' ? 'metadata' : 'details')}
                  className="px-3 py-2 text-sm bg-primary text-primary-foreground rounded-lg flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {activePanel === 'details' ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    )}
                  </svg>
                  <span>{activePanel === 'details' ? 'Analysis' : 'Details'}</span>
                </button>
              </div>
            </div>
            <Breadcrumb items={breadcrumbItems} />
          </div>

          {/* Main Content */}
          <div className="h-[calc(100vh-8rem)] flex">
            {/* Mobile Schema Tree - Full Width */}
            <div className="w-full lg:hidden">
              <SchemaTree
                onTableSelect={handleTableSelect}
                selectedTable={selectedTable}
                searchQuery={searchQuery}
                onSearchChange={handleSearchChange}
                selectedConnection={selectedConnection || urlDatabase}
              />
            </div>

            {/* Desktop Layout - Three Panels */}
            <div className="hidden lg:flex flex-1 relative">
              {/* Schema Tree - Left Panel */}
              {!isSchemaPanelCollapsed && (
                <>
                  <div 
                    className="flex-shrink-0"
                    style={{ width: `${schemaPanelWidth}px` }}
                  >
                    <SchemaTree
                      onTableSelect={handleTableSelect}
                      selectedTable={selectedTable}
                      searchQuery={searchQuery}
                      onSearchChange={handleSearchChange}
                      selectedConnection={selectedConnection || urlDatabase}
                      onToggleCollapse={toggleSchemaPanel}
                    />
                  </div>

                  {/* Schema Panel Resize Handle */}
                  <div
                    className={`w-2 bg-border hover:bg-primary/20 cursor-col-resize flex-shrink-0 transition-colors group relative ${
                      isResizing && resizeType === 'schema' ? 'bg-primary/30' : ''
                    }`}
                    onMouseDown={(e) => handleMouseDown(e, 'schema')}
                    style={{ cursor: 'col-resize' }}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      {/* Resize grip lines */}
                      <div className="flex flex-col space-y-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                      </div>
                    </div>
                    
                    {/* Hover tooltip */}
                    <div className="absolute left-1/2 top-4 transform -translate-x-1/2 bg-text-primary text-background text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                      Drag to resize
                    </div>
                  </div>
                </>
              )}

              {/* Collapsed Schema Panel - Show Toggle Button */}
              {isSchemaPanelCollapsed && (
                <div className="w-12 bg-surface border-r border-border flex items-start justify-center pt-4">
                  <button
                    onClick={toggleSchemaPanel}
                    className="p-2 text-text-muted hover:text-text-primary hover:bg-surface-secondary rounded-lg transition-colors"
                    title="Expand Schema Explorer"
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
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              )}
              {/* Table Details - Center Panel */}
              <div className="flex-1 min-w-0">
                <TableDetails 
                  selectedTable={selectedTable} 
                  enhancedTableData={enhancedTableData}
                  onTableDataLoaded={(tableData) => {
                    // For stored metadata, set the enhanced data directly
                    setEnhancedTableData(tableData);
                  }}
                />
              </div>

              {!isMetadataPanelCollapsed && (
                <>
                  {/* Metadata Panel Resize Handle */}
                  <div
                    className={`w-2 bg-border hover:bg-primary/20 cursor-col-resize flex-shrink-0 transition-colors group relative ${
                      isResizing && resizeType === 'metadata' ? 'bg-primary/30' : ''
                    }`}
                    onMouseDown={(e) => handleMouseDown(e, 'metadata')}
                    style={{ cursor: 'col-resize' }}
                  >
                    <div className="w-full h-full flex items-center justify-center">
                      {/* Resize grip lines */}
                      <div className="flex flex-col space-y-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                        <div className="w-0.5 h-4 bg-text-muted rounded-full"></div>
                      </div>
                    </div>
                    
                    {/* Hover tooltip */}
                    <div className="absolute left-1/2 top-4 transform -translate-x-1/2 bg-text-primary text-background text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                      Drag to resize
                    </div>
                  </div>

                  {/* Metadata Panel - Right Panel */}
                  <div 
                    className="flex-shrink-0 relative"
                    style={{ width: `${metadataPanelWidth}px` }}
                  >
                    <MetadataPanel 
                      selectedTable={selectedTable} 
                      onToggleCollapse={toggleMetadataPanel}
                      isCollapsed={isMetadataPanelCollapsed}
                      onMetadataGenerated={handleMetadataGenerated}
                    />
                  </div>
                </>
              )}

              {/* Collapsed Panel - Show Toggle Button */}
              {isMetadataPanelCollapsed && (
                <div className="w-12 bg-surface border-l border-border flex items-start justify-center pt-4">
                  <button
                    onClick={toggleMetadataPanel}
                    className="p-2 text-text-muted hover:text-text-primary hover:bg-surface-secondary rounded-lg transition-colors"
                    title="Expand Analysis Panel"
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
                </div>
              )}
            </div>

            {/* Mobile/Tablet Layout - Single Panel */}
            <div className="flex-1 lg:hidden">
              {activePanel === 'details' ? (
                <TableDetails 
                  selectedTable={selectedTable} 
                  enhancedTableData={enhancedTableData}
                  onTableDataLoaded={(tableData) => {
                    // For stored metadata, set the enhanced data directly
                    setEnhancedTableData(tableData);
                  }}
                />
              ) : (
                <MetadataPanel 
                  selectedTable={selectedTable} 
                  onMetadataGenerated={handleMetadataGenerated}
                />
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
};

export default SchemaExplorer;