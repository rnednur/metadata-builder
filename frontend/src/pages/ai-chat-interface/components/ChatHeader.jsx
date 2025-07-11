import React from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const ChatHeader = ({ onToggleContext, onExportChat, onClearChat, messageCount = 0 }) => {
  const handleExport = () => {
    // Mock export functionality
    const chatData = {
      timestamp: new Date().toISOString(),
      messageCount,
      exportedAt: new Date().toLocaleString()
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    onExportChat();
  };

  return (
    <div className="flex items-center justify-between p-4 border-b border-border bg-surface">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 bg-gradient-to-br from-accent to-primary rounded-lg flex items-center justify-center">
          <Icon name="Bot" size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-text-primary">AI Assistant</h1>
          <p className="text-sm text-text-secondary">
            {messageCount > 0 ? `${messageCount} messages` : 'Ready to help with your database queries'}
          </p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        {/* Export Chat */}
        {messageCount > 0 && (
          <Button
            variant="ghost"
            onClick={handleExport}
            className="p-2"
            aria-label="Export chat"
          >
            <Icon name="Download" size={18} className="text-text-secondary" />
          </Button>
        )}

        {/* Clear Chat */}
        {messageCount > 0 && (
          <Button
            variant="ghost"
            onClick={onClearChat}
            className="p-2"
            aria-label="Clear chat"
          >
            <Icon name="Trash2" size={18} className="text-text-secondary" />
          </Button>
        )}

        {/* Toggle Context Sidebar */}
        <Button
          variant="ghost"
          onClick={onToggleContext}
          className="p-2 lg:hidden"
          aria-label="Toggle context sidebar"
        >
          <Icon name="Sidebar" size={18} className="text-text-secondary" />
        </Button>
      </div>
    </div>
  );
};

export default ChatHeader;