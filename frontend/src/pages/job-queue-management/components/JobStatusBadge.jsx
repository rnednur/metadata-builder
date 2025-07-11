import React from 'react';
import Icon from '../../../components/AppIcon';

const JobStatusBadge = ({ status, size = 'md' }) => {
  const getStatusConfig = (status) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return {
          icon: 'Clock',
          text: 'Pending',
          className: 'bg-warning-100 text-warning-700 border-warning-200'
        };
      case 'running':
        return {
          icon: 'Play',
          text: 'Running',
          className: 'bg-accent-100 text-accent-700 border-accent-200'
        };
      case 'completed':
        return {
          icon: 'CheckCircle',
          text: 'Completed',
          className: 'bg-success-100 text-success-700 border-success-200'
        };
      case 'failed':
        return {
          icon: 'XCircle',
          text: 'Failed',
          className: 'bg-error-100 text-error-700 border-error-200'
        };
      case 'cancelled':
        return {
          icon: 'Square',
          text: 'Cancelled',
          className: 'bg-secondary-100 text-secondary-700 border-secondary-200'
        };
      default:
        return {
          icon: 'HelpCircle',
          text: 'Unknown',
          className: 'bg-secondary-100 text-secondary-700 border-secondary-200'
        };
    }
  };

  const config = getStatusConfig(status);
  const sizeClasses = size === 'sm' ? 'px-2 py-1 text-xs' : 'px-3 py-1 text-sm';
  const iconSize = size === 'sm' ? 12 : 14;

  return (
    <span className={`inline-flex items-center space-x-1 ${sizeClasses} font-medium border rounded-full ${config.className}`}>
      <Icon name={config.icon} size={iconSize} />
      <span>{config.text}</span>
    </span>
  );
};

export default JobStatusBadge;