import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';

const ConnectionToolbar = ({ 
  searchQuery, 
  onSearchChange, 
  viewMode, 
  onViewModeChange, 
  onAddConnection,
  connectionCount 
}) => {
  const navigate = useNavigate();
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const handleAddConnection = () => {
    navigate('/add-edit-database-connection');
  };

  const clearSearch = () => {
    onSearchChange('');
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        {/* Left Section - Title and Count */}
        <div className="flex items-center space-x-4">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Database Connections</h1>
            <p className="text-sm text-text-secondary mt-1">
              {connectionCount} {connectionCount === 1 ? 'connection' : 'connections'} configured
            </p>
          </div>
        </div>

        {/* Right Section - Actions */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center space-y-3 sm:space-y-0 sm:space-x-3">
          {/* Search Bar */}
          <div className="relative flex-1 sm:flex-initial sm:w-64">
            <div className={`relative flex items-center transition-all duration-150 ${
              isSearchFocused ? 'ring-2 ring-accent/20' : ''
            }`}>
              <Icon 
                name="Search" 
                size={16} 
                className="absolute left-3 text-text-muted pointer-events-none"
              />
              <Input
                type="search"
                placeholder="Search connections..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onBlur={() => setIsSearchFocused(false)}
                className="pl-10 pr-10"
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
          </div>

          {/* View Toggle */}
          <div className="flex items-center bg-surface-secondary rounded-lg p-1">
            <button
              onClick={() => onViewModeChange('grid')}
              className={`p-2 rounded transition-all duration-150 ${
                viewMode === 'grid' ?'bg-surface shadow-sm text-text-primary' :'text-text-secondary hover:text-text-primary'
              }`}
              aria-label="Grid view"
            >
              <Icon name="Grid3X3" size={16} />
            </button>
            <button
              onClick={() => onViewModeChange('list')}
              className={`p-2 rounded transition-all duration-150 ${
                viewMode === 'list' ?'bg-surface shadow-sm text-text-primary' :'text-text-secondary hover:text-text-primary'
              }`}
              aria-label="List view"
            >
              <Icon name="List" size={16} />
            </button>
          </div>

          {/* Add Connection Button */}
          <Button
            variant="primary"
            onClick={handleAddConnection}
            iconName="Plus"
            iconPosition="left"
            className="whitespace-nowrap"
          >
            Add Connection
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConnectionToolbar;