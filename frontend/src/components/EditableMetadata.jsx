import React, { useState, useEffect } from 'react';
import Icon from './AppIcon';

const EditableMetadata = ({ 
  value, 
  field, 
  onSave, 
  onAIUpdate, 
  placeholder = "Click to edit...",
  type = "text", // text, textarea, select
  options = [], // for select type
  multiline = false,
  label = "",
  disabled = false,
  showAIHelper = true,
  renderMarkdown = false
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value || "");
  const [isLoading, setIsLoading] = useState(false);
  const [showAIFeedback, setShowAIFeedback] = useState(false);
  const [aiFeedback, setAiFeedback] = useState("");

  useEffect(() => {
    setEditValue(value || "");
  }, [value]);

  const handleSave = async () => {
    if (editValue !== value) {
      setIsLoading(true);
      try {
        await onSave(field, editValue);
        setIsEditing(false);
      } catch (error) {
        console.error('Error saving metadata:', error);
      } finally {
        setIsLoading(false);
      }
    } else {
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setEditValue(value || "");
    setIsEditing(false);
  };

  const handleAIUpdate = async () => {
    if (!aiFeedback.trim()) return;
    
    setIsLoading(true);
    try {
      await onAIUpdate(field, aiFeedback, value);
      setShowAIFeedback(false);
      setAiFeedback("");
    } catch (error) {
      console.error('Error with AI update:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !multiline) {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const renderEditableContent = () => {
    if (disabled) {
      return (
        <div className="text-text-secondary text-sm">
          {value || placeholder}
        </div>
      );
    }

    if (isEditing) {
      return (
        <div className="space-y-2">
          {type === 'textarea' || multiline ? (
            <textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="w-full p-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent resize-none"
              rows={multiline ? 3 : 1}
              disabled={isLoading}
              autoFocus
            />
          ) : type === 'select' ? (
            <select
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full p-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent"
              disabled={isLoading}
              autoFocus
            >
              <option value="">Select an option...</option>
              {options.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="w-full p-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent"
              disabled={isLoading}
              autoFocus
            />
          )}
          
          {/* Action buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="flex items-center space-x-1 px-3 py-1 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 text-sm"
              >
                {isLoading ? (
                  <>
                    <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Icon name="Check" size={14} />
                    <span>Save</span>
                  </>
                )}
              </button>
              <button
                onClick={handleCancel}
                disabled={isLoading}
                className="flex items-center space-x-1 px-3 py-1 bg-surface-secondary text-text-secondary rounded-md hover:bg-surface-secondary/80 disabled:opacity-50 text-sm"
              >
                <Icon name="X" size={14} />
                <span>Cancel</span>
              </button>
            </div>
            
            {showAIHelper && onAIUpdate && (
              <button
                onClick={() => setShowAIFeedback(!showAIFeedback)}
                disabled={isLoading}
                className="flex items-center space-x-1 px-3 py-1 bg-accent/10 text-accent rounded-md hover:bg-accent/20 disabled:opacity-50 text-sm"
              >
                <Icon name="Sparkles" size={14} />
                <span>AI Help</span>
              </button>
            )}
          </div>
          
          {/* AI Feedback Section */}
          {showAIFeedback && (
            <div className="mt-2 p-3 bg-accent/5 border border-accent/20 rounded-md">
              <div className="text-sm text-text-secondary mb-2">
                Describe what you'd like to change about this field:
              </div>
              <textarea
                value={aiFeedback}
                onChange={(e) => setAiFeedback(e.target.value)}
                placeholder="e.g., 'This description is incorrect, it should mention that this table contains employee data, not customer data.'"
                className="w-full p-2 text-sm border border-border rounded-md bg-surface text-text-primary focus:outline-none focus:ring-2 focus:ring-accent focus:border-accent resize-none"
                rows={2}
                disabled={isLoading}
              />
              <div className="flex items-center space-x-2 mt-2">
                <button
                  onClick={handleAIUpdate}
                  disabled={isLoading || !aiFeedback.trim()}
                  className="flex items-center space-x-1 px-3 py-1 bg-accent text-accent-foreground rounded-md hover:bg-accent/90 disabled:opacity-50 text-sm"
                >
                  {isLoading ? (
                    <>
                      <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <Icon name="Sparkles" size={14} />
                      <span>Update with AI</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowAIFeedback(false);
                    setAiFeedback("");
                  }}
                  disabled={isLoading}
                  className="text-sm text-text-muted hover:text-text-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      );
    }

    return (
      <div
        onClick={() => setIsEditing(true)}
        className="group cursor-pointer hover:bg-surface-secondary/50 p-1 rounded-md transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            {value ? (
              renderMarkdown ? (
                <div
                  className="text-text-primary text-sm prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{
                    __html: (value || "")
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.*?)\*/g, '<em>$1</em>')
                      .replace(/\n\n/g, '</p><p>')
                      .replace(/\n/g, '<br/>')
                      .replace(/^/, '<p>')
                      .replace(/$/, '</p>')
                  }}
                />
              ) : (
                <div className="text-text-primary text-sm whitespace-pre-wrap">
                  {value}
                </div>
              )
            ) : (
              <div className="text-text-muted text-sm italic">
                {placeholder}
              </div>
            )}
          </div>
          <div className="opacity-0 group-hover:opacity-100 transition-opacity ml-2">
            <Icon name="Edit2" size={12} className="text-text-muted" />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="w-full">
      {label && (
        <div className="text-xs text-text-muted mb-1 font-medium">
          {label}
        </div>
      )}
      {renderEditableContent()}
    </div>
  );
};

export default EditableMetadata; 