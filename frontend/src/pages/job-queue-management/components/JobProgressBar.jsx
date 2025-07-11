import React from 'react';

const JobProgressBar = ({ progress, status, size = 'md' }) => {
  const getProgressColor = (status) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'bg-accent';
      case 'completed':
        return 'bg-success';
      case 'failed':
        return 'bg-error';
      case 'cancelled':
        return 'bg-secondary-400';
      default:
        return 'bg-secondary-300';
    }
  };

  const getBackgroundColor = (status) => {
    switch (status.toLowerCase()) {
      case 'running':
        return 'bg-accent-100';
      case 'completed':
        return 'bg-success-100';
      case 'failed':
        return 'bg-error-100';
      case 'cancelled':
        return 'bg-secondary-100';
      default:
        return 'bg-secondary-100';
    }
  };

  const heightClass = size === 'sm' ? 'h-1' : size === 'lg' ? 'h-3' : 'h-2';
  const progressValue = Math.min(Math.max(progress || 0, 0), 100);
  const progressColor = getProgressColor(status);
  const backgroundColor = getBackgroundColor(status);

  return (
    <div className="w-full">
      <div className={`w-full ${backgroundColor} rounded-full overflow-hidden ${heightClass}`}>
        <div
          className={`${heightClass} ${progressColor} transition-all duration-300 ease-out ${
            status === 'running' ? 'animate-pulse' : ''
          }`}
          style={{ width: `${progressValue}%` }}
        />
      </div>
      {size !== 'sm' && (
        <div className="flex justify-between items-center mt-1">
          <span className="text-xs text-text-muted">
            {progressValue}%
          </span>
          {status === 'running' && (
            <span className="text-xs text-accent font-medium">
              In Progress
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default JobProgressBar;