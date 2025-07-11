import React from 'react';
import Icon from '../../../components/AppIcon';

const ChatMessage = ({ message, isUser, timestamp, isTyping = false, intent, entities, actions, suggestions }) => {
  const formatTimestamp = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }).format(new Date(date));
  };

  const renderMessageContent = (content) => {
    // Check if content contains code blocks
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: content.slice(lastIndex, match.index)
        });
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'sql',
        content: match[2].trim()
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < content.length) {
      parts.push({
        type: 'text',
        content: content.slice(lastIndex)
      });
    }

    // If no code blocks found, return as single text part
    if (parts.length === 0) {
      parts.push({ type: 'text', content });
    }

    return parts.map((part, index) => {
      if (part.type === 'code') {
        return (
          <div key={index} className="my-3 bg-secondary-900 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-secondary-800 border-b border-secondary-700">
              <span className="text-xs font-medium text-secondary-300 uppercase">
                {part.language}
              </span>
              <button
                onClick={() => navigator.clipboard.writeText(part.content)}
                className="text-secondary-400 hover:text-secondary-200 transition-colors duration-150"
              >
                <Icon name="Copy" size={14} />
              </button>
            </div>
            <pre className="p-4 text-sm text-secondary-100 overflow-x-auto">
              <code>{part.content}</code>
            </pre>
          </div>
        );
      }
      return (
        <div key={index} className="whitespace-pre-wrap">
          {part.content}
        </div>
      );
    });
  };

  if (isTyping) {
    return (
      <div className="flex items-start space-x-3 mb-6">
        <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center flex-shrink-0">
          <Icon name="Bot" size={16} className="text-accent-foreground" />
        </div>
        <div className="flex-1">
          <div className="bg-surface-secondary rounded-lg px-4 py-3 max-w-3xl">
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex items-start space-x-3 mb-6 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser 
          ? 'bg-primary text-primary-foreground' 
          : 'bg-accent text-accent-foreground'
      }`}>
        <Icon name={isUser ? 'User' : 'Bot'} size={16} />
      </div>
      
      <div className="flex-1">
        <div className={`rounded-lg px-4 py-3 max-w-3xl ${
          isUser 
            ? 'bg-primary text-primary-foreground ml-auto' 
            : 'bg-surface-secondary text-text-primary'
        }`}>
          <div className="text-sm leading-relaxed">
            {renderMessageContent(message.content)}
          </div>
          
          {/* Metadata correction actions */}
          {!isUser && intent === 'metadata_correction' && (
            <div className="mt-3 pt-3 border-t border-border space-y-2">
              {entities && entities.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-text-muted">Referenced objects:</span>
                  {entities.map((entity, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-accent/10 text-accent"
                    >
                      <Icon name="At" size={12} className="mr-1" />
                      {entity}
                    </span>
                  ))}
                </div>
              )}
              
              {actions && actions.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-text-muted">Available actions:</span>
                  {actions.map((action, index) => (
                    <button
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded text-xs bg-secondary-100 hover:bg-secondary-200 text-text-primary transition-colors"
                    >
                      <Icon name="Play" size={12} className="mr-1" />
                      {action.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              )}
              
              {suggestions && suggestions.length > 0 && (
                <div className="space-y-1">
                  <span className="text-xs text-text-muted">Suggestions:</span>
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={index}
                      className="text-xs text-text-secondary bg-warning/10 px-2 py-1 rounded"
                    >
                      {suggestion}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className={`text-xs text-text-muted mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
          {formatTimestamp(timestamp)}
          {message.status && isUser && (
            <span className="ml-2">
              <Icon 
                name={message.status === 'sent' ? 'Check' : message.status === 'delivered' ? 'CheckCheck' : 'Clock'} 
                size={12} 
                className="inline"
              />
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;