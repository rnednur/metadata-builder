import React, { useState } from 'react';
import { Layout, Menu, Switch, Avatar, Dropdown, Typography, Badge } from 'antd';
import type { MenuProps } from 'antd';
import {
  DatabaseOutlined,
  SearchOutlined,
  FileTextOutlined,
  CodeOutlined,
  BarChartOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BellOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  children?: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <BarChartOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/databases',
      icon: <DatabaseOutlined />,
      label: 'Database Connections',
    },
    {
      key: '/explorer',
      icon: <SearchOutlined />,
      label: 'Schema Explorer',
    },
    {
      key: '/metadata',
      icon: <FileTextOutlined />,
      label: 'Metadata Generation',
    },
    {
      key: '/lookml',
      icon: <CodeOutlined />,
      label: 'LookML',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics Dashboard',
    },
  ];

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      danger: true,
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      localStorage.removeItem('auth_token');
      navigate('/login');
    } else {
      navigate(`/${key}`);
    }
  };

  const selectedKeys = [location.pathname];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme={darkMode ? 'dark' : 'light'}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
            marginBottom: 16,
          }}
        >
          <DatabaseOutlined
            style={{
              fontSize: collapsed ? 24 : 32,
              color: '#1890ff',
              marginRight: collapsed ? 0 : 8,
            }}
          />
          {!collapsed && (
            <Text strong style={{ fontSize: 16, color: '#1890ff' }}>
              Metadata Builder
            </Text>
          )}
        </div>

        <div style={{ padding: collapsed ? 0 : '0 16px', marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {collapsed ? '' : 'Navigation'}
          </Text>
        </div>

        <Menu
          theme={darkMode ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={selectedKeys}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0 }}
        />

        <div
          style={{
            position: 'absolute',
            bottom: 16,
            left: 0,
            right: 0,
            padding: collapsed ? '0 8px' : '0 16px',
          }}
        >
          <div
            style={{
              padding: collapsed ? 8 : 16,
              backgroundColor: darkMode ? '#1f1f1f' : '#f5f5f5',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: collapsed ? 'center' : 'space-between',
            }}
          >
            <SettingOutlined
              style={{
                fontSize: 16,
                color: '#666',
                marginRight: collapsed ? 0 : 8,
              }}
            />
            {!collapsed && (
              <Text type="secondary" style={{ fontSize: 14 }}>
                Settings
              </Text>
            )}
          </div>
        </div>
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid #f0f0f0',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <DatabaseOutlined
              style={{ fontSize: 24, color: '#1890ff', marginRight: 12 }}
            />
            <div>
              <Text strong style={{ fontSize: 18 }}>
                Metadata Builder
              </Text>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Badge status="success" />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Normal Mode
                </Text>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <SunOutlined style={{ color: darkMode ? '#666' : '#1890ff' }} />
              <Switch
                size="small"
                checked={darkMode}
                onChange={setDarkMode}
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {darkMode ? 'Dark' : 'Normal'} Mode
              </Text>
            </div>

            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18, color: '#666' }} />
            </Badge>

            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleUserMenuClick,
              }}
              placement="bottomRight"
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: 6,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
              >
                <Avatar size="small" icon={<UserOutlined />} />
                <Text strong style={{ fontSize: 14 }}>
                  JD
                </Text>
                <Badge status="success" />
              </div>
            </Dropdown>
          </div>
        </Header>

        <Content
          style={{
            margin: 0,
            minHeight: 'calc(100vh - 64px)',
            background: '#f5f5f5',
            overflow: 'auto',
          }}
        >
          {children || <Outlet />}
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout; 