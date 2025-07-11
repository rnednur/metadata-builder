import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';

const JobFilters = ({ 
  filters, 
  onFilterChange, 
  onClearFilters, 
  onRefresh 
}) => {
  const statusOptions = [
    { value: '', label: 'All Status' },
    { value: 'pending', label: 'Pending' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  const jobTypeOptions = [
    { value: '', label: 'All Types' },
    { value: 'metadata_generation', label: 'Metadata Generation' },
    { value: 'lookml_creation', label: 'LookML Creation' },
    { value: 'schema_analysis', label: 'Schema Analysis' },
    { value: 'data_profiling', label: 'Data Profiling' },
    { value: 'system_maintenance', label: 'System Maintenance' }
  ];

  const priorityOptions = [
    { value: '', label: 'All Priorities' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' }
  ];

  const handleInputChange = (field, value) => {
    onFilterChange({ ...filters, [field]: value });
  };

  const hasActiveFilters = Object.values(filters).some(value => value !== '');

  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary flex items-center">
          <Icon name="Filter" size={20} className="mr-2 text-accent" />
          Filters
        </h3>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            onClick={onRefresh}
            iconName="RefreshCw"
            iconSize={16}
          >
            Refresh
          </Button>
          {hasActiveFilters && (
            <Button
              variant="outline"
              onClick={onClearFilters}
              iconName="X"
              iconSize={16}
            >
              Clear
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        {/* Status Filter */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Status
          </label>
          <select
            value={filters.status}
            onChange={(e) => handleInputChange('status', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-surface focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Job Type Filter */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Job Type
          </label>
          <select
            value={filters.jobType}
            onChange={(e) => handleInputChange('jobType', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-surface focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
          >
            {jobTypeOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Priority
          </label>
          <select
            value={filters.priority}
            onChange={(e) => handleInputChange('priority', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-border rounded-lg bg-surface focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent"
          >
            {priorityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date From */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            From Date
          </label>
          <Input
            type="date"
            value={filters.dateFrom}
            onChange={(e) => handleInputChange('dateFrom', e.target.value)}
            className="text-sm"
          />
        </div>

        {/* Date To */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            To Date
          </label>
          <Input
            type="date"
            value={filters.dateTo}
            onChange={(e) => handleInputChange('dateTo', e.target.value)}
            className="text-sm"
          />
        </div>

        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            Search
          </label>
          <Input
            type="search"
            placeholder="Job ID, target..."
            value={filters.search}
            onChange={(e) => handleInputChange('search', e.target.value)}
            className="text-sm"
          />
        </div>
      </div>
    </div>
  );
};

export default JobFilters;