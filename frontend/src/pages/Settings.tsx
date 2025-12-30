import { useState, useEffect } from 'react';
import { MainWorkspace } from '../components/layout';
import { useTheme } from '../providers';
import { settingsApi, type LLMSettings, type LLMProvider } from '../api';

export function SettingsPage() {
  const { theme, toggleTheme } = useTheme();
  const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider>('anthropic');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const settings = await settingsApi.getSettings();
      setLlmSettings(settings);
      setSelectedProvider(settings.provider);
      setSelectedModel(settings.model);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleProviderChange = (provider: LLMProvider) => {
    setSelectedProvider(provider);
    // Reset model to first available for the new provider
    const providerInfo = llmSettings?.available_providers.find(p => p.id === provider);
    if (providerInfo && providerInfo.models.length > 0) {
      setSelectedModel(providerInfo.models[0]);
    }
    setSuccessMessage(null);
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
    setSuccessMessage(null);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);
      const updated = await settingsApi.updateSettings({
        provider: selectedProvider,
        model: selectedModel,
      });
      setLlmSettings(updated);
      setSuccessMessage('Settings saved successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const getCurrentProviderModels = (): string[] => {
    const providerInfo = llmSettings?.available_providers.find(p => p.id === selectedProvider);
    return providerInfo?.models || [];
  };

  const isProviderConfigured = (provider: LLMProvider): boolean => {
    const providerInfo = llmSettings?.available_providers.find(p => p.id === provider);
    return providerInfo?.configured || false;
  };

  const hasChanges = llmSettings && (
    selectedProvider !== llmSettings.provider ||
    selectedModel !== llmSettings.model
  );

  return (
    <MainWorkspace title="Settings">
      <div className="settings-section">
        <h2>Appearance</h2>
        <div className="setting-item">
          <label>
            Theme
            <select value={theme} onChange={() => toggleTheme()}>
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </label>
        </div>
      </div>

      <div className="settings-section" style={{ marginTop: '2rem' }}>
        <h2>LLM Configuration</h2>

        {isLoading ? (
          <p>Loading settings...</p>
        ) : error ? (
          <div className="error-message" style={{ color: 'var(--color-error, #dc2626)', marginBottom: '1rem' }}>
            {error}
            <button onClick={loadSettings} style={{ marginLeft: '1rem' }}>
              Retry
            </button>
          </div>
        ) : (
          <>
            <div className="setting-item" style={{ marginBottom: '1rem' }}>
              <label>
                Provider
                <select
                  value={selectedProvider}
                  onChange={(e) => handleProviderChange(e.target.value as LLMProvider)}
                  disabled={isSaving}
                >
                  {llmSettings?.available_providers.map((provider) => (
                    <option
                      key={provider.id}
                      value={provider.id}
                      disabled={!provider.configured}
                    >
                      {provider.name} {!provider.configured && '(API key not configured)'}
                    </option>
                  ))}
                </select>
              </label>
              {!isProviderConfigured(selectedProvider) && (
                <p style={{ color: 'var(--color-warning, #f59e0b)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                  Add {selectedProvider === 'anthropic' ? 'ANTHROPIC_API_KEY' : 'GROQ_API_KEY'} to your .env file to use this provider.
                </p>
              )}
            </div>

            <div className="setting-item" style={{ marginBottom: '1rem' }}>
              <label>
                Model
                <select
                  value={selectedModel}
                  onChange={(e) => handleModelChange(e.target.value)}
                  disabled={isSaving || !isProviderConfigured(selectedProvider)}
                >
                  {getCurrentProviderModels().map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="setting-item" style={{ marginTop: '1.5rem' }}>
              <button
                onClick={handleSave}
                disabled={isSaving || !hasChanges || !isProviderConfigured(selectedProvider)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: hasChanges ? 'var(--color-primary, #2563eb)' : 'var(--color-muted, #9ca3af)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.375rem',
                  cursor: hasChanges ? 'pointer' : 'not-allowed',
                }}
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>

              {successMessage && (
                <span style={{ marginLeft: '1rem', color: 'var(--color-success, #16a34a)' }}>
                  {successMessage}
                </span>
              )}
            </div>

            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--color-surface, #f3f4f6)', borderRadius: '0.5rem' }}>
              <h3 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 600 }}>Current Configuration</h3>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>
                <strong>Provider:</strong> {llmSettings?.provider === 'anthropic' ? 'Anthropic (Claude)' : 'Groq'}
              </p>
              <p style={{ margin: 0, fontSize: '0.875rem' }}>
                <strong>Model:</strong> {llmSettings?.model}
              </p>
            </div>
          </>
        )}
      </div>
    </MainWorkspace>
  );
}
