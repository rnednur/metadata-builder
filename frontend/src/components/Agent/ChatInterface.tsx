import React, { useState, useEffect, useRef } from 'react';
import { Card, Input, Button, Typography, Spin, Avatar, Tag, Tooltip } from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons';
import { api } from '../../services/api';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  actions_taken?: any;
  suggestions?: string[];
  error?: string;
}

interface ChatInterfaceProps {
  onContextChange?: (context: any) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onContextChange }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize with welcome message
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: `Hello! I'm your Metadata Assistant. I can help you with:

• 📊 **Generate metadata** for your database tables
• 🔍 **Search and explore** your data assets
• 📈 **Analyze data quality** and identify issues
• 🏗️ **Track schema changes** and structure updates
• 💼 **Explain business context** and meanings
• 📤 **Export and report** metadata in various formats

Just tell me what you'd like to do in natural language! For example:
- "Generate metadata for the users table"
- "Show me all tables with customer data"
- "Check data quality issues in my database"`,
        timestamp: new Date().toISOString(),
        suggestions: [
          "Show me available databases",
          "Generate metadata for a specific table",
          "Check data quality across all tables",
          "Find tables containing customer information"
        ]
      }
    ]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await api.post('/agent/chat', {
        user_id: 'current_user', // In real app, get from auth context
        message: inputValue,
        session_id: sessionId
      });

      const assistantMessage: Message = {
        id: `assistant_${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        intent: response.data.intent,
        actions_taken: response.data.actions_taken,
        suggestions: response.data.suggestions,
        error: response.data.error
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update context if provided
      if (response.data.context && onContextChange) {
        onContextChange(response.data.context);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your request. Please try again or rephrase your question.",
        timestamp: new Date().toISOString(),
        error: 'Network or server error',
        suggestions: [
          "Try rephrasing your request",
          "Check your network connection",
          "Contact support if the issue persists"
        ]
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
  };

  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user';
    
    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div className={`flex max-w-3xl ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            className={`${isUser ? 'ml-2' : 'mr-2'} flex-shrink-0`}
            style={{
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
            }}
          />
          
          <div className={`${isUser ? 'mr-2' : 'ml-2'} flex-1`}>
            <Card
              size="small"
              className={`${
                isUser
                  ? 'bg-blue-50 border-blue-200'
                  : message.error
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="whitespace-pre-wrap">
                <Paragraph className="mb-0">
                  {message.content}
                </Paragraph>
              </div>
              
              {/* Show intent and actions for assistant messages */}
              {!isUser && (
                <div className="mt-2 space-y-2">
                  {message.intent && (
                    <div>
                      <Tag color="blue" size="small">
                        Intent: {message.intent}
                      </Tag>
                    </div>
                  )}
                  
                  {message.actions_taken && message.actions_taken.actions_performed?.length > 0 && (
                    <div>
                      <Text type="secondary" className="text-xs">
                        Actions performed:
                      </Text>
                      <div className="mt-1">
                        {message.actions_taken.actions_performed.map((action: string, index: number) => (
                          <Tag key={index} color="green" size="small">
                            {action}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {message.error && (
                    <div>
                      <Tag color="red" size="small">
                        Error occurred
                      </Tag>
                    </div>
                  )}
                </div>
              )}
              
              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <Text type="secondary" className="text-xs block mb-2">
                    Suggestions:
                  </Text>
                  <div className="space-y-1">
                    {message.suggestions.map((suggestion, index) => (
                      <Button
                        key={index}
                        type="link"
                        size="small"
                        className="text-left p-0 h-auto text-blue-600 hover:text-blue-800"
                        onClick={() => handleSuggestionClick(suggestion)}
                      >
                        💡 {suggestion}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-right mt-2">
                <Text type="secondary" className="text-xs">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </Text>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  };

  const clearChat = () => {
    setMessages([messages[0]]); // Keep welcome message
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center space-x-2">
          <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#52c41a' }} />
          <div>
            <Text strong>Metadata Assistant</Text>
            <br />
            <Text type="secondary" className="text-xs">
              AI-powered metadata management
            </Text>
          </div>
        </div>
        
        <Tooltip title="Clear conversation">
          <Button
            icon={<ReloadOutlined />}
            onClick={clearChat}
            type="text"
            size="small"
          />
        </Tooltip>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-white">
        {messages.map(renderMessage)}
        
        {loading && (
          <div className="flex justify-start mb-4">
            <div className="flex max-w-3xl">
              <Avatar
                icon={<RobotOutlined />}
                className="mr-2 flex-shrink-0"
                style={{ backgroundColor: '#52c41a' }}
              />
              <Card size="small" className="bg-gray-50 border-gray-200">
                <div className="flex items-center space-x-2">
                  <Spin size="small" />
                  <Text type="secondary">Thinking...</Text>
                </div>
              </Card>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200 bg-white">
        <div className="flex space-x-2">
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your metadata... (Press Enter to send, Shift+Enter for new line)"
            autoSize={{ minRows: 1, maxRows: 4 }}
            className="flex-1"
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={loading}
            disabled={!inputValue.trim()}
            className="flex-shrink-0"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}; 