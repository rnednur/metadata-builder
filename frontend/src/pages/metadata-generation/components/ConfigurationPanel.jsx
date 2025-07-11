import React, { useState } from 'react';
import Icon from '../../../components/AppIcon';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';

const ConfigurationPanel = ({ 
  configuration, 
  onConfigurationChange, 
  onStartGeneration,
  isGenerating,
  hasValidSelection 
}) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['basic', 'advanced']));

  const toggleSection = (sectionId) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const handleConfigChange = (field, value) => {
    onConfigurationChange({
      ...configuration,
      [field]: value
    });
  };

  const applyPreset = (preset) => {
    onConfigurationChange({
      ...configuration,
      ...preset.settings
    });
  };

  const llmModels = [
    { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI', description: 'Most capable model for complex analysis' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI', description: 'Fast and efficient for standard analysis' },
    { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic', description: 'Excellent for detailed documentation' },
    { id: 'gemini-pro', name: 'Gemini Pro', provider: 'Google', description: 'Strong analytical capabilities' }
  ];

  const quickPresets = [
    { 
      id: 'essential', 
      label: 'Essential Only', 
      description: 'Column definitions, table insights, and categorical values',
      settings: {
        dataQuality: false,
        categoricalValues: true,
        queryExamples: false,
        queryRules: false,
        businessRules: false,
        relationships: false,
        aggregationRules: false,
        additionalInsights: false
      }
    },
    { 
      id: 'all', 
      label: 'All Features', 
      description: 'Complete analysis with all available insights',
      settings: {
        dataQuality: true,
        categoricalValues: true,
        queryExamples: true,
        queryRules: true,
        businessRules: true,
        relationships: true,
        aggregationRules: true,
        additionalInsights: true
      }
    },
    { 
      id: 'analytics', 
      label: 'Analytics Focus', 
      description: 'Optimized for analytics and business intelligence',
      settings: {
        dataQuality: true,
        categoricalValues: true,
        queryExamples: true,
        queryRules: false,
        businessRules: true,
        relationships: false,
        aggregationRules: true,
        additionalInsights: false
      }
    }
  ];

  const validateConfiguration = () => {
    const errors = [];
    
    if (configuration.sampleSize < 100 || configuration.sampleSize > 100000) {
      errors.push('Sample size must be between 100 and 100,000');
    }
    
    if (configuration.partitionLimit < 1 || configuration.partitionLimit > 50) {
      errors.push('Partition limit must be between 1 and 50');
    }
    
    if (configuration.customPrompt && configuration.customPrompt.length > 2000) {
      errors.push('Custom prompt must be less than 2000 characters');
    }
    
    return errors;
  };

  const configErrors = validateConfiguration();
  const isValid = configErrors.length === 0 && hasValidSelection;

  const ConfigSection = ({ id, title, icon, children, defaultExpanded = false }) => {
    const isExpanded = expandedSections.has(id);
    
    return (
      <div className="border border-border rounded-lg">
        <div 
          className="flex items-center justify-between p-4 cursor-pointer hover:bg-surface-secondary transition-colors"
          onClick={() => toggleSection(id)}
        >
          <div className="flex items-center space-x-3">
            <Icon name={icon} size={18} className="text-primary" />
            <h4 className="font-medium text-text-primary">{title}</h4>
          </div>
          <Icon 
            name="ChevronRight" 
            size={16} 
            className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          />
        </div>
        {isExpanded && (
          <div className="border-t border-border p-4 bg-surface-secondary/30">
            {children}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-surface border border-border rounded-lg h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-text-primary mb-2">Generation Configuration</h3>
        <p className="text-sm text-text-secondary">
          Configure parameters for AI-powered metadata analysis
        </p>
      </div>

      {/* Configuration Sections */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Basic Parameters */}
        <ConfigSection id="basic" title="Basic Parameters" icon="Settings" defaultExpanded>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Sample Size
              </label>
              <Input
                type="number"
                value={configuration.sampleSize}
                onChange={(e) => handleConfigChange('sampleSize', parseInt(e.target.value))}
                placeholder="10000"
                min="100"
                max="100000"
              />
              <p className="text-xs text-text-muted mt-1">
                Number of rows to analyze per table (100 - 100,000)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Partition Limit
              </label>
              <Input
                type="number"
                value={configuration.partitionLimit}
                onChange={(e) => handleConfigChange('partitionLimit', parseInt(e.target.value))}
                placeholder="10"
                min="1"
                max="50"
              />
              <p className="text-xs text-text-muted mt-1">
                Maximum partitions to analyze per table (1 - 50)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-3">
                Generation Options
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-3">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.dataQuality || false}
                      onChange={(e) => handleConfigChange('dataQuality', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Data Quality</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.categoricalValues || false}
                      onChange={(e) => handleConfigChange('categoricalValues', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Categorical Values</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.queryExamples || false}
                      onChange={(e) => handleConfigChange('queryExamples', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Query Examples</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.queryRules || false}
                      onChange={(e) => handleConfigChange('queryRules', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Query Rules</span>
                  </label>
                </div>
                <div className="space-y-3">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.businessRules || false}
                      onChange={(e) => handleConfigChange('businessRules', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Business Rules</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.relationships || false}
                      onChange={(e) => handleConfigChange('relationships', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Relationships</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.aggregationRules || false}
                      onChange={(e) => handleConfigChange('aggregationRules', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Aggregation Rules</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configuration.additionalInsights || false}
                      onChange={(e) => handleConfigChange('additionalInsights', e.target.checked)}
                    />
                    <span className="text-sm text-text-primary">Additional Insights</span>
                  </label>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-3">
                Quick Presets
              </label>
              <div className="flex space-x-2">
                {quickPresets.map((preset) => (
                  <Button
                    key={preset.id}
                    variant={preset.id === 'essential' ? 'primary' : 'ghost'}
                    onClick={() => applyPreset(preset)}
                    className="text-sm px-3 py-2"
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Custom Instructions (Optional)
              </label>
              <textarea
                value={configuration.customPrompt || ''}
                onChange={(e) => handleConfigChange('customPrompt', e.target.value)}
                placeholder="Enter custom instructions for the AI analysis..."
                rows={3}
                maxLength={2000}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent resize-none text-sm"
              />
              <div className="flex justify-between text-xs text-text-muted mt-1">
                <span>Customize the analysis instructions</span>
                <span>{configuration.customPrompt?.length || 0}/2000</span>
              </div>
            </div>
          </div>
        </ConfigSection>

        {/* LLM Configuration - Commented out, using default model from Explore page */}
        {/*
        <ConfigSection id="llm" title="LLM Model Selection" icon="Brain">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-3">
                Select Model
              </label>
              <div className="space-y-3">
                {llmModels.map((model) => (
                  <label key={model.id} className="flex items-start space-x-3 cursor-pointer p-3 border border-border rounded-lg hover:bg-surface-secondary transition-colors">
                    <input
                      type="radio"
                      name="llmModel"
                      value={model.id}
                      checked={configuration.llmModel === model.id}
                      onChange={(e) => handleConfigChange('llmModel', e.target.value)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-text-primary">{model.name}</span>
                        <span className="text-xs bg-secondary-100 text-secondary-700 px-2 py-1 rounded">
                          {model.provider}
                        </span>
                      </div>
                      <div className="text-xs text-text-secondary mt-1">{model.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={configuration.includeBusinessContext}
                  onChange={(e) => handleConfigChange('includeBusinessContext', e.target.checked)}
                />
                <span className="text-sm text-text-primary">Include business context analysis</span>
              </label>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={configuration.generateLookML}
                  onChange={(e) => handleConfigChange('generateLookML', e.target.checked)}
                />
                <span className="text-sm text-text-primary">Generate LookML semantic models</span>
              </label>
            </div>
          </div>
        </ConfigSection>
        */}

        {/* Advanced Options */}
        <ConfigSection id="advanced" title="Advanced Options" icon="Cog">
          <div className="space-y-4">
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={configuration.enableParallelProcessing}
                  onChange={(e) => handleConfigChange('enableParallelProcessing', e.target.checked)}
                />
                <span className="text-sm text-text-primary">Enable parallel processing</span>
              </label>
              <p className="text-xs text-text-muted mt-1 ml-6">
                Process multiple tables simultaneously for faster completion
              </p>
            </div>

            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={configuration.saveIntermediateResults}
                  onChange={(e) => handleConfigChange('saveIntermediateResults', e.target.checked)}
                />
                <span className="text-sm text-text-primary">Save intermediate results</span>
              </label>
              <p className="text-xs text-text-muted mt-1 ml-6">
                Save progress to resume if interrupted
              </p>
            </div>
          </div>
        </ConfigSection>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        {/* Validation Errors */}
        {configErrors.length > 0 && (
          <div className="mb-4 p-3 bg-error-50 border border-error-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Icon name="AlertCircle" size={16} className="text-error mt-0.5" />
              <div>
                <div className="text-sm font-medium text-error">Configuration Errors</div>
                <ul className="text-xs text-error-700 mt-1 space-y-1">
                  {configErrors.map((error, index) => (
                    <li key={index}>• {error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Start Generation Button */}
        <Button
          variant="primary"
          onClick={onStartGeneration}
          disabled={!isValid || isGenerating}
          loading={isGenerating}
          fullWidth
          iconName={isGenerating ? undefined : "Sparkles"}
        >
          {isGenerating ? 'Generating AI Metadata...' : 'Generate AI Metadata'}
        </Button>

        {!hasValidSelection && (
          <p className="text-xs text-text-muted text-center mt-2">
            Select at least one table to begin generation
          </p>
        )}
      </div>
    </div>
  );
};

export default ConfigurationPanel;