import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Icon from '../AppIcon';
import Button from './Button';
import { useJobs } from '../../contexts/JobContext';

const Sidebar = ({ isOpen, onClose, isCollapsed = false, onToggleCollapse }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { totalJobs, hasActiveJobs, jobs } = useJobs();
  const activeJobsCount = jobs.filter(job => job.status === 'running' || job.status === 'pending').length;
  const [connectionStatus, setConnectionStatus] = useState({
    connected: 2,
    total: 3,
    status: 'healthy'
  });

  const navigationItems = [
    {
      id: 'connections',
      label: 'Connections',
      icon: 'Database',
      path: '/database-connections-dashboard'
    },
    {
      id: 'explore',
      label: 'Explore',
      path: '/schema-explorer',
      icon: 'Search'
    },
    {
      id: 'generate',
      label: 'Generate',
      path: '/metadata-generation',
      icon: 'Sparkles',
      badge: activeJobsCount > 0 ? activeJobsCount : null
    },
    {
      id: 'monitor',
      label: 'Monitor',
      path: '/job-queue-management',
      icon: 'Activity',
      badge: totalJobs > 0 ? totalJobs : null
    }
    // {
    //   id: 'chat',
    //   label: 'Chat',
    //   path: '/ai-chat-interface',
    //   icon: 'MessageSquare'
    // }
  ];

  const handleNavigation = (path) => {
    if (path) {
      navigate(path);
      if (window.innerWidth < 1024) {
        onClose();
      }
    }
  };

  const isActiveRoute = (path) => {
    return location.pathname === path;
  };

  const isParentActive = (item) => {
    if (item.children) {
      return item.children.some(child => isActiveRoute(child.path));
    }
    return false;
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus.status) {
      case 'healthy':
        return 'text-success';
      case 'warning':
        return 'text-warning';
      case 'error':
        return 'text-error';
      default:
        return 'text-text-muted';
    }
  };

  const Logo = () => (
    <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'}`}>
      <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
        <Icon name="Database" size={20} className="text-white" />
      </div>
      {!isCollapsed && (
        <div className="flex flex-col">
          <span className="text-lg font-semibold text-text-primary">Metadata</span>
          <span className="text-sm text-text-secondary -mt-1">Builder</span>
        </div>
      )}
    </div>
  );

  const ConnectionStatus = () => (
    <div className={`px-4 py-3 bg-surface-secondary rounded-lg ${isCollapsed ? 'px-2' : ''}`}>
      {isCollapsed ? (
        <div className="flex flex-col items-center space-y-1">
          <div className={`w-3 h-3 rounded-full ${getConnectionStatusColor()}`}>
            <div className="w-full h-full rounded-full bg-current"></div>
          </div>
          <span className="text-xs font-medium text-text-primary">
            {connectionStatus.connected}/{connectionStatus.total}
          </span>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text-primary">Connections</span>
            <div className={`flex items-center space-x-1 ${getConnectionStatusColor()}`}>
              <div className="w-2 h-2 rounded-full bg-current"></div>
              <span className="text-xs font-medium">
                {connectionStatus.connected}/{connectionStatus.total}
              </span>
            </div>
          </div>
          <div className="text-xs text-text-secondary">
            {connectionStatus.connected} active connections
          </div>
        </>
      )}
    </div>
  );

  const NavItem = ({ item, level = 0 }) => {
    const [isExpanded, setIsExpanded] = useState(isParentActive(item));
    const hasChildren = item.children && item.children.length > 0;
    const isActive = item.path ? isActiveRoute(item.path) : isParentActive(item);

    const handleClick = () => {
      if (hasChildren) {
        setIsExpanded(!isExpanded);
      } else if (item.path) {
        handleNavigation(item.path);
      }
    };

    return (
      <div>
        <button
          onClick={handleClick}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-left transition-all duration-150 group ${
            isActive
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
          } ${isCollapsed ? 'justify-center' : ''}`}
          title={isCollapsed ? item.label : ''}
        >
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-3'}`}>
            <Icon 
              name={item.icon} 
              size={18} 
              className={isActive ? 'text-primary-foreground' : 'text-current'}
            />
            {!isCollapsed && (
              <span className="text-sm font-medium">{item.label}</span>
            )}
          </div>
          
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              {item.badge && (
                <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  isActive 
                    ? 'bg-primary-foreground/20 text-primary-foreground' 
                    : 'bg-accent text-accent-foreground'
                }`}>
                  {item.badge}
                </span>
              )}
              {hasChildren && (
                <Icon 
                  name="ChevronRight" 
                  size={14} 
                  className={`transition-transform duration-150 ${
                    isExpanded ? 'rotate-90' : ''
                  } ${isActive ? 'text-primary-foreground' : 'text-current'}`}
                />
              )}
            </div>
          )}
        </button>

        {hasChildren && isExpanded && !isCollapsed && (
          <div className="ml-6 mt-1 space-y-1">
            {item.children.map((child) => (
              <button
                key={child.id}
                onClick={() => handleNavigation(child.path)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-all duration-150 ${
                  isActiveRoute(child.path)
                    ? 'bg-accent text-accent-foreground shadow-sm'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-secondary'
                }`}
              >
                <Icon 
                  name={child.icon} 
                  size={16} 
                  className="text-current"
                />
                <span className="text-sm">{child.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

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
        fixed top-0 left-0 h-full bg-surface border-r border-border z-200
        transform transition-transform duration-300 ease-out-custom
        lg:translate-x-0 lg:z-100
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        ${isCollapsed ? 'w-16' : 'w-60'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className={`flex items-center justify-between p-4 border-b border-border ${isCollapsed ? 'px-2' : ''}`}>
            <Logo />
            <div className="flex items-center space-x-1">
              {onToggleCollapse && (
                <Button
                  variant="ghost"
                  onClick={onToggleCollapse}
                  className="p-2 hidden lg:block"
                  aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                  <Icon 
                    name={isCollapsed ? "ChevronRight" : "ChevronLeft"} 
                    size={16} 
                    className="text-text-secondary" 
                  />
                </Button>
              )}
              <Button
                variant="ghost"
                onClick={onClose}
                className="p-2 lg:hidden"
                aria-label="Close sidebar"
              >
                <Icon name="X" size={20} className="text-text-secondary" />
              </Button>
            </div>
          </div>

          {/* Connection Status */}
          <div className={`p-4 ${isCollapsed ? 'px-2' : ''}`}>
            <ConnectionStatus />
          </div>

          {/* Navigation */}
          <nav className={`flex-1 pb-4 ${isCollapsed ? 'px-2' : 'px-4'}`}>
            <div className="space-y-2">
              {navigationItems.map((item) => (
                <NavItem key={item.id} item={item} />
              ))}
            </div>
          </nav>

          {/* Footer */}
          <div className={`p-4 border-t border-border ${isCollapsed ? 'px-2' : ''}`}>
            <div className={`flex items-center text-xs text-text-muted ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
              {!isCollapsed && <span>v1.0.0</span>}
              <Button
                variant="ghost"
                className="p-1"
                aria-label="Help"
                title={isCollapsed ? "Help" : ""}
              >
                <Icon name="HelpCircle" size={16} className="text-text-muted" />
              </Button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;