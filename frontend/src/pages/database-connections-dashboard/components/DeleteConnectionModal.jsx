import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const DeleteConnectionModal = ({ isOpen, connection, onConfirm, onCancel, isDeleting }) => {
  if (!isOpen || !connection) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-200 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-error/10 rounded-lg flex items-center justify-center">
              <Icon name="AlertTriangle" size={20} className="text-error" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary">Delete Connection</h3>
              <p className="text-sm text-text-secondary">This action cannot be undone</p>
            </div>
          </div>

          {/* Content */}
          <div className="mb-6">
            <p className="text-text-secondary mb-4">
              Are you sure you want to delete the connection <strong className="text-text-primary">"{connection.name}"</strong>?
            </p>
            <div className="bg-surface-secondary rounded-lg p-3">
              <div className="flex items-center space-x-2 text-sm text-text-secondary">
                <Icon name="Database" size={14} />
                <span>{connection.type} • {connection.host}:{connection.port}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3">
            <Button
              variant="ghost"
              onClick={onCancel}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={() => onConfirm(connection.id)}
              disabled={isDeleting}
              loading={isDeleting}
            >
              {isDeleting ? 'Deleting...' : 'Delete Connection'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteConnectionModal;