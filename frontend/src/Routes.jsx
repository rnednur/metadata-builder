import React from "react";
import { BrowserRouter, Routes as RouterRoutes, Route } from "react-router-dom";
import ScrollToTop from "components/ScrollToTop";
import ErrorBoundary from "components/ErrorBoundary";
import ProtectedRoute from "components/ProtectedRoute";
// Add your imports here
import LoginPage from "pages/login";
import DatabaseConnectionsDashboard from "pages/database-connections-dashboard";
import AddEditDatabaseConnection from "pages/add-edit-database-connection";
import SchemaExplorer from "pages/schema-explorer";
import AiChatInterface from "pages/ai-chat-interface";
import JobQueueManagement from "pages/job-queue-management";
import MetadataGeneration from "pages/metadata-generation";
import NotFound from "pages/NotFound";

const Routes = () => {
  return (
    <BrowserRouter>
      <ErrorBoundary>
      <ScrollToTop />
      <RouterRoutes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <DatabaseConnectionsDashboard />
          </ProtectedRoute>
        } />
        <Route path="/database-connections-dashboard" element={
          <ProtectedRoute>
            <DatabaseConnectionsDashboard />
          </ProtectedRoute>
        } />
        <Route path="/add-edit-database-connection" element={
          <ProtectedRoute>
            <AddEditDatabaseConnection />
          </ProtectedRoute>
        } />
        <Route path="/schema-explorer" element={
          <ProtectedRoute>
            <SchemaExplorer />
          </ProtectedRoute>
        } />
        <Route path="/ai-chat-interface" element={
          <ProtectedRoute>
            <AiChatInterface />
          </ProtectedRoute>
        } />
        <Route path="/job-queue-management" element={
          <ProtectedRoute>
            <JobQueueManagement />
          </ProtectedRoute>
        } />
        <Route path="/metadata-generation" element={
          <ProtectedRoute>
            <MetadataGeneration />
          </ProtectedRoute>
        } />
        
        {/* 404 page */}
        <Route path="*" element={<NotFound />} />
      </RouterRoutes>
      </ErrorBoundary>
    </BrowserRouter>
  );
};

export default Routes;