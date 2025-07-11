import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../AppIcon';
import Button from './Button';
import authService from '../../services/authService.js';

const Header = ({ onMenuToggle, isMenuOpen, isSidebarCollapsed = false }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [user, setUser] = useState(authService.getUser());
  const [showUserMenu, setShowUserMenu] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkUser = async () => {
      if (authService.isAuthenticated()) {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      }
    };
    checkUser();
  }, []);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    console.log('Search query:', searchQuery);
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  const getUserInitials = (user) => {
    if (!user) return '?';
    if (user.first_name && user.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    return user.username?.[0]?.toUpperCase() || '?';
  };

  const getUserDisplayName = (user) => {
    if (!user) return 'User';
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    return user.username || 'User';
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-100 bg-surface border-b border-border px-4 py-3 ${isSidebarCollapsed ? 'lg:pl-16' : 'lg:pl-60'}`}>
      <div className="flex items-center justify-between">
        {/* Mobile Menu Toggle */}
        <div className="flex items-center lg:hidden">
          <Button
            variant="ghost"
            onClick={onMenuToggle}
            className="p-2 -ml-2"
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
          >
            <Icon 
              name={isMenuOpen ? 'X' : 'Menu'} 
              size={20} 
              className="text-text-secondary"
            />
          </Button>
        </div>

        {/* Search Bar - Desktop */}
        <div className="hidden md:flex flex-1 max-w-md mx-4">
          <form onSubmit={handleSearchSubmit} className="relative w-full">
            <div className={`relative flex items-center transition-all duration-150 ${
              isSearchFocused ? 'ring-2 ring-accent/20' : ''
            }`}>
              <Icon 
                name="Search" 
                size={16} 
                className="absolute left-3 text-text-muted pointer-events-none"
              />
              <input
                type="text"
                placeholder="Search databases, schemas, tables..."
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className="w-full pl-10 pr-10 py-2 text-sm bg-surface-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all duration-150"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={clearSearch}
                  className="absolute right-3 p-1 hover:bg-secondary-100 rounded transition-colors duration-150"
                >
                  <Icon name="X" size={14} className="text-text-muted" />
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center space-x-2">
          {/* Mobile Search Toggle */}
          <Button
            variant="ghost"
            className="p-2 md:hidden"
            aria-label="Search"
          >
            <Icon name="Search" size={20} className="text-text-secondary" />
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            className="p-2 relative"
            aria-label="Notifications"
          >
            <Icon name="Bell" size={20} className="text-text-secondary" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></span>
          </Button>

          {/* Settings */}
          <Button
            variant="ghost"
            className="p-2"
            aria-label="Settings"
          >
            <Icon name="Settings" size={20} className="text-text-secondary" />
          </Button>

          {/* User Profile */}
          <div className="relative">
            <Button
              variant="ghost"
              className="p-2"
              aria-label="User profile"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                {user ? (
                  <span className="text-sm font-medium text-primary-foreground">
                    {getUserInitials(user)}
                  </span>
                ) : (
                  <Icon name="User" size={16} className="text-primary-foreground" />
                )}
              </div>
            </Button>

            {/* User Menu Dropdown */}
            {showUserMenu && user && (
              <div className="absolute right-0 mt-2 w-48 bg-surface border border-border rounded-lg shadow-lg py-1 z-50">
                <div className="px-4 py-2 text-sm text-text border-b border-border">
                  <div className="font-medium">{getUserDisplayName(user)}</div>
                  <div className="text-xs text-text-muted">{user.email}</div>
                  {user.role && (
                    <div className="text-xs text-text-muted capitalize mt-1">
                      Role: {user.role}
                    </div>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2 text-sm text-text hover:bg-surface-secondary transition-colors duration-150"
                >
                  <Icon name="LogOut" size={14} className="inline mr-2" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile menu backdrop */}
      {showUserMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowUserMenu(false)}
        />
      )}

      {/* Mobile Search Bar */}
      <div className="md:hidden mt-3">
        <form onSubmit={handleSearchSubmit} className="relative">
          <div className={`relative flex items-center transition-all duration-150 ${
            isSearchFocused ? 'ring-2 ring-accent/20' : ''
          }`}>
            <Icon 
              name="Search" 
              size={16} 
              className="absolute left-3 text-text-muted pointer-events-none"
            />
            <input
              type="text"
              placeholder="Search databases, schemas, tables..."
              value={searchQuery}
              onChange={handleSearchChange}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setIsSearchFocused(false)}
              className="w-full pl-10 pr-10 py-2 text-sm bg-surface-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all duration-150"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-3 p-1 hover:bg-secondary-100 rounded transition-colors duration-150"
              >
                <Icon name="X" size={14} className="text-text-muted" />
              </button>
            )}
          </div>
        </form>
      </div>
    </header>
  );
};

export default Header;