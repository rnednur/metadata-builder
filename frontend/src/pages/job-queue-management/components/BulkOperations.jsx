import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const BulkOperations = ({ 
  selectedJobs, 
  onSelectAll, 
  onDeselectAll, 
  onBulkCancel, 
  onBulkRetry, 
  onBulkDelete,
  totalJobs,
  isAllSelected 
}) => {
  const selectedCount = selectedJobs.length;
  const hasSelection = selectedCount > 0;

  const handleSelectAll = () => {
    if (isAllSelected) {
      onDeselectAll();
    } else {
      onSelectAll();
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={isAllSelected}
              onChange={handleSelectAll}
              className="w-4 h-4 text-accent border-border rounded focus:ring-accent/20"
            />
            <span className="text-sm text-text-secondary">
              {selectedCount > 0 
                ? `${selectedCount} of ${totalJobs} selected`
                : `Select all ${totalJobs} jobs`
              }
            </span>
          </div>

          {hasSelection && (
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onBulkCancel}
                iconName="Square"
                iconSize={14}
              >
                Cancel
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onBulkRetry}
                iconName="RotateCcw"
                iconSize={14}
              >
                Retry
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={onBulkDelete}
                iconName="Trash2"
                iconSize={14}
              >
                Delete
              </Button>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-text-muted">
            Bulk Operations
          </span>
          <Icon name="Settings" size={16} className="text-text-muted" />
        </div>
      </div>
    </div>
  );
};

export default BulkOperations;