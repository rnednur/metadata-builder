import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet';
import Header from '../../components/ui/Header';
import Sidebar from '../../components/ui/Sidebar';
import Breadcrumb from '../../components/ui/Breadcrumb';
import ConnectionCard from './components/ConnectionCard';
import ConnectionList from './components/ConnectionList';
import ConnectionToolbar from './components/ConnectionToolbar';
import SystemHealthSidebar from './components/SystemHealthSidebar';
import DeleteConnectionModal from './components/DeleteConnectionModal';
import SchemaFilterModal from '../../components/SchemaFilterModal';
import { databaseAPI, systemAPI, apiUtils } from '../../services/api';

const DatabaseConnectionsDashboard = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isHealthSidebarCollapsed, setIsHealthSidebarCollapsed] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid');
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, connection: null });
  const [schemaFilterModal, setSchemaFilterModal] = useState({ isOpen: false, connection: null });
  const [isDeleting, setIsDeleting] = useState(false);
  const [connections, setConnections] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Health metrics state - will be loaded from backend API
  const [healthMetrics, setHealthMetrics] = useState({
    connections: {
      active: 0,
      total: 0,
      status: 'unknown'
    },
    jobs: [],
    agents: {
      status: 'unknown',
      list: []
    },
    resources: {
      cpu: 0,
      memory: 0
    }
  });

  // Load connections on component mount
  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await databaseAPI.listConnections();
      const formattedConnections = response.data.map(apiUtils.formatConnectionData);
      setConnections(formattedConnections);

      // Update health metrics based on real connection data
      const activeConnections = formattedConnections.filter(conn => conn.status === 'connected').length;
      setHealthMetrics(prev => ({
        ...prev,
        connections: {
          active: activeConnections,
          total: formattedConnections.length,
          status: formattedConnections.length > 0 ? (activeConnections > 0 ? 'healthy' : 'warning') : 'unknown'
        }
      }));

    } catch (err) {
      setError(apiUtils.handleApiError(err));
      console.error('Failed to load connections:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter connections based on search query
  const filteredConnections = useMemo(() => {
    if (!searchQuery.trim()) return connections;
    
    return connections.filter(connection =>
      connection.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connection.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connection.host.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connection.database.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [connections, searchQuery]);

  const breadcrumbItems = [
    { label: 'Connections', path: '/database-connections-dashboard' }
  ];

  const handleConnect = async (connection) => {
    try {
      // Update connection status to connecting
      setConnections(prev => prev.map(conn => 
        conn.id === connection.id 
          ? { ...conn, status: 'connecting' }
          : conn
      ));

      // Test the connection
      const response = await databaseAPI.testConnection(connection.name);
      const testResult = response.data;

      if (testResult.status === 'success') {
        setConnections(prev => prev.map(conn => 
          conn.id === connection.id 
            ? { ...conn, status: 'connected', lastUsed: new Date() }
            : conn
        ));
        
        // Navigate to schema explorer
        navigate('/schema-explorer', { 
          state: { connectionId: connection.id, connectionName: connection.name }
        });
      } else {
        setConnections(prev => prev.map(conn => 
          conn.id === connection.id 
            ? { ...conn, status: 'disconnected' }
            : conn
        ));
        setError(`Connection test failed: ${testResult.message}`);
      }
    } catch (err) {
      setConnections(prev => prev.map(conn => 
        conn.id === connection.id 
          ? { ...conn, status: 'disconnected' }
          : conn
      ));
      setError(apiUtils.handleApiError(err));
    }
  };

  const handleEdit = (connection) => {
    navigate('/add-edit-database-connection', { 
      state: { connection, mode: 'edit' }
    });
  };

  const handleDelete = (connection) => {
    setDeleteModal({ isOpen: true, connection });
  };

  const handleConfirmDelete = async (connectionId) => {
    try {
      setIsDeleting(true);
      
      // Get the connection name from the modal
      const connectionName = deleteModal.connection?.name;
      if (!connectionName) {
        throw new Error('Connection name not found');
      }

      // Delete the connection
      await databaseAPI.deleteConnection(connectionName);
      
      // Remove from local state
      setConnections(prev => prev.filter(conn => conn.id !== connectionId));
      setDeleteModal({ isOpen: false, connection: null });
      
    } catch (err) {
      setError(apiUtils.handleApiError(err));
      console.error('Failed to delete connection:', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancelDelete = () => {
    setDeleteModal({ isOpen: false, connection: null });
  };

  const handleConfigureSchemas = (connection) => {
    setSchemaFilterModal({ isOpen: true, connection });
  };

  const handleSchemaFilterClose = (saved) => {
    setSchemaFilterModal({ isOpen: false, connection: null });
    // If changes were saved, we could optionally refresh connection data
    if (saved) {
      console.log('Schema filter configuration saved');
    }
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleHealthSidebar = () => {
    setIsHealthSidebarCollapsed(!isHealthSidebarCollapsed);
  };

  return (
    <div className="min-h-screen bg-background">
      <Helmet>
        <title>Database Connections Dashboard - Metadata Builder</title>
        <meta name="description" content="Manage and monitor your database connections with real-time status updates and system health metrics." />
      </Helmet>

      <Header 
        onMenuToggle={toggleSidebar} 
        isMenuOpen={isSidebarOpen} 
        isSidebarCollapsed={isSidebarCollapsed}
      />
      <Sidebar 
        isOpen={isSidebarOpen} 
        onClose={() => setIsSidebarOpen(false)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapse}
      />

      <main className={`pt-16 ${isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
        <div className="p-6">
          {/* Breadcrumb */}
          <div className="mb-6">
            <Breadcrumb items={breadcrumbItems} />
          </div>

          {/* Toolbar */}
          <ConnectionToolbar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            connectionCount={filteredConnections.length}
          />

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-red-800 font-medium">Error</p>
                  <p className="text-red-700">{error}</p>
                </div>
                <button
                  onClick={() => setError(null)}
                  className="ml-auto p-1 text-red-500 hover:text-red-700"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Loading Display */}
          {isLoading && (
            <div className="text-center py-12">
              <div className="inline-flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-lg text-text-secondary">Loading connections...</span>
              </div>
            </div>
          )}

          {/* Main Content */}
          {!isLoading && (
            <div className={`${!isHealthSidebarCollapsed ? 'lg:pr-84' : ''} transition-all duration-300`}>
              {filteredConnections.length > 0 ? (
                viewMode === 'grid' ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    {filteredConnections.map((connection) => (
                      <ConnectionCard
                        key={connection.id}
                        connection={connection}
                        onConnect={handleConnect}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onConfigureSchemas={handleConfigureSchemas}
                      />
                    ))}
                  </div>
                ) : (
                  <ConnectionList
                    connections={filteredConnections}
                    onConnect={handleConnect}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onConfigureSchemas={handleConfigureSchemas}
                  />
                )
              ) : searchQuery ? (
                <div className="text-center py-12">
                  <div className="text-text-muted mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-text-primary mb-2">No connections found</h3>
                  <p className="text-text-secondary">
                    No connections match your search for "{searchQuery}". Try adjusting your search terms.
                  </p>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-text-muted mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-text-primary mb-2">No database connections</h3>
                  <p className="text-text-secondary mb-6">
                    Get started by creating your first database connection to begin generating metadata.
                  </p>
                  <button
                    onClick={() => navigate('/add-edit-database-connection')}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Add Database Connection
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* System Health Sidebar */}
      <SystemHealthSidebar
        isCollapsed={isHealthSidebarCollapsed}
        onToggle={toggleHealthSidebar}
        healthMetrics={healthMetrics}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConnectionModal
        isOpen={deleteModal.isOpen}
        connection={deleteModal.connection}
        onConfirm={handleConfirmDelete}
        onCancel={handleCancelDelete}
        isDeleting={isDeleting}
      />

      {/* Schema Filter Modal */}
      <SchemaFilterModal
        isOpen={schemaFilterModal.isOpen}
        connectionName={schemaFilterModal.connection?.name}
        onClose={handleSchemaFilterClose}
      />
    </div>
  );
};

export default DatabaseConnectionsDashboard;