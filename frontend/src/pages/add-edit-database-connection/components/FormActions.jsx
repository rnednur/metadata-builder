import React, { useState } from 'react';
import Button from '../../../components/ui/Button';
import Icon from '../../../components/AppIcon';

const FormActions = ({ 
  onSave, 
  onCancel, 
  isLoading, 
  hasUnsavedChanges, 
  isValid,
  isEditMode 
}) => {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      setShowConfirmDialog(true);
    } else {
      onCancel();
    }
  };

  const handleConfirmCancel = () => {
    setShowConfirmDialog(false);
    onCancel();
  };

  const handleSave = () => {
    onSave();
  };

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0 sm:space-x-4 pt-6 border-t border-border">
        <div className="flex items-center space-x-2 text-sm text-text-muted">
          <Icon name="Info" size={16} />
          <span>
            {isEditMode ? 'Modifying existing connection' : 'Creating new connection'}
          </span>
        </div>
        
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
            iconName="X"
            iconPosition="left"
            className="sm:order-1"
          >
            Cancel
          </Button>
          
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={!isValid || isLoading}
            loading={isLoading}
            iconName="Save"
            iconPosition="left"
            className="sm:order-2"
          >
            {isLoading ? 'Saving...' : isEditMode ? 'Update Connection' : 'Create Connection'}
          </Button>
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-200 flex items-center justify-center p-4">
          <div className="bg-surface rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start space-x-3">
              <div className="p-2 bg-warning-100 rounded-lg">
                <Icon name="AlertTriangle" size={20} className="text-warning-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-text-primary">
                  Discard Changes?
                </h3>
                <p className="text-sm text-text-secondary mt-1">
                  You have unsaved changes. Are you sure you want to leave without saving?
                </p>
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 mt-6">
              <Button
                variant="outline"
                onClick={() => setShowConfirmDialog(false)}
                className="flex-1"
              >
                Keep Editing
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmCancel}
                className="flex-1"
                iconName="Trash2"
                iconPosition="left"
              >
                Discard Changes
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default FormActions;