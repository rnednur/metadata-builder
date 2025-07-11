import React from 'react';
import Icon from '../../../components/AppIcon';

const QueueStatistics = ({ statistics }) => {
  const statCards = [
    {
      id: 'total',
      label: 'Total Jobs',
      value: statistics.totalJobs,
      icon: 'BarChart3',
      color: 'text-primary',
      bgColor: 'bg-primary-50'
    },
    {
      id: 'running',
      label: 'Running',
      value: statistics.runningJobs,
      icon: 'Play',
      color: 'text-success',
      bgColor: 'bg-success-50'
    },
    {
      id: 'pending',
      label: 'Pending',
      value: statistics.pendingJobs,
      icon: 'Clock',
      color: 'text-warning',
      bgColor: 'bg-warning-50'
    },
    {
      id: 'completed',
      label: 'Completed',
      value: statistics.completedJobs,
      icon: 'CheckCircle',
      color: 'text-success',
      bgColor: 'bg-success-50'
    },
    {
      id: 'failed',
      label: 'Failed',
      value: statistics.failedJobs,
      icon: 'XCircle',
      color: 'text-error',
      bgColor: 'bg-error-50'
    },
    {
      id: 'avgTime',
      label: 'Avg. Duration',
      value: statistics.averageDuration,
      icon: 'Timer',
      color: 'text-accent',
      bgColor: 'bg-accent-50'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      {statCards.map((stat) => (
        <div
          key={stat.id}
          className="bg-surface border border-border rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`p-2 rounded-lg ${stat.bgColor}`}>
              <Icon 
                name={stat.icon} 
                size={20} 
                className={stat.color}
              />
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-2xl font-semibold text-text-primary">
              {stat.value}
            </p>
            <p className="text-sm text-text-secondary">
              {stat.label}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default QueueStatistics;