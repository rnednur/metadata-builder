import React from 'react';
import { ConfigProvider, theme } from 'antd';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import MainLayout from './components/Layout/MainLayout';
import DashboardPage from './pages/DashboardPage';
import MetadataPage from './pages/MetadataPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <Router>
          <MainLayout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/databases" element={<div style={{ padding: 24 }}>Database Connections - Coming Soon</div>} />
              <Route path="/explorer" element={<div style={{ padding: 24 }}>Schema Explorer - Coming Soon</div>} />
              <Route path="/metadata" element={<MetadataPage />} />
              <Route path="/lookml" element={<div style={{ padding: 24 }}>LookML Generation - Coming Soon</div>} />
              <Route path="/analytics" element={<div style={{ padding: 24 }}>Analytics Dashboard - Coming Soon</div>} />
              <Route path="/settings" element={<div style={{ padding: 24 }}>Settings - Coming Soon</div>} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </MainLayout>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
