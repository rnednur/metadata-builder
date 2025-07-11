import React, { useState, useRef, useEffect } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import { metadataAPI, agentAPI, apiUtils } from '../../../services/api';

const MetadataPanel = ({ selectedTable, onToggleCollapse, isCollapsed, onMetadataGenerated }) => {
  const [activeTab, setActiveTab] = useState('metadata');
  const [isGenerating, setIsGenerating] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Metadata generation configuration
  const [configuration, setConfiguration] = useState({
    sampleSize: 100,
    numSamples: 5,
    maxPartitions: 10,
    customPrompt: '',
    includeRelationships: false,
    includeAggregationRules: false,
    includeQueryRules: false,
    includeDataQuality: false,
    includeQueryExamples: false,
    includeAdditionalInsights: false,
    includeBusinessRules: false,
    includeCategoricalDefinitions: true,
  });

  // Initialize chat when table changes
  useEffect(() => {
    if (selectedTable) {
      setMessages([{
        id: 1,
        content: `I'm ready to help you analyze the ${selectedTable.name} table. What would you like to know about it?`,
        isUser: false,
        timestamp: new Date(),
        status: 'delivered'
      }]);
    } else {
      setMessages([]);
    }
  }, [selectedTable]);

  // Clear metadata when table changes
  useEffect(() => {
    setMetadata(null);
    setError(null);
    setIsGenerating(false);
  }, [selectedTable]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleGenerateMetadata = async () => {
    if (!selectedTable) return;
    
    try {
      setIsGenerating(true);
      setError(null);
      
      // Build metadata request with configuration
      const metadataRequest = apiUtils.buildMetadataRequest({
        dbName: selectedTable.database,
        tableName: selectedTable.name,
        schemaName: selectedTable.schema,
        sampleSize: configuration.sampleSize,
        numSamples: configuration.numSamples,
        maxPartitions: configuration.maxPartitions,
        customPrompt: configuration.customPrompt || null,
        includeRelationships: configuration.includeRelationships,
        includeAggregationRules: configuration.includeAggregationRules,
        includeQueryRules: configuration.includeQueryRules,
        includeDataQuality: configuration.includeDataQuality,
        includeQueryExamples: configuration.includeQueryExamples,
        includeAdditionalInsights: configuration.includeAdditionalInsights,
        includeBusinessRules: configuration.includeBusinessRules,
        includeCategoricalDefinitions: configuration.includeCategoricalDefinitions,
      });
      
      const response = await metadataAPI.generateAndSaveMetadata(metadataRequest);
      
      // Parse the response
      let generatedMetadata = null;
      
      // Check if there's an error in the response
      if (response.data?.error) {
        setError(`Backend error: ${response.data.error}`);
        return;
      }
      
      if (typeof response.data?.metadata === 'string') {
        try {
          generatedMetadata = JSON.parse(response.data.metadata);
        } catch {
          generatedMetadata = { description: response.data.metadata };
        }
      } else {
        generatedMetadata = response.data?.metadata || response.data;
      }
      
      // Check if the generated metadata contains an error
      if (generatedMetadata?.error) {
        setError(`Metadata generation failed: ${generatedMetadata.error}`);
        return;
      }
      
      setMetadata(generatedMetadata);
      
      // Notify parent component to integrate metadata with table details
      if (onMetadataGenerated && generatedMetadata) {
        onMetadataGenerated(generatedMetadata);
      }
    } catch (err) {
      console.error('Error generating metadata:', err);
      setError(`Failed to generate metadata: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCreateLookML = async () => {
    if (!selectedTable) return;
    
    try {
      const response = await metadataAPI.generateLookMLSync({
        database_name: selectedTable.database,
        schema_name: selectedTable.schema,
        table_names: [selectedTable.name]
      });
      
      // Download the LookML file
      const blob = new Blob([response.lookml_content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${selectedTable.name}.view.lkml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error creating LookML:', err);
      setError(`Failed to create LookML: ${err.message}`);
    }
  };

  const handleSendMessage = async (content) => {
    if (!content.trim() || !selectedTable) return;

    const userMessage = {
      id: Date.now(),
      content,
      isUser: true,
      timestamp: new Date(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setChatLoading(true);
    setIsTyping(true);

    try {
      // Update message status to sent
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'sent' }
            : msg
        )
      );

      // Send message to AI agent with table context
      const contextualPrompt = `${content}\n\n[Context: Currently analyzing table ${selectedTable.database}.${selectedTable.schema}.${selectedTable.name}]`;
      const userId = 'user_schema_explorer';
      const chatRequest = apiUtils.buildChatRequest(userId, contextualPrompt);
      
      const response = await agentAPI.chat(chatRequest);
      const aiResponseData = response.data;
      
      setIsTyping(false);
      
      const responseMessage = {
        id: Date.now() + 1,
        content: aiResponseData.response || aiResponseData.message || 'I received your message.',
        isUser: false,
        timestamp: new Date(),
        status: 'delivered',
        intent: aiResponseData.intent,
        entities: aiResponseData.entities,
        actions: aiResponseData.actions_taken,
        suggestions: aiResponseData.suggestions
      };

      setMessages(prev => [...prev, responseMessage]);

      // Update user message to delivered
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'delivered' }
            : msg
        )
      );

    } catch (error) {
      setIsTyping(false);
      
      console.error('Failed to send message:', error);
      
      // Show error message
      const errorMessage = {
        id: Date.now() + 1,
        content: `Sorry, I encountered an error: ${apiUtils.handleApiError(error)}. Please try again.`,
        isUser: false,
        timestamp: new Date(),
        status: 'delivered',
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);

      // Update user message to failed
      setMessages(prev => 
        prev.map(msg => 
          msg.id === userMessage.id 
            ? { ...msg, status: 'failed' }
            : msg
        )
      );
    } finally {
      setChatLoading(false);
    }
  };

  const handleConfigChange = (field, value) => {
    setConfiguration(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getQualityColor = (quality) => {
    switch (quality?.toLowerCase()) {
      case 'high':
        return 'text-success';
      case 'medium':
        return 'text-warning';
      case 'low':
        return 'text-error';
      default:
        return 'text-text-muted';
    }
  };

  const getRelationshipIcon = (type) => {
    switch (type) {
      case 'One-to-Many':
        return 'ArrowRight';
      case 'Many-to-One':
        return 'ArrowLeft';
      case 'Many-to-Many':
        return 'ArrowLeftRight';
      default:
        return 'Minus';
    }
  };

  const tabs = [
    { id: 'metadata', label: 'Metadata', icon: 'Sparkles' },
    { id: 'chat', label: 'AI Chat', icon: 'MessageSquare' },
    { id: 'lookml', label: 'LookML', icon: 'Code' }
  ];

  if (!selectedTable) {
    return (
      <div className="h-full flex items-center justify-center bg-surface border-l border-border">
        <div className="text-center p-6">
          <Icon name="Sparkles" size={48} className="text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-medium text-text-primary mb-2">Table Analysis</h3>
          <p className="text-text-secondary text-sm">
            Select a table to access metadata generation, AI chat, and LookML tools
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-surface border-l border-border">
      {/* Header with Tabs */}
      <div className="border-b border-border">
        <div className="p-3 pb-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-text-primary">
              Analysis: {selectedTable.name}
            </h3>
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                className="p-1.5 text-text-muted hover:text-text-primary hover:bg-surface-secondary rounded-lg transition-colors"
                title="Collapse Analysis Panel"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-surface-secondary/50 mx-3 mb-3 rounded-lg p-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-1.5 px-2 py-1.5 rounded-md text-sm font-medium transition-colors duration-150 ${
                activeTab === tab.id 
                  ? 'bg-surface text-text-primary shadow-sm' 
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface/50'
              }`}
            >
              <Icon name={tab.icon} size={14} />
              <span className="text-xs">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden min-h-0">
        {activeTab === 'metadata' && <MetadataTab />}
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'lookml' && <LookMLTab />}
      </div>
    </div>
  );

  // Metadata Tab Component
  function MetadataTab() {
    return (
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-text-primary">AI Metadata Analysis</h3>
            <div className="flex items-center space-x-2">
              {metadata && (
                <span className="text-xs bg-success/10 text-success px-2 py-1 rounded">
                  Generated
                </span>
              )}
              {metadata && (
                <button
                  onClick={() => {
                    setMetadata(null);
                    setError(null);
                  }}
                  className="text-xs px-2 py-1 bg-accent/10 text-accent hover:bg-accent/20 rounded transition-colors"
                  title="Regenerate metadata with new settings"
                >
                  Regenerate
                </button>
              )}
            </div>
          </div>
          
          {!metadata && (
            <p className="text-sm text-text-secondary mb-4">
              Generate AI-powered metadata to get detailed insights about table structure, 
              business context, data quality, and relationships.
            </p>
          )}
          
          {metadata && (
            <p className="text-sm text-text-secondary">
              Click "Regenerate" to create new metadata with different configuration options.
            </p>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {!metadata ? (
            <div className="p-4">
              {/* Configuration Options */}
              <div className="space-y-4 mb-6">
                <h4 className="text-sm font-medium text-text-primary">Generation Options</h4>
                
                <div className="grid grid-cols-2 gap-3">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeDataQuality}
                      onChange={(e) => handleConfigChange('includeDataQuality', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Data Quality</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeBusinessRules}
                      onChange={(e) => handleConfigChange('includeBusinessRules', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Business Rules</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeCategoricalDefinitions}
                      onChange={(e) => handleConfigChange('includeCategoricalDefinitions', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Categorical Values</span>
                  </label>
                  
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeRelationships}
                      onChange={(e) => handleConfigChange('includeRelationships', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Relationships</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeQueryExamples}
                      onChange={(e) => handleConfigChange('includeQueryExamples', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Query Examples</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeAggregationRules}
                      onChange={(e) => handleConfigChange('includeAggregationRules', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Aggregation Rules</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeQueryRules}
                      onChange={(e) => handleConfigChange('includeQueryRules', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Query Rules</span>
                  </label>

                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.includeAdditionalInsights}
                      onChange={(e) => handleConfigChange('includeAdditionalInsights', e.target.checked)}
                      className="w-4 h-4 text-accent bg-surface border-border rounded focus:ring-accent focus:ring-2"
                    />
                    <span className="text-sm text-text-secondary">Additional Insights</span>
                  </label>
                </div>

                {/* Quick Presets */}
                <div className="mt-4 pt-4 border-t border-border">
                  <h5 className="text-xs font-medium text-text-primary mb-2">Quick Presets</h5>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => {
                        handleConfigChange('includeDataQuality', true);
                        handleConfigChange('includeBusinessRules', true);
                        handleConfigChange('includeCategoricalDefinitions', true);
                        handleConfigChange('includeRelationships', true);
                        handleConfigChange('includeQueryExamples', true);
                        handleConfigChange('includeAggregationRules', true);
                        handleConfigChange('includeQueryRules', true);
                        handleConfigChange('includeAdditionalInsights', true);
                      }}
                      className="px-3 py-1 text-xs bg-primary/10 text-primary hover:bg-primary/20 rounded transition-colors"
                    >
                      All Features
                    </button>
                    <button
                      onClick={() => {
                        handleConfigChange('includeDataQuality', false);
                        handleConfigChange('includeBusinessRules', false);
                        handleConfigChange('includeCategoricalDefinitions', true);
                        handleConfigChange('includeRelationships', false);
                        handleConfigChange('includeQueryExamples', false);
                        handleConfigChange('includeAggregationRules', false);
                        handleConfigChange('includeQueryRules', false);
                        handleConfigChange('includeAdditionalInsights', false);
                      }}
                      className="px-3 py-1 text-xs bg-accent/10 text-accent hover:bg-accent/20 rounded transition-colors"
                    >
                      Essential Only
                    </button>
                    <button
                      onClick={() => {
                        handleConfigChange('includeDataQuality', true);
                        handleConfigChange('includeBusinessRules', true);
                        handleConfigChange('includeCategoricalDefinitions', true);
                        handleConfigChange('includeRelationships', true);
                        handleConfigChange('includeQueryExamples', true);
                        handleConfigChange('includeAggregationRules', true);
                        handleConfigChange('includeQueryRules', false);
                        handleConfigChange('includeAdditionalInsights', false);
                      }}
                      className="px-3 py-1 text-xs bg-secondary/10 text-secondary hover:bg-secondary/20 rounded transition-colors"
                    >
                      Analytics Focus
                    </button>
                  </div>
                </div>

                {/* Custom Instructions */}
                <div className="mt-4 pt-4 border-t border-border">
                  <h5 className="text-xs font-medium text-text-primary mb-2">Custom Instructions (Optional)</h5>
                  <textarea
                    value={configuration.customPrompt || ''}
                    onChange={(e) => handleConfigChange('customPrompt', e.target.value)}
                    placeholder="Enter custom instructions for the AI analysis..."
                    rows={3}
                    maxLength={2000}
                    className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent resize-none text-xs"
                  />
                  <div className="flex justify-between text-xs text-text-muted mt-1">
                    <span>Customize the analysis instructions</span>
                    <span>{configuration.customPrompt?.length || 0}/2000</span>
                  </div>
                </div>
              </div>

              {/* Generate Button */}
              <Button
                variant="primary"
                onClick={handleGenerateMetadata}
                disabled={isGenerating}
                loading={isGenerating}
                fullWidth
                iconName={isGenerating ? undefined : "Sparkles"}
              >
                {isGenerating ? 'Generating Metadata...' : 'Generate AI Metadata'}
              </Button>

              {error && (
                <div className="mt-4 p-3 bg-error/10 border border-error/20 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <Icon name="AlertCircle" size={16} className="text-error mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-error">Generation Failed</div>
                      <div className="text-xs text-error/80 mt-1">{error}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {/* Generation Status */}
              <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Icon name="CheckCircle" size={16} className="text-success" />
                  <div>
                    <div className="text-sm font-medium text-success">Metadata Generated Successfully</div>
                    <div className="text-xs text-success/80">
                      View insights in the Overview and Misc tabs
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              {metadata.table_description && (
                <div className="p-3 bg-surface-secondary rounded-lg border border-border">
                  <h4 className="text-sm font-medium text-text-primary mb-2">Quick Info</h4>
                  <div className="space-y-1 text-xs text-text-secondary">
                    <div>✓ Table insights generated</div>
                    {metadata.categorical_definitions && (
                      <div>✓ Categorical definitions included</div>
                    )}
                    {metadata.business_rules && (
                      <div>✓ Business rules defined</div>
                    )}
                    {metadata.query_examples && metadata.query_examples.length > 0 && (
                      <div>✓ {metadata.query_examples.length} query examples</div>
                    )}
                    {metadata.relationships && metadata.relationships.length > 0 && (
                      <div>✓ {metadata.relationships.length} relationships found</div>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="space-y-2">
                <button
                  onClick={() => {
                    setMetadata(null);
                    setError(null);
                  }}
                  className="w-full px-3 py-2 bg-accent/10 text-accent hover:bg-accent/20 rounded transition-colors text-sm font-medium"
                >
                  Regenerate Metadata
                </button>
                
                <div className="text-center">
                  <p className="text-xs text-text-muted">
                    All insights are now displayed in the main tabs
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Chat Tab Component
  function ChatTab() {
    return (
      <div className="h-full flex flex-col">
        {/* Messages - Fixed height container */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto p-3 space-y-3">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-center">
                <div>
                  <Icon name="MessageSquare" size={32} className="text-text-muted mx-auto mb-2" />
                  <p className="text-text-secondary text-sm">
                    I'm ready to help you analyze the<br/>
                    <strong>{selectedTable.name}</strong> table. What would you like<br/>
                    to know about it?
                  </p>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] p-2.5 rounded-lg ${
                        message.isUser
                          ? 'bg-primary text-primary-foreground'
                          : message.isError
                          ? 'bg-error/10 border border-error/20 text-error'
                          : 'bg-surface-secondary text-text-primary'
                      }`}
                    >
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      <div className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isTyping && (
                  <div className="flex justify-start">
                    <div className="bg-surface-secondary p-2.5 rounded-lg">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Message Input - Always visible at bottom */}
        <div className="flex-shrink-1 border-t border-border p-3 bg-surface min-h-[60px]">
          <ChatInput onSend={handleSendMessage} disabled={chatLoading} />
        </div>
      </div>
    );
  }

  // LookML Tab Component
  function LookMLTab() {
    return (
      <div className="h-full flex flex-col p-4">
        <div className="text-center py-8">
          <Icon name="Code" size={48} className="text-text-muted mx-auto mb-4" />
          <h4 className="text-lg font-medium text-text-primary mb-2">LookML Generator</h4>
          <p className="text-text-secondary text-sm mb-6">
            Generate LookML view files for your selected table
          </p>
          
          <Button
            variant="secondary"
            iconName="Code"
            onClick={handleCreateLookML}
            className="justify-center"
          >
            Generate LookML File
          </Button>
          
          <div className="mt-6 p-4 bg-surface-secondary/50 rounded-lg border border-border">
            <p className="text-xs text-text-muted">
              <strong>Note:</strong> This feature is currently in development. 
              The generated LookML file will be automatically downloaded when ready.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Chat Input Component
  function ChatInput({ onSend, disabled }) {
    const [input, setInput] = useState('');

    const handleSubmit = (e) => {
      e.preventDefault();
      if (input.trim() && !disabled) {
        onSend(input.trim());
        setInput('');
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="flex space-x-2 items-end">
        <div className="flex-1">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask about ${selectedTable?.name || 'this table'}...`}
            disabled={disabled}
            className="w-full"
          />
          <div className="text-xs text-text-muted mt-1">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
        <Button
          type="submit"
          iconName="Send"
          disabled={!input.trim() || disabled}
          loading={disabled}
          className="flex-shrink-0"
        />
      </form>
    );
  }
};

export default MetadataPanel;