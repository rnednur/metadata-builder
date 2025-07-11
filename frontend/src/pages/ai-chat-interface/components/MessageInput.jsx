import React, { useState, useRef, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const MessageInput = ({ onSendMessage, onAttachSchema, isLoading = false }) => {
  const [message, setMessage] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showMentionDropdown, setShowMentionDropdown] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionPosition, setMentionPosition] = useState({ top: 0, left: 0 });
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef(null);
  const mentionDropdownRef = useRef(null);

  const suggestedPrompts = [
    "Explain the relationship between users and orders tables",
    "What are the key columns in the products table?",
    "Generate a summary of the customer_analytics schema",
    "Show me tables with foreign key relationships",
    "What data types are used in the inventory table?",
    "Identify potential data quality issues in sales_data",
    "Fix the metadata for @table_name",
    "Update categorical values for @column_name",
    "Generate better descriptions for @schema_name"
  ];

  // Mock database objects for @ mentions
  const availableObjects = {
    tables: [
      { name: 'users', type: 'table', schema: 'public', description: 'User account information' },
      { name: 'orders', type: 'table', schema: 'public', description: 'Order transactions' },
      { name: 'products', type: 'table', schema: 'public', description: 'Product catalog' },
      { name: 'customer_analytics', type: 'table', schema: 'analytics', description: 'Customer metrics' },
      { name: 'inventory', type: 'table', schema: 'warehouse', description: 'Inventory tracking' },
      { name: 'sales_data', type: 'table', schema: 'reporting', description: 'Sales reporting data' }
    ],
    columns: [
      { name: 'user_id', type: 'column', table: 'users', description: 'Unique user identifier' },
      { name: 'email', type: 'column', table: 'users', description: 'User email address' },
      { name: 'status', type: 'column', table: 'orders', description: 'Order status' },
      { name: 'category', type: 'column', table: 'products', description: 'Product category' },
      { name: 'price', type: 'column', table: 'products', description: 'Product price' }
    ],
    schemas: [
      { name: 'public', type: 'schema', description: 'Main application schema' },
      { name: 'analytics', type: 'schema', description: 'Analytics and reporting' },
      { name: 'warehouse', type: 'schema', description: 'Data warehouse tables' },
      { name: 'reporting', type: 'schema', description: 'Business reporting' }
    ]
  };

  // Get filtered objects based on mention query
  const getFilteredObjects = () => {
    if (!mentionQuery) {
      return [...availableObjects.tables, ...availableObjects.columns, ...availableObjects.schemas];
    }
    
    const query = mentionQuery.toLowerCase();
    const filtered = [];
    
    // Search tables
    availableObjects.tables.forEach(obj => {
      if (obj.name.toLowerCase().includes(query) || obj.description.toLowerCase().includes(query)) {
        filtered.push(obj);
      }
    });
    
    // Search columns
    availableObjects.columns.forEach(obj => {
      if (obj.name.toLowerCase().includes(query) || obj.description.toLowerCase().includes(query)) {
        filtered.push(obj);
      }
    });
    
    // Search schemas
    availableObjects.schemas.forEach(obj => {
      if (obj.name.toLowerCase().includes(query) || obj.description.toLowerCase().includes(query)) {
        filtered.push(obj);
      }
    });
    
    return filtered.slice(0, 10); // Limit to 10 results
  };

  // Calculate cursor position in textarea
  const getCursorPosition = () => {
    const textarea = textareaRef.current;
    if (!textarea) return { top: 0, left: 0 };
    
    const style = window.getComputedStyle(textarea);
    const fontSize = parseInt(style.fontSize);
    const lineHeight = parseInt(style.lineHeight) || fontSize * 1.2;
    
    const textBeforeCursor = textarea.value.substring(0, textarea.selectionStart);
    const lines = textBeforeCursor.split('\n');
    const currentLine = lines.length - 1;
    const currentColumn = lines[currentLine].length;
    
    return {
      top: currentLine * lineHeight + parseInt(style.paddingTop) + 40,
      left: currentColumn * 8 + parseInt(style.paddingLeft) // Rough character width
    };
  };

  // Handle @ mention detection
  const handleMentionDetection = (text, selectionStart) => {
    const textBeforeCursor = text.substring(0, selectionStart);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    
    if (lastAtIndex === -1) {
      setShowMentionDropdown(false);
      return;
    }
    
    const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
    
    // Check if there's a space after @ (which would end the mention)
    if (textAfterAt.includes(' ')) {
      setShowMentionDropdown(false);
      return;
    }
    
    setMentionQuery(textAfterAt);
    setShowMentionDropdown(true);
    setMentionPosition(getCursorPosition());
  };

  // Handle mention selection
  const handleMentionSelect = (selectedObject) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const selectionStart = textarea.selectionStart;
    const textBeforeCursor = message.substring(0, selectionStart);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    
    if (lastAtIndex === -1) return;
    
    const textBeforeAt = message.substring(0, lastAtIndex);
    const textAfterCursor = message.substring(selectionStart);
    
    const newMessage = textBeforeAt + `@${selectedObject.name}` + textAfterCursor;
    setMessage(newMessage);
    setShowMentionDropdown(false);
    setMentionQuery('');
    
    // Focus back to textarea
    setTimeout(() => {
      textarea.focus();
      const newCursorPosition = lastAtIndex + selectedObject.name.length + 1;
      textarea.setSelectionRange(newCursorPosition, newCursorPosition);
    }, 0);
  };

  // Close mention dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (mentionDropdownRef.current && !mentionDropdownRef.current.contains(event.target)) {
        setShowMentionDropdown(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
      setShowSuggestions(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    const newMessage = e.target.value;
    const selectionStart = e.target.selectionStart;
    
    setMessage(newMessage);
    setCursorPosition(selectionStart);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    
    // Check for @ mention
    handleMentionDetection(newMessage, selectionStart);
  };

  const handleSuggestionClick = (suggestion) => {
    setMessage(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };

  const handleAttachClick = () => {
    onAttachSchema();
  };

  return (
    <div className="border-t border-border bg-surface relative">
      {/* @ Mention Dropdown */}
      {showMentionDropdown && (
        <div 
          ref={mentionDropdownRef}
          className="absolute bottom-full left-4 right-4 bg-surface border border-border rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto"
          style={{
            marginBottom: '8px'
          }}
        >
          <div className="p-2">
            <div className="text-xs text-text-muted mb-2 px-2">
              Select database object to reference:
            </div>
            {getFilteredObjects().map((obj, index) => (
              <button
                key={`${obj.type}-${obj.name}`}
                onClick={() => handleMentionSelect(obj)}
                className="w-full text-left p-2 hover:bg-surface-secondary rounded-md transition-colors duration-150 flex items-center space-x-2"
              >
                <div className="flex-shrink-0">
                  <Icon 
                    name={obj.type === 'table' ? 'Table' : obj.type === 'column' ? 'Columns' : 'Database'} 
                    size={16} 
                    className="text-accent" 
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-text-primary">
                      {obj.name}
                    </span>
                    <span className="text-xs text-text-muted bg-secondary-100 px-2 py-1 rounded">
                      {obj.type}
                    </span>
                  </div>
                  <div className="text-xs text-text-secondary truncate">
                    {obj.description}
                    {obj.type === 'column' && obj.table && (
                      <span className="ml-2 text-text-muted">in {obj.table}</span>
                    )}
                    {obj.type === 'table' && obj.schema && (
                      <span className="ml-2 text-text-muted">({obj.schema})</span>
                    )}
                  </div>
                </div>
              </button>
            ))}
            {getFilteredObjects().length === 0 && (
              <div className="text-center py-4 text-text-muted text-sm">
                No objects found matching "{mentionQuery}"
              </div>
            )}
          </div>
        </div>
      )}

      {/* Suggested Prompts */}
      {showSuggestions && (
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-text-primary">Suggested Prompts</h4>
            <Button
              variant="ghost"
              onClick={() => setShowSuggestions(false)}
              className="p-1"
            >
              <Icon name="X" size={16} />
            </Button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {suggestedPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(prompt)}
                className="text-left p-3 text-sm bg-surface-secondary hover:bg-secondary-100 rounded-lg transition-colors duration-150 border border-border"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Message Input */}
      <form onSubmit={handleSubmit} className="p-4">
        <div className="flex items-end space-x-3">
          {/* Attach Schema Button */}
          <Button
            type="button"
            variant="ghost"
            onClick={handleAttachClick}
            className="p-2 flex-shrink-0"
            disabled={isLoading}
          >
            <Icon name="Paperclip" size={20} className="text-text-secondary" />
          </Button>

          {/* Suggestions Toggle */}
          <Button
            type="button"
            variant="ghost"
            onClick={() => setShowSuggestions(!showSuggestions)}
            className="p-2 flex-shrink-0"
            disabled={isLoading}
          >
            <Icon name="Lightbulb" size={20} className="text-text-secondary" />
          </Button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your database schema, relationships, or data insights..."
              className="w-full px-4 py-3 pr-12 text-sm bg-surface-secondary border border-border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all duration-150"
              style={{ minHeight: '48px', maxHeight: '120px' }}
              disabled={isLoading}
            />
            
            {/* Character Count */}
            <div className="absolute bottom-2 right-2 text-xs text-text-muted">
              {message.length}/2000
            </div>
          </div>

          {/* Send Button */}
          <Button
            type="submit"
            variant="primary"
            disabled={!message.trim() || isLoading}
            className="p-3 flex-shrink-0"
            loading={isLoading}
          >
            <Icon name="Send" size={20} />
          </Button>
        </div>

        {/* Input Hints */}
        <div className="flex items-center justify-between mt-2 text-xs text-text-muted">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>Max 2000 characters</span>
        </div>
      </form>
    </div>
  );
};

export default MessageInput;