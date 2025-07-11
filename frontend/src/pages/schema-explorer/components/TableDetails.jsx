import React, { useState, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Input from '../../../components/ui/Input';
import EditableMetadata from '../../../components/EditableMetadata';
import { databaseAPI, metadataAPI } from '../../../services/api';

// Component for displaying categorical values with expandable definitions
const CategoricalValuesSection = ({ column, categoricalDefinitions }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const hasDefinitions = categoricalDefinitions && Object.keys(categoricalDefinitions).length > 0;
  const hasValues = column.categoricalValues && column.categoricalValues.length > 0;
  
  if (!hasDefinitions && !hasValues) return null;
  
  return (
    <div className="mb-3">
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs text-text-muted">
          {hasDefinitions 
            ? `Categorical Values (${Object.keys(categoricalDefinitions).length} defined)`
            : `Values (${column.categoricalValues?.length || 0})`
          }
        </div>
        {hasDefinitions && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-accent hover:text-accent-hover transition-colors flex items-center space-x-1"
          >
            <span>{isExpanded ? 'Hide' : 'Show'} definitions</span>
            <Icon 
              name={isExpanded ? 'ChevronUp' : 'ChevronDown'} 
              size={12} 
              className="transition-transform"
            />
          </button>
        )}
      </div>
      
      {/* Collapsed view - show values as tags */}
      {!isExpanded && (
        <div className="flex flex-wrap gap-1">
          {hasDefinitions 
            ? Object.keys(categoricalDefinitions).slice(0, 5).map((value, idx) => (
                <span 
                  key={idx}
                  className="px-2 py-1 text-xs bg-accent/10 text-accent rounded cursor-pointer hover:bg-accent/20 transition-colors"
                  onClick={() => setIsExpanded(true)}
                  title="Click to see definition"
                >
                  {value}
                </span>
              ))
            : column.categoricalValues?.slice(0, 5).map((value, idx) => (
                <span 
                  key={idx}
                  className="px-2 py-1 text-xs bg-accent/10 text-accent rounded"
                >
                  {value.value} ({value.count})
                </span>
              ))
          }
          {((hasDefinitions && Object.keys(categoricalDefinitions).length > 5) || 
            (hasValues && column.categoricalValues.length > 5)) && (
            <span className="px-2 py-1 text-xs bg-surface text-text-muted rounded">
              +{hasDefinitions 
                ? Object.keys(categoricalDefinitions).length - 5 
                : column.categoricalValues.length - 5
              } more
            </span>
          )}
        </div>
      )}
      
      {/* Expanded view - show definitions */}
      {isExpanded && hasDefinitions && (
        <div className="space-y-2">
          {Object.entries(categoricalDefinitions).map(([value, definition]) => (
            <div key={value} className="p-3 bg-surface-secondary rounded-lg border border-border">
              <div className="flex items-start space-x-3">
                <span className="font-mono text-xs bg-accent/10 text-accent px-2 py-1 rounded border">
                  {value}
                </span>
                <div className="flex-1">
                  <p className="text-sm text-text-secondary">{definition}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Expanded view - show values without definitions */}
      {isExpanded && !hasDefinitions && hasValues && (
        <div className="flex flex-wrap gap-1">
          {column.categoricalValues.map((value, idx) => (
            <span 
              key={idx}
              className="px-2 py-1 text-xs bg-accent/10 text-accent rounded"
            >
              {value.value} ({value.count})
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const TableDetails = ({ selectedTable, enhancedTableData, onTableDataLoaded }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [tableData, setTableData] = useState(null);
  // Default to 'sample' when no metadata, 'overview' when metadata exists
  const [activeTab, setActiveTab] = useState(enhancedTableData ? 'overview' : 'sample');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Sample data fetching state
  const [sampleDataLoading, setSampleDataLoading] = useState(false);
  const [sampleDataError, setSampleDataError] = useState(null);
  const [fetchedSampleData, setFetchedSampleData] = useState(null);
  const [metadataChecked, setMetadataChecked] = useState(false);

  // Use enhanced data if available, otherwise use regular table data
  const displayData = enhancedTableData || tableData;
  
  // Debug logs
  console.log('TableDetails Current state:', {
    selectedTable: selectedTable?.name,
    tableData: !!tableData,
    enhancedTableData: !!enhancedTableData,
    hasStoredMetadata: tableData?.hasStoredMetadata,
    displayData: !!displayData,
    columnsCount: displayData?.columns?.length || 0,
    enhancedColumns: displayData?.columns?.filter(col => col.hasMetadata)?.length || 0
  });
  
  // Debug displayData structure for Table Insights
  console.log('TableDetails displayData structure:', {
    domain: displayData?.domain,
    table_insights: displayData?.table_insights,
    purpose: displayData?.purpose,
    usage_patterns: displayData?.usage_patterns,
    business_use_cases: displayData?.business_use_cases,
    category: displayData?.category,
    description: displayData?.description
  });

  // Switch to overview tab when metadata is generated
  useEffect(() => {
    if (enhancedTableData && activeTab === 'sample') {
      setActiveTab('overview');
    }
  }, [enhancedTableData]);

  // Switch to a different tab if current tab becomes unavailable
  useEffect(() => {
    const hasSampleData = (displayData?.columns && displayData.columns.length > 0) || 
                         (displayData?.sampleData && displayData.sampleData.length > 0) ||
                         (fetchedSampleData?.sample_data && fetchedSampleData.sample_data.length > 0);
    
    const hasCategoricalData = displayData?.categorical_definitions && Object.keys(displayData.categorical_definitions).length > 0;
    
    // If on sample tab but no sample data available, switch to overview
    if (activeTab === 'sample' && !hasSampleData) {
      setActiveTab('overview');
    }
    
    // If on categorical tab but no categorical data available, switch to overview
    if (activeTab === 'categorical' && !hasCategoricalData) {
      setActiveTab('overview');
    }
  }, [displayData, fetchedSampleData, activeTab]);

  // Load table data when selectedTable changes
  useEffect(() => {
    if (selectedTable && selectedTable.database && selectedTable.schema && selectedTable.name) {
      loadTableData();
      // Reset to sample tab for new tables (unless they already have metadata)
      if (!enhancedTableData) {
        setActiveTab('sample');
      }
      // Reset sample data state for new table
      setFetchedSampleData(null);
      setSampleDataError(null);
      // Reset metadata checked flag for new table
      setMetadataChecked(false);
    } else {
      setTableData(null);
      setError(null);
      setFetchedSampleData(null);
      setSampleDataError(null);
      setMetadataChecked(false);
    }
  }, [selectedTable]);

  // Check for stored metadata after table data is loaded
  useEffect(() => {
    if (selectedTable && tableData && tableData.columns && tableData.columns.length > 0 && !metadataChecked) {
      checkAndLoadStoredMetadata();
    }
  }, [selectedTable?.database, selectedTable?.schema, selectedTable?.name, tableData?.columns?.length, metadataChecked]);

  // Notify parent component when final enhanced data is ready
  useEffect(() => {
    if (tableData && tableData.hasStoredMetadata && onTableDataLoaded) {
      onTableDataLoaded(tableData);
    }
  }, [tableData?.hasStoredMetadata, onTableDataLoaded]);

  // Function to check and load stored metadata
  const checkAndLoadStoredMetadata = async () => {
    if (!selectedTable) return;

    // Set flag to prevent multiple checks
    setMetadataChecked(true);

    try {
      // Check if metadata exists and load it directly (no separate check needed)
      const metadataResponse = await metadataAPI.checkMetadataExists(
        selectedTable.database,
        selectedTable.schema,
        selectedTable.name
      );

      if (metadataResponse.status === 200) {
        // Metadata exists and is loaded
        console.log('Stored metadata found and loaded successfully');
        
        const storedMetadata = metadataResponse.data;
        
        if (storedMetadata && storedMetadata.metadata) {
          console.log('Processing stored metadata for integration:', storedMetadata.metadata);
          console.log('Current table columns:', tableData?.columns?.map(c => c.name));
          
          // Handle double nesting - check if metadata.metadata exists (double-nested)
          let actualMetadata = storedMetadata.metadata;
          if (actualMetadata.metadata && typeof actualMetadata.metadata === 'object') {
            actualMetadata = actualMetadata.metadata;
            console.log('Found double-nested metadata, using inner metadata');
          }
          
          console.log('Available metadata columns:', Object.keys(actualMetadata.columns || {}));
          
          // Merge stored metadata with existing table data
          setTableData(prevTableData => {
            if (!prevTableData) return prevTableData;
            
            // Use the correctly nested metadata
            const metadata = actualMetadata;
            
            // Enhance columns with stored metadata
            const enhancedColumns = prevTableData.columns?.map(column => {
              const columnMetadata = metadata.columns?.[column.name];
              
              if (columnMetadata) {
                console.log(`Enhancing column ${column.name} with metadata:`, columnMetadata);
                return {
                  ...column,
                  // Merge metadata fields
                  description: columnMetadata.description || columnMetadata.definition || column.description,
                  businessName: columnMetadata.business_name || column.businessName,
                  purpose: columnMetadata.purpose || column.purpose,
                  format: columnMetadata.format || column.format,
                  constraints: columnMetadata.constraints || column.constraints || [],
                  statistics: columnMetadata.statistics || column.statistics || {},
                  isNumerical: columnMetadata.is_numerical || column.isNumerical,
                  isCategorical: columnMetadata.is_categorical || column.isCategorical,
                  dataQuality: columnMetadata.data_quality || column.dataQuality,
                  hasMetadata: true // Flag to indicate enhanced metadata is available
                };
              } else {
                console.log(`No metadata found for column ${column.name}`);
                return column;
              }
            }) || [];
            
            // If no columns were enhanced, check if we can enhance the table-level metadata
            const hasEnhancedColumns = enhancedColumns.some(col => col.hasMetadata);
            console.log(`Enhanced ${enhancedColumns.filter(col => col.hasMetadata).length} out of ${enhancedColumns.length} columns`);

            // Enhance table-level data with stored metadata
            const enhancedTableData = {
              ...prevTableData,
              columns: enhancedColumns,
              description: metadata.description || prevTableData.description,
              purpose: metadata.table_description?.purpose || prevTableData.purpose,
              usage_patterns: metadata.table_description?.business_use_cases || metadata.table_insights?.usage_patterns || [],
              constraints: metadata.constraints || prevTableData.constraints,
              categorical_definitions: metadata.categorical_definitions || {},
              tableInsights: metadata.table_insights || {},
              hasStoredMetadata: true
            };

            console.log('Enhanced table data:', enhancedTableData);
            return enhancedTableData;
          });
          
          // Switch to overview tab if metadata was loaded
          setActiveTab('overview');
        }
      }
    } catch (error) {
      // Metadata doesn't exist or error occurred - this is normal for tables without metadata
      if (error.response?.status !== 404) {
        console.warn('Error checking for stored metadata:', error);
      }
    }
  };

  const loadTableData = async () => {
    if (!selectedTable) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await databaseAPI.getTableInfo(
        selectedTable.database,
        selectedTable.schema,
        selectedTable.name
      );
      
      const tableInfo = response.data;
      console.log('Raw table info from API:', tableInfo); // Debug log
      
      // Debug log - handle different column formats
      if (Array.isArray(tableInfo.columns)) {
        console.log('API column names (array):', tableInfo.columns?.map(c => c.name || c.column_name));
      } else if (typeof tableInfo.columns === 'object' && tableInfo.columns !== null) {
        console.log('API column names (object):', Object.keys(tableInfo.columns));
      }
      
      // Transform the API response to match our expected format
      let columns = [];
      
      // Handle different column formats from the API
      if (tableInfo && tableInfo.columns) {
        if (Array.isArray(tableInfo.columns)) {
          // If columns is already an array of objects
          columns = tableInfo.columns.map(col => ({
            name: col.name || col.column_name,
            type: col.data_type || col.type,
            nullable: col.nullable !== false,
            primaryKey: col.primary_key || col.is_primary_key || false,
            unique: col.unique || col.is_unique || false,
            foreignKey: col.foreign_key || col.is_foreign_key || null,
            defaultValue: col.default_value || col.column_default || null,
            description: col.description || col.comment || '',
            sampleValues: col.sample_values || []
          }));
        } else if (typeof tableInfo.columns === 'object' && tableInfo.columns !== null) {
          // Check if it's the new detailed format (array of ColumnInfo objects)
          if (Array.isArray(tableInfo.columns)) {
            // New format: List of ColumnInfo objects
            columns = tableInfo.columns.map(col => ({
              name: col.name,
              type: col.data_type,
              nullable: col.is_nullable,
              primaryKey: col.is_primary_key,
              unique: col.is_unique,
              foreignKey: col.is_foreign_key,
              foreignKeyTable: col.foreign_key_table,
              foreignKeyColumn: col.foreign_key_column,
              defaultValue: col.default_value,
              description: col.comment || '',
              characterMaxLength: col.character_maximum_length,
              numericPrecision: col.numeric_precision,
              numericScale: col.numeric_scale,
              sampleValues: []
            }));
          } else {
            // Old format: Dictionary of column_name: data_type
            columns = Object.entries(tableInfo.columns).map(([columnName, dataType]) => ({
              name: columnName,
              type: dataType,
              nullable: null,
              primaryKey: false,
              unique: false,
              foreignKey: false,
              defaultValue: null,
              description: '',
              sampleValues: []
            }));
          }
        }
      }

      console.log('Transformed columns:', columns); // Debug log

      const transformedData = {
        name: selectedTable.name,
        schema: selectedTable.schema,
        database: selectedTable.database,
        type: 'table', // Default to table
        rowCount: tableInfo.row_count || null,
        size: tableInfo.size || 'Unknown',
        lastUpdated: tableInfo.last_updated || 'Unknown',
        description: tableInfo.description || `Table: ${selectedTable.name}`,
        columns: columns,
        indexes: tableInfo.indexes || [],
        foreignKeys: tableInfo.foreign_keys || [],
        constraints: tableInfo.constraints || [],
        sampleData: tableInfo.sample_data || []
      };
      
      console.log('Final transformed data:', transformedData); // Debug log
      setTableData(transformedData);
    } catch (err) {
      console.error('Error loading table data:', err);
      setError(`Failed to load table information: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Function to fetch sample data independently
  const fetchSampleData = async () => {
    if (!selectedTable || sampleDataLoading) return;

    try {
      setSampleDataLoading(true);
      setSampleDataError(null);

      const response = await metadataAPI.getSampleData(
        selectedTable.database,
        selectedTable.schema,
        selectedTable.name,
        100, // sample_size
        2    // num_samples
      );

      const sampleDataResult = response.data;
      setFetchedSampleData(sampleDataResult);

    } catch (err) {
      console.error('Error fetching sample data:', err);
      
      // Fallback to test endpoint for development
      try {
        console.log('Attempting fallback to test sample data endpoint...');
        const fallbackResponse = await metadataAPI.getSampleDataTest(
          selectedTable.database,
          selectedTable.schema,
          selectedTable.name,
          100, // sample_size
          2    // num_samples
        );
        
        const sampleDataResult = fallbackResponse.data;
        setFetchedSampleData(sampleDataResult);
        console.log('Successfully retrieved fallback sample data');
        
      } catch (fallbackErr) {
        console.error('Fallback sample data also failed:', fallbackErr);
        setSampleDataError(`Failed to fetch sample data: ${err.response?.data?.detail || err.message}`);
      }
    } finally {
      setSampleDataLoading(false);
    }
  };

  // Tab configuration
  const baseTabs = [
    { id: 'overview', label: 'Overview', icon: 'Info' },
    { id: 'columns', label: 'Columns', icon: 'Columns' },
    { id: 'indexes', label: 'Indexes', icon: 'Key' },
  ];

  // Add sample data tab only if we have table data or existing sample data
  const sampleTab = (displayData?.columns && displayData.columns.length > 0) || 
                    (displayData?.sampleData && displayData.sampleData.length > 0) ||
                    (fetchedSampleData?.sample_data && fetchedSampleData.sample_data.length > 0)
    ? [{ id: 'sample', label: 'Sample Data', icon: 'Table' }]
    : [];

  // Add categorical tab only if categorical definitions exist
  const categoricalTab = displayData?.categorical_definitions && Object.keys(displayData.categorical_definitions).length > 0
    ? [{ id: 'categorical', label: 'Categorical', icon: 'Tag' }]
    : [];

  const tabs = [
    ...baseTabs,
    ...sampleTab,
    ...categoricalTab,
    { id: 'misc', label: 'Misc', icon: 'MoreHorizontal' }
  ];

  const filteredColumns = displayData?.columns?.filter(column =>
    column.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (column.type || column.data_type || '').toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  // Handle tab switching with automatic sample data fetching
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    
    // If switching to sample tab and no sample data is available, fetch it
    if (tabId === 'sample') {
      const hasExistingSampleData = displayData?.sampleData && displayData.sampleData.length > 0;
      const hasFetchedSampleData = fetchedSampleData?.sample_data && fetchedSampleData.sample_data.length > 0;
      
      if (!hasExistingSampleData && !hasFetchedSampleData && !sampleDataLoading) {
        fetchSampleData();
      }
    }
  };

  const getTypeIcon = (type) => {
    if (!type || typeof type !== 'string') return 'Circle';
    const lowerType = type.toLowerCase();
    if (lowerType.includes('varchar') || lowerType.includes('text') || lowerType.includes('string')) return 'Type';
    if (lowerType.includes('integer') || lowerType.includes('decimal') || lowerType.includes('number') || lowerType.includes('int') || lowerType.includes('bigint')) return 'Hash';
    if (lowerType.includes('timestamp') || lowerType.includes('date') || lowerType.includes('time')) return 'Calendar';
    if (lowerType.includes('boolean') || lowerType.includes('bool')) return 'ToggleLeft';
    return 'Circle';
  };

  const getConstraintBadges = (column) => {
    const badges = [];
    if (column.primaryKey === true) badges.push({ label: 'PK', color: 'bg-primary text-primary-foreground' });
    if (column.foreignKey === true) {
      const fkLabel = column.foreignKeyTable ? `FK → ${column.foreignKeyTable}` : 'FK';
      badges.push({ label: fkLabel, color: 'bg-accent text-accent-foreground' });
    }
    if (column.unique === true) badges.push({ label: 'UQ', color: 'bg-warning text-warning-foreground' });
    if (column.nullable === false) badges.push({ label: 'NN', color: 'bg-secondary text-secondary-foreground' });
    return badges;
  };

  // Metadata update functions
  const handleMetadataUpdate = async (field, value, isColumnField = false, columnName = null) => {
    if (!selectedTable) return;
    
    try {
      const requestData = {
        db_name: selectedTable.database,
        schema_name: selectedTable.schema,
        table_name: selectedTable.name,
        table_metadata: isColumnField ? {} : { [field]: value },
        column_metadata: isColumnField ? { [columnName]: { [field]: value } } : {}
      };
      
      const response = await metadataAPI.updateMetadata(requestData);
      
      if (response.data.success) {
        // Update the local state with the new value
        if (isColumnField) {
          setTableData(prevData => ({
            ...prevData,
            columns: prevData.columns.map(col => 
              col.name === columnName ? { ...col, [field]: value } : col
            )
          }));
        } else {
          setTableData(prevData => ({
            ...prevData,
            [field]: value
          }));
        }
        
        // Show success notification
        console.log('Metadata updated successfully:', response.data);
      }
    } catch (error) {
      console.error('Error updating metadata:', error);
      throw error;
    }
  };

  const handleAIMetadataUpdate = async (field, userFeedback, currentValue, isColumnField = false, columnName = null) => {
    if (!selectedTable) return;
    
    try {
      const requestData = {
        db_name: selectedTable.database,
        schema_name: selectedTable.schema,
        table_name: selectedTable.name,
        current_metadata: isColumnField 
          ? { [field]: currentValue }
          : { [field]: currentValue },
        user_feedback: userFeedback,
        update_scope: isColumnField ? 'column_level' : 'table_level',
        target_column: isColumnField ? columnName : null
      };
      
      const response = await metadataAPI.updateMetadataWithAI(requestData);
      
      if (response.data.suggested_updates) {
        // Extract the updated value from AI response
        const suggestedValue = response.data.suggested_updates[field];
        
        if (suggestedValue !== undefined) {
          // Apply the AI suggested update
          await handleMetadataUpdate(field, suggestedValue, isColumnField, columnName);
          
          // Show AI explanation
          console.log('AI Update:', {
            explanation: response.data.explanation,
            confidence: response.data.confidence_score,
            reasoning: response.data.reasoning
          });
        }
      }
    } catch (error) {
      console.error('Error with AI metadata update:', error);
      throw error;
    }
  };

  // Enhanced column rendering with metadata support
  const renderColumnCard = (column, index) => {
    const hasMetadata = column.metadata || column.businessName || column.purpose || column.dataQuality;
    
    return (
      <div key={index} className="p-4 bg-surface-secondary rounded-lg border border-border hover:border-accent/30 transition-colors">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <Icon name={getTypeIcon(column.type || column.data_type)} size={16} className="text-text-muted mt-0.5" />
            <div>
              <h4 className="font-medium text-text-primary">{column.name}</h4>
              <div className="mt-1 mb-2">
                <EditableMetadata
                  value={column.businessName || ""}
                  field="business_name"
                  onSave={(field, value) => handleMetadataUpdate(field, value, true, column.name)}
                  onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue, true, column.name)}
                  placeholder="Add business name..."
                  type="text"
                  label="Business Name"
                />
              </div>
              <p className="text-sm text-text-secondary">{column.type || column.data_type}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-1">
            {getConstraintBadges(column).map((badge, badgeIndex) => (
              <span
                key={badgeIndex}
                className={`px-2 py-1 text-xs font-medium rounded ${badge.color}`}
              >
                {badge.label}
              </span>
            ))}
          </div>
        </div>
        
        {/* Business Description */}
        <div className="mb-3">
          <EditableMetadata
            value={column.purpose || column.description || ""}
            field="description"
            onSave={(field, value) => handleMetadataUpdate(field, value, true, column.name)}
            onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue, true, column.name)}
            placeholder="Add column description..."
            type="textarea"
            multiline={true}
            label="Description"
          />
        </div>

        {/* Statistics */}
        {column.statistics && (
          column.statistics.min !== undefined || 
          column.statistics.max !== undefined || 
          column.statistics.mean !== undefined || 
          column.statistics.null_count !== undefined
        ) && (
          <div className="mb-3 p-2 bg-surface rounded border">
            <div className="text-xs text-text-muted mb-1">Statistics</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {column.statistics.min !== undefined && (
                <div>
                  <span className="text-text-muted">Min:</span> 
                  <span className="text-text-primary ml-1">{column.statistics.min}</span>
                </div>
              )}
              {column.statistics.max !== undefined && (
                <div>
                  <span className="text-text-muted">Max:</span> 
                  <span className="text-text-primary ml-1">{column.statistics.max}</span>
                </div>
              )}
              {column.statistics.mean !== undefined && (
                <div>
                  <span className="text-text-muted">Avg:</span> 
                  <span className="text-text-primary ml-1">{column.statistics.mean?.toFixed(2)}</span>
                </div>
              )}
              {column.statistics.null_count !== undefined && (
                <div>
                  <span className="text-text-muted">Nulls:</span> 
                  <span className="text-text-primary ml-1">{column.statistics.null_count}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Categorical Values with Definitions */}
        {(column.categoricalValues || (displayData.categorical_definitions && displayData.categorical_definitions[column.name])) && (
          <CategoricalValuesSection 
            column={column} 
            categoricalDefinitions={displayData.categorical_definitions && displayData.categorical_definitions[column.name]} 
          />
        )}

        {/* Sample Values */}
        {column.sampleValues && column.sampleValues.length > 0 && !column.categoricalValues && (
          <div className="mb-3">
            <div className="text-xs text-text-muted mb-2">Sample Values</div>
            <div className="flex flex-wrap gap-1">
              {column.sampleValues.slice(0, 3).map((value, idx) => (
                <code 
                  key={idx}
                  className={`px-2 py-1 text-xs bg-surface rounded text-text-primary ${
                    value && value.length > 100 ? 'cursor-help border-dashed' : ''
                  }`}
                  title={value && value.length > 100 ? value : undefined}
                >
                  {value && value.length > 100 ? value.substring(0, 100) + '...' : value}
                </code>
              ))}
            </div>
          </div>
        )}

        {/* Business Rules */}
        {column.businessRules && column.businessRules.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-text-muted mb-2">Business Rules</div>
            <div className="space-y-1">
              {column.businessRules.slice(0, 2).map((rule, idx) => (
                <div key={idx} className="text-xs text-text-secondary p-2 bg-surface rounded border-l-2 border-accent">
                  {rule}
                </div>
              ))}
              {column.businessRules.length > 2 && (
                <div className="text-xs text-text-muted">
                  +{column.businessRules.length - 2} more rules
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Default Value */}
        {column.defaultValue && (
          <div className="text-xs text-text-muted">
            Default: <code className="px-1 bg-surface rounded">{column.defaultValue}</code>
          </div>
        )}

        {/* Metadata indicator */}
        {hasMetadata && (
          <div className="mt-2 pt-2 border-t border-border">
            <div className="flex items-center space-x-1">
              <Icon name="Sparkles" size={12} className="text-accent" />
              <span className="text-xs text-accent">Enhanced with AI metadata</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!selectedTable) {
    return (
      <div className="h-full flex items-center justify-center bg-surface-secondary">
        <div className="text-center">
          <Icon name="Table" size={48} className="text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">No Table Selected</h3>
          <p className="text-text-secondary">Select a table from the schema tree to view its details</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-surface">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading table details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-surface">
        <div className="text-center p-4">
          <Icon name="AlertCircle" size={48} className="text-error mx-auto mb-4" />
          <p className="text-error text-sm mb-4">{error}</p>
          <button 
            onClick={loadTableData}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!displayData) {
    return (
      <div className="h-full flex items-center justify-center bg-surface">
        <div className="text-center">
          <Icon name="Database" size={48} className="text-text-muted mx-auto mb-4" />
          <p className="text-text-secondary">No table data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-surface">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold text-text-primary">{displayData.name}</h2>
            <p className="text-sm text-text-secondary">
              {displayData.database}.{displayData.schema}.{displayData.name}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="text-right text-sm">
              <div className="text-text-primary font-medium">
                {displayData.rowCount ? `${displayData.rowCount.toLocaleString()} rows` : 'Unknown rows'}
              </div>
              <div className="text-text-secondary">{displayData.size}</div>
            </div>
            <Icon name={displayData.type === 'view' ? 'Eye' : 'Table'} size={24} className="text-text-muted" />
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 bg-surface-secondary rounded-lg p-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
                activeTab === tab.id 
                  ? 'bg-surface text-text-primary shadow-sm' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface/50'
              }`}
            >
              <Icon name={tab.icon} size={16} />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'overview' && (
          <div className="h-full overflow-y-auto p-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Table Summary */}
              <div className="bg-surface-secondary rounded-lg border border-border p-6">
                <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center">
                  <Icon name="Table" size={20} className="mr-2" />
                  Table Summary
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-text-secondary">Rows</dt>
                      <dd className="text-lg font-semibold text-text-primary">
                        {displayData.rowCount ? displayData.rowCount.toLocaleString() : 'Unknown'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-text-secondary">Columns</dt>
                      <dd className="text-lg font-semibold text-text-primary">
                        {displayData.columns ? displayData.columns.length : 'Unknown'}
                      </dd>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <dt className="text-sm font-medium text-text-secondary">Type</dt>
                      <dd className="text-lg font-semibold text-text-primary capitalize">
                        {displayData.type || 'Table'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-text-secondary">Size</dt>
                      <dd className="text-lg font-semibold text-text-primary">
                        {displayData.size || 'Unknown'}
                      </dd>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick stats merged */}
              {displayData.columns && displayData.columns.length > 0 && (
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="text-center">
                    <div className="text-xl font-bold text-primary">
                      {displayData.columns.filter(col => col.primaryKey === true).length}
                    </div>
                    <div className="text-sm text-text-secondary">Primary Keys</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-accent">
                      {displayData.columns.filter(col => col.foreignKey === true).length}
                    </div>
                    <div className="text-sm text-text-secondary">Foreign Keys</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-secondary">
                      {displayData.columns.filter(col => col.nullable === false).length}
                    </div>
                    <div className="text-sm text-text-secondary">Required</div>
                  </div>
                </div>
              )}

              {/* Table Insights Section */}
              {(displayData.domain || displayData.table_insights || displayData.purpose || displayData.usage_patterns || displayData.business_use_cases) && (
                <div className="bg-surface-secondary rounded-lg border border-border p-6">
                  <h3 className="text-lg font-semibold text-text-primary mb-6 flex items-center">
                    <Icon name="Lightbulb" size={20} className="mr-2" />
                    Table Insights
                  </h3>
                  
                  <div className="space-y-6">
                    {/* Domain and Category */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-center space-x-2 mb-2">
                          <Icon name="Tag" size={16} className="text-accent" />
                          <h4 className="font-medium text-text-primary">Domain</h4>
                        </div>
                        <EditableMetadata
                          value={displayData.domain || displayData.table_insights?.domain || ""}
                          field="domain"
                          onSave={(field, value) => handleMetadataUpdate(field, value)}
                          onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue)}
                          placeholder="Add domain classification..."
                          type="text"
                        />
                      </div>
                      
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-center space-x-2 mb-2">
                          <Icon name="Folder" size={16} className="text-secondary" />
                          <h4 className="font-medium text-text-primary">Category</h4>
                        </div>
                        <EditableMetadata
                          value={displayData.category || displayData.table_insights?.category || ""}
                          field="category"
                          onSave={(field, value) => handleMetadataUpdate(field, value)}
                          onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue)}
                          placeholder="Add category classification..."
                          type="text"
                        />
                      </div>
                    </div>

                    {/* Table Description */}
                    <div className="p-4 bg-surface rounded-lg border border-border">
                      <div className="flex items-center space-x-2 mb-3">
                        <Icon name="FileText" size={16} className="text-warning" />
                        <h4 className="font-medium text-text-primary">Description</h4>
                      </div>
                      <EditableMetadata
                        value={displayData.description !== `Table: ${displayData.name}` ? displayData.description : ""}
                        field="description"
                        onSave={(field, value) => handleMetadataUpdate(field, value)}
                        onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue)}
                        placeholder="Add table description..."
                        type="textarea"
                        multiline={true}
                        renderMarkdown={true}
                      />
                    </div>

                    {/* Purpose */}
                    <div className="p-4 bg-surface rounded-lg border border-border">
                      <div className="flex items-center space-x-2 mb-3">
                        <Icon name="Target" size={16} className="text-primary" />
                        <h4 className="font-medium text-text-primary">Purpose</h4>
                      </div>
                      <EditableMetadata
                        value={displayData.purpose || 
                               displayData.table_insights?.purpose || 
                               displayData.table_description?.purpose || ""}
                        field="purpose"
                        onSave={(field, value) => handleMetadataUpdate(field, value)}
                        onAIUpdate={(field, feedback, currentValue) => handleAIMetadataUpdate(field, feedback, currentValue)}
                        placeholder="Describe the purpose of this table..."
                        type="textarea"
                        multiline={true}
                      />
                    </div>

                    {/* Usage Patterns */}
                    {(displayData.usage_patterns || displayData.business_use_cases) && 
                     (displayData.usage_patterns || displayData.business_use_cases).length > 0 && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-center space-x-2 mb-3">
                          <Icon name="Activity" size={16} className="text-success" />
                          <h4 className="font-medium text-text-primary">Usage Patterns</h4>
                        </div>
                        <div className="space-y-2">
                          {(displayData.usage_patterns || displayData.business_use_cases).slice(0, 4).map((useCase, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface-secondary rounded-lg border border-border">
                              <div className="text-success mt-0.5">
                                <Icon name="CheckCircle" size={14} />
                              </div>
                              <p className="text-text-secondary text-sm flex-1">{useCase}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Data Lifecycle */}
                    {displayData.data_lifecycle && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-center space-x-2 mb-3">
                          <Icon name="Clock" size={16} className="text-info" />
                          <h4 className="font-medium text-text-primary">Data Lifecycle</h4>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <h5 className="text-sm font-medium text-text-primary mb-2">Update Frequency</h5>
                            <p className="text-text-secondary text-sm">
                              {displayData.data_lifecycle.update_frequency || 'Not specified'}
                            </p>
                          </div>
                          <div>
                            <h5 className="text-sm font-medium text-text-primary mb-2">Retention Policy</h5>
                            <p className="text-text-secondary text-sm">
                              {displayData.data_lifecycle.retention_policy || 'Not specified'}
                            </p>
                          </div>
                          <div>
                            <h5 className="text-sm font-medium text-text-primary mb-2">Archival Strategy</h5>
                            <p className="text-text-secondary text-sm">
                              {displayData.data_lifecycle.archival_strategy || 'Not defined'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Additional Insights */}
              {displayData.additional_insights && (
                <div className="bg-surface-secondary rounded-lg border border-border p-6">
                  <h3 className="text-lg font-semibold text-text-primary mb-6 flex items-center">
                    <Icon name="Sparkles" size={20} className="mr-2" />
                    Additional Insights
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    {/* Data Patterns */}
                    {displayData.additional_insights.data_patterns && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center">
                          <Icon name="TrendingUp" size={14} className="text-success mr-2" />
                          Data Patterns
                        </h4>
                        <p className="text-text-secondary text-sm">{displayData.additional_insights.data_patterns}</p>
                      </div>
                    )}

                    {/* Domain Specific Notes */}
                    {displayData.additional_insights.domain_specific_notes && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center">
                          <Icon name="Info" size={14} className="text-accent mr-2" />
                          Domain Insights
                        </h4>
                        <p className="text-text-secondary text-sm">{displayData.additional_insights.domain_specific_notes}</p>
                      </div>
                    )}

                    {/* Integration Considerations */}
                    {displayData.additional_insights.integration_considerations && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center">
                          <Icon name="Link" size={14} className="text-primary mr-2" />
                          Integration Considerations
                        </h4>
                        <p className="text-text-secondary text-sm">{displayData.additional_insights.integration_considerations}</p>
                      </div>
                    )}

                    {/* Governance Notes */}
                    {displayData.additional_insights.governance_notes && (
                      <div className="p-4 bg-surface rounded-lg border border-border">
                        <h4 className="text-sm font-medium text-text-primary mb-2 flex items-center">
                          <Icon name="Shield" size={14} className="text-warning mr-2" />
                          Data Governance
                        </h4>
                        <p className="text-text-secondary text-sm">{displayData.additional_insights.governance_notes}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Last Updated */}
              {displayData.lastUpdated && displayData.lastUpdated !== 'Unknown' && (
                <div className="text-center">
                  <p className="text-sm text-text-muted">
                    Last updated: {displayData.lastUpdated}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'columns' && (
          <div className="h-full flex flex-col">
            {/* Search */}
            <div className="p-4 border-b border-border">
              <Input
                type="text"
                placeholder="Search columns..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                iconName="Search"
                className="w-full"
              />
            </div>

            {/* Columns List */}
            <div className="flex-1 overflow-y-auto">
              {filteredColumns.length === 0 ? (
                <div className="text-center py-8">
                  <Icon name="Columns" size={48} className="text-text-muted mx-auto mb-4" />
                  <p className="text-text-secondary">No columns found</p>
                </div>
              ) : (
                <div className="space-y-2 p-4">
                  {filteredColumns.map((column, index) => renderColumnCard(column, index))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'indexes' && (
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              {displayData.indexes && displayData.indexes.length > 0 ? (
                <div className="space-y-2">
                  {displayData.indexes.map((index, indexIdx) => (
                    <div key={indexIdx} className="p-4 bg-surface-secondary rounded-lg border border-border">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-text-primary">
                          {index.type === 'PARTITION' ? 'Table Partition' : 
                           index.type === 'CLUSTERING' ? 'Clustering Keys' : 
                           index.name}
                        </h4>
                        <div className="flex items-center space-x-2">
                          {index.is_unique && (
                            <span className="text-xs px-2 py-1 bg-warning text-warning-foreground rounded">
                              UNIQUE
                            </span>
                          )}
                          {index.is_primary && (
                            <span className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded">
                              PRIMARY
                            </span>
                          )}
                          <span className={`text-xs px-2 py-1 rounded ${
                            index.type === 'PARTITION' ? 'bg-blue-100 text-blue-800' :
                            index.type === 'CLUSTERING' ? 'bg-purple-100 text-purple-800' :
                            'bg-accent text-accent-foreground'
                          }`}>
                            {index.index_type || index.type || 'INDEX'}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-text-secondary mt-1">
                        {index.type === 'PARTITION' ? 'Partitioned by: ' :
                         index.type === 'CLUSTERING' ? 'Clustered by: ' :
                         'Columns: '}
                        {Array.isArray(index.columns) ? index.columns.join(', ') : index.columns}
                      </p>
                      {index.type === 'PARTITION' && (
                        <p className="text-xs text-text-muted mt-1">
                          Improves query performance by reducing data scanned
                        </p>
                      )}
                      {index.type === 'CLUSTERING' && (
                        <p className="text-xs text-text-muted mt-1">
                          Optimizes queries with WHERE clauses on these columns
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Icon name="Key" size={48} className="text-text-muted mx-auto mb-4" />
                  <p className="text-text-secondary">No indexes found</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'sample' && (
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              {sampleDataLoading ? (
                // Loading state
                <div className="text-center py-8">
                  <div className="flex flex-col items-center space-y-4">
                    <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                    <div>
                      <p className="text-text-primary font-medium">Fetching Sample Data</p>
                      <p className="text-text-secondary text-sm">Loading data from {selectedTable?.name}...</p>
                    </div>
                  </div>
                </div>
              ) : sampleDataError ? (
                // Error state
                <div className="text-center py-8">
                  <Icon name="AlertCircle" size={48} className="text-destructive mx-auto mb-4" />
                  <p className="text-text-primary font-medium mb-2">Failed to Load Sample Data</p>
                  <p className="text-text-secondary text-sm mb-4">{sampleDataError}</p>
                  <button
                    onClick={fetchSampleData}
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                  >
                    <Icon name="RefreshCw" size={16} />
                    <span>Try Again</span>
                  </button>
                </div>
              ) : (() => {
                // Determine which sample data to show
                const sampleData = displayData?.sampleData?.length > 0 
                  ? displayData.sampleData 
                  : fetchedSampleData?.sample_data || [];
                
                return sampleData.length > 0 ? (
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <Icon name="Table" size={16} className="text-primary" />
                        <h3 className="font-semibold text-text-primary">Sample Data</h3>
                        {fetchedSampleData && !displayData?.sampleData?.length && (
                          <span className="text-xs bg-accent/10 text-accent px-2 py-1 rounded">
                            Fetched on demand
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-xs text-text-muted bg-surface-secondary px-2 py-1 rounded">
                          {Math.min(sampleData.length, 2)} rows
                        </span>
                        <button
                          onClick={fetchSampleData}
                          disabled={sampleDataLoading}
                          className="text-xs text-text-muted hover:text-text-primary flex items-center space-x-1"
                        >
                          <Icon name="RefreshCw" size={12} />
                          <span>Refresh</span>
                        </button>
                      </div>
                    </div>

                    {/* Transposed Grid */}
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm border border-border rounded-lg">
                        <thead className="bg-surface-secondary">
                          <tr>
                            <th className="px-4 py-3 text-left font-medium text-text-primary border-b border-border min-w-[200px]">
                              Column
                            </th>
                            {sampleData.slice(0, 2).map((_, rowIndex) => (
                              <th key={rowIndex} className="px-4 py-3 text-left font-medium text-text-primary border-b border-border min-w-[150px]">
                                Row {rowIndex + 1}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {/* Each column becomes a row */}
                          {Object.keys(sampleData[0]).map((columnName, colIndex) => (
                            <tr key={columnName} className="hover:bg-surface-secondary">
                              {/* Column name */}
                              <td className="px-4 py-3 font-medium text-text-primary border-b border-border bg-surface-secondary/50">
                                <div className="flex items-center space-x-2">
                                  <Icon name="Database" size={14} className="text-accent" />
                                  <span>{columnName}</span>
                                </div>
                              </td>
                              {/* Values for this column across the 2 rows */}
                              {sampleData.slice(0, 2).map((row, rowIndex) => {
                                const value = row[columnName];
                                const valueStr = value !== null && value !== undefined ? String(value) : null;
                                const truncatedValue = valueStr && valueStr.length > 100 
                                  ? valueStr.substring(0, 100) + '...' 
                                  : valueStr;
                                
                                return (
                                  <td key={rowIndex} className="px-4 py-3 text-text-secondary border-b border-border">
                                    <div className="flex items-center space-x-2">
                                      <span 
                                        className={`font-mono text-sm bg-surface px-2 py-1 rounded border ${
                                          valueStr && valueStr.length > 100 ? 'cursor-help border-dashed' : ''
                                        }`}
                                        title={valueStr && valueStr.length > 100 ? valueStr : undefined}
                                      >
                                        {valueStr !== null ? truncatedValue : (
                                          <span className="text-text-muted italic">null</span>
                                        )}
                                      </span>
                                      {/* Data type indicator */}
                                      <span className="text-xs text-text-muted">
                                        {value === null || value === undefined ? 'null' : 
                                         typeof value === 'number' ? 'num' :
                                         typeof value === 'boolean' ? 'bool' :
                                         value instanceof Date ? 'date' : 'str'}
                                      </span>
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Sample Data Statistics */}
                    <div className="mt-4 p-3 bg-surface-secondary rounded-lg border border-border">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-text-secondary">
                          Showing {Math.min(sampleData.length, 2)} of {sampleData.length} sample rows
                        </span>
                        <div className="flex items-center space-x-4">
                          <span className="text-text-muted">
                            {Object.keys(sampleData[0]).length} columns
                          </span>
                          <span className="text-text-muted">
                            {fetchedSampleData ? 'Fetched on demand' : 'Generated from metadata analysis'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  // Empty state
                  <div className="text-center py-8">
                    <Icon name="Table" size={48} className="text-text-muted mx-auto mb-4" />
                    <p className="text-text-secondary mb-2">No sample data available</p>
                    <p className="text-text-muted text-sm mb-4">Click below to fetch sample data from this table</p>
                    <button
                      onClick={fetchSampleData}
                      disabled={sampleDataLoading}
                      className="inline-flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                      <Icon name="Download" size={16} />
                      <span>Fetch Sample Data</span>
                    </button>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {activeTab === 'categorical' && (
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              
              {/* Categorical Definitions */}
              {displayData.categorical_definitions && Object.keys(displayData.categorical_definitions).length > 0 && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="Tag" size={18} className="text-accent" />
                    <h3 className="text-lg font-semibold text-text-primary">Categorical Definitions</h3>
                  </div>
                  <div className="space-y-4">
                    {Object.entries(displayData.categorical_definitions).map(([column, definitions]) => (
                      <div key={column} className="p-4 bg-surface rounded-lg border border-border">
                        <h4 className="font-medium text-text-primary mb-3 flex items-center">
                          <Icon name="Database" size={14} className="text-accent mr-2" />
                          {column}
                        </h4>
                        <div className="space-y-2">
                          {Object.entries(definitions).map(([value, definition]) => (
                            <div key={value} className="flex items-start space-x-3 p-2 bg-surface-secondary rounded border">
                              <span className="font-mono text-xs bg-surface px-2 py-1 rounded border text-text-primary">
                                {value}
                              </span>
                              <span className="text-sm text-text-secondary flex-1">{definition}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!displayData.categorical_definitions && (
                <div className="text-center py-12">
                  <Icon name="MoreHorizontal" size={48} className="text-text-muted mx-auto mb-4" />
                  <p className="text-text-secondary mb-2">No categorical content available</p>
                  <p className="text-text-muted text-sm">Generate metadata with additional options to see categorical definitions</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'misc' && (
          <div className="h-full flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              
              {/* Business Rules */}
              {displayData.business_rules && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="Shield" size={18} className="text-primary" />
                    <h3 className="text-lg font-semibold text-text-primary">Business Rules</h3>
                  </div>
                  <div className="space-y-4">
                    
                    {/* Data Quality Rules */}
                    {displayData.business_rules.data_quality_rules && 
                     displayData.business_rules.data_quality_rules.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Data Quality Rules</h4>
                        <div className="space-y-2">
                          {displayData.business_rules.data_quality_rules.map((rule, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="CheckSquare" size={14} className="text-success mt-1" />
                              <p className="text-text-secondary text-sm">{rule}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Business Constraints */}
                    {displayData.business_rules.business_constraints && 
                     displayData.business_rules.business_constraints.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Business Constraints</h4>
                        <div className="space-y-2">
                          {displayData.business_rules.business_constraints.map((constraint, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="Lock" size={14} className="text-warning mt-1" />
                              <p className="text-text-secondary text-sm">{constraint}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Validation Recommendations */}
                    {displayData.business_rules.validation_recommendations && 
                     displayData.business_rules.validation_recommendations.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Validation Recommendations</h4>
                        <div className="space-y-2">
                          {displayData.business_rules.validation_recommendations.map((validation, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="AlertTriangle" size={14} className="text-accent mt-1" />
                              <p className="text-text-secondary text-sm">{validation}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Performance Optimization */}
              {displayData.performance_optimization && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="Zap" size={18} className="text-warning" />
                    <h3 className="text-lg font-semibold text-text-primary">Performance Optimization</h3>
                  </div>
                  <div className="space-y-4">
                    
                    {/* Indexing Recommendations */}
                    {displayData.performance_optimization.indexing_recommendations && 
                     displayData.performance_optimization.indexing_recommendations.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Indexing Recommendations</h4>
                        <div className="space-y-2">
                          {displayData.performance_optimization.indexing_recommendations.map((rec, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="Database" size={14} className="text-primary mt-1" />
                              <p className="text-text-secondary text-sm">{rec}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Query Patterns */}
                    {displayData.performance_optimization.query_patterns && 
                     displayData.performance_optimization.query_patterns.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Query Patterns</h4>
                        <div className="space-y-2">
                          {displayData.performance_optimization.query_patterns.map((pattern, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="Search" size={14} className="text-accent mt-1" />
                              <p className="text-text-secondary text-sm">{pattern}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Performance Considerations */}
                    {displayData.performance_optimization.performance_considerations && 
                     displayData.performance_optimization.performance_considerations.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-text-primary mb-3">Performance Considerations</h4>
                        <div className="space-y-2">
                          {displayData.performance_optimization.performance_considerations.map((consideration, idx) => (
                            <div key={idx} className="flex items-start space-x-3 p-3 bg-surface rounded-lg border border-border">
                              <Icon name="TrendingUp" size={14} className="text-success mt-1" />
                              <p className="text-text-secondary text-sm">{consideration}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Query Examples */}
              {displayData.query_examples && displayData.query_examples.length > 0 && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="Code" size={18} className="text-accent" />
                    <h3 className="text-lg font-semibold text-text-primary">Query Examples</h3>
                  </div>
                  <div className="space-y-4">
                    {displayData.query_examples.map((example, idx) => (
                      <div key={idx} className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-medium text-text-primary">{example.name}</h4>
                          <span className="text-xs text-text-muted bg-surface-secondary px-2 py-1 rounded">
                            {example.frequency || 'As needed'}
                          </span>
                        </div>
                        <p className="text-sm text-text-secondary mb-3">{example.description}</p>
                        <div className="mb-2">
                          <span className="text-xs font-medium text-text-primary">Use Case: </span>
                          <span className="text-xs text-text-muted">{example.use_case}</span>
                        </div>
                        <div className="bg-surface-secondary rounded border p-3">
                          <code className="text-xs text-text-primary whitespace-pre-wrap font-mono">
                            {example.sql}
                          </code>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Aggregation Rules */}
              {displayData.aggregation_rules && displayData.aggregation_rules.length > 0 && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="BarChart3" size={18} className="text-secondary" />
                    <h3 className="text-lg font-semibold text-text-primary">Aggregation Rules</h3>
                  </div>
                  <div className="space-y-4">
                    {displayData.aggregation_rules.map((rule, idx) => (
                      <div key={idx} className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-medium text-text-primary">{rule.rule_name}</h4>
                          <span className="text-xs text-text-muted bg-surface-secondary px-2 py-1 rounded">
                            {rule.use_case}
                          </span>
                        </div>
                        <p className="text-sm text-text-secondary mb-3">{rule.description}</p>
                        {rule.business_value && (
                          <div className="mb-2">
                            <span className="text-xs font-medium text-text-primary">Business Value: </span>
                            <span className="text-xs text-text-muted">{rule.business_value}</span>
                          </div>
                        )}
                        {rule.sql_pattern && (
                          <div className="bg-surface-secondary rounded border p-3">
                            <code className="text-xs text-text-primary whitespace-pre-wrap font-mono">
                              {rule.sql_pattern}
                            </code>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Relationships */}
              {displayData.relationships && displayData.relationships.length > 0 && (
                <div className="bg-surface-secondary rounded-lg border border-border p-4">
                  <div className="flex items-center space-x-2 mb-4">
                    <Icon name="GitBranch" size={18} className="text-info" />
                    <h3 className="text-lg font-semibold text-text-primary">Relationships</h3>
                  </div>
                  <div className="space-y-3">
                    {displayData.relationships.map((rel, idx) => (
                      <div key={idx} className="p-4 bg-surface rounded-lg border border-border">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-text-primary">{rel.relates_to}</h4>
                          <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                            {rel.relationship_type}
                          </span>
                        </div>
                        <p className="text-xs text-text-muted mb-2">Column: {rel.column}</p>
                        <p className="text-sm text-text-secondary">{rel.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {!displayData.business_rules && !displayData.performance_optimization && 
               !displayData.query_examples && !displayData.aggregation_rules && 
               !displayData.relationships && (
                <div className="text-center py-12">
                  <Icon name="MoreHorizontal" size={48} className="text-text-muted mx-auto mb-4" />
                  <p className="text-text-secondary mb-2">No miscellaneous content available</p>
                  <p className="text-text-muted text-sm">Generate metadata with additional options to see business rules, query examples, and more</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TableDetails;