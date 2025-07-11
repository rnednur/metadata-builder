import React, { useState } from 'react';
import Input from '../../../components/ui/Input';

import Icon from '../../../components/AppIcon';

const AuthenticationForm = ({ 
  formData, 
  onChange, 
  errors, 
  databaseType 
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleInputChange = (field, value) => {
    onChange(field, value);
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const shouldShowAuth = () => {
    return databaseType && !['sqlite', 'duckdb'].includes(databaseType.id);
  };

  const shouldShowCredentials = () => {
    return databaseType && !['bigquery'].includes(databaseType.id) && shouldShowAuth();
  };

  if (!shouldShowAuth()) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-text-primary flex items-center space-x-2">
          <Icon name="Shield" size={20} className="text-accent" />
          <span>Authentication</span>
        </h3>

        {/* BigQuery Service Account */}
        {databaseType?.id === 'bigquery' && (
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Service Account Key (JSON) <span className="text-error">*</span>
            </label>
            <textarea
              rows={6}
              placeholder="Paste your service account JSON key here..."
              value={formData.serviceAccountKey || ''}
              onChange={(e) => handleInputChange('serviceAccountKey', e.target.value)}
              className={`w-full px-3 py-2 border rounded-lg text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent transition-all duration-150 ${
                errors.serviceAccountKey ? 'border-error' : 'border-border'
              }`}
            />
            {errors.serviceAccountKey && (
              <p className="text-sm text-error mt-1 flex items-center space-x-1">
                <Icon name="AlertCircle" size={16} />
                <span>{errors.serviceAccountKey}</span>
              </p>
            )}
            <p className="text-xs text-text-muted mt-1">
              Download the JSON key file from Google Cloud Console and paste its contents here
            </p>
          </div>
        )}

        {/* Username & Password */}
        {shouldShowCredentials() && (
          <>
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Username <span className="text-error">*</span>
              </label>
              <Input
                type="text"
                placeholder="Database username"
                value={formData.username || ''}
                onChange={(e) => handleInputChange('username', e.target.value)}
                className={errors.username ? 'border-error' : ''}
              />
              {errors.username && (
                <p className="text-sm text-error mt-1 flex items-center space-x-1">
                  <Icon name="AlertCircle" size={16} />
                  <span>{errors.username}</span>
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Password <span className="text-error">*</span>
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Database password"
                  value={formData.password || ''}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className={`pr-10 ${errors.password ? 'border-error' : ''}`}
                />
                <button
                  type="button"
                  onClick={togglePasswordVisibility}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary transition-colors duration-150"
                >
                  <Icon name={showPassword ? 'EyeOff' : 'Eye'} size={16} />
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-error mt-1 flex items-center space-x-1">
                  <Icon name="AlertCircle" size={16} />
                  <span>{errors.password}</span>
                </p>
              )}
            </div>
          </>
        )}

        {/* SSL Options */}
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="sslEnabled"
              checked={formData.sslEnabled || false}
              onChange={(e) => handleInputChange('sslEnabled', e.target.checked)}
              className="w-4 h-4 text-accent border-border rounded focus:ring-accent focus:ring-2"
            />
            <label htmlFor="sslEnabled" className="text-sm font-medium text-text-primary">
              Enable SSL/TLS
            </label>
          </div>
          
          {formData.sslEnabled && (
            <div className="ml-7 space-y-3">
              <div className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  id="sslVerify"
                  checked={formData.sslVerify || false}
                  onChange={(e) => handleInputChange('sslVerify', e.target.checked)}
                  className="w-4 h-4 text-accent border-border rounded focus:ring-accent focus:ring-2"
                />
                <label htmlFor="sslVerify" className="text-sm text-text-secondary">
                  Verify SSL certificate
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Advanced Settings */}
        <div className="border-t border-border pt-4">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-sm font-medium text-accent hover:text-accent-600 transition-colors duration-150"
          >
            <Icon 
              name="ChevronRight" 
              size={16} 
              className={`transition-transform duration-150 ${showAdvanced ? 'rotate-90' : ''}`}
            />
            <span>Advanced Settings</span>
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-4 pl-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Connection Timeout (seconds)
                  </label>
                  <Input
                    type="number"
                    placeholder="30"
                    value={formData.connectionTimeout || ''}
                    onChange={(e) => handleInputChange('connectionTimeout', e.target.value)}
                    min="1"
                    max="300"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-2">
                    Query Timeout (seconds)
                  </label>
                  <Input
                    type="number"
                    placeholder="60"
                    value={formData.queryTimeout || ''}
                    onChange={(e) => handleInputChange('queryTimeout', e.target.value)}
                    min="1"
                    max="3600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-primary mb-2">
                  Additional Parameters
                </label>
                <Input
                  type="text"
                  placeholder="key1=value1&key2=value2"
                  value={formData.additionalParams || ''}
                  onChange={(e) => handleInputChange('additionalParams', e.target.value)}
                />
                <p className="text-xs text-text-muted mt-1">
                  Additional connection parameters in URL format
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthenticationForm;