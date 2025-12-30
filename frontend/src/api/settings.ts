/**
 * LLM Settings API
 *
 * Handles API calls for LLM provider and model configuration.
 */

// API base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Types
export type LLMProvider = 'anthropic' | 'groq';

export interface ProviderInfo {
  id: LLMProvider;
  name: string;
  configured: boolean;
  models: string[];
}

export interface LLMSettings {
  provider: LLMProvider;
  model: string;
  available_providers: ProviderInfo[];
  anthropic_configured: boolean;
  groq_configured: boolean;
}

export interface LLMSettingsUpdate {
  provider: LLMProvider;
  model: string;
}

export interface AvailableModels {
  anthropic: string[];
  groq: string[];
}

// Error handling
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message =
      errorData.detail?.message || errorData.detail || response.statusText;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return response.json();
}

export const settingsApi = {
  /**
   * Get current LLM settings
   */
  async getSettings(): Promise<LLMSettings> {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'GET',
      credentials: 'include',
    });
    return handleResponse<LLMSettings>(response);
  },

  /**
   * Update LLM settings
   */
  async updateSettings(settings: LLMSettingsUpdate): Promise<LLMSettings> {
    const response = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(settings),
    });
    return handleResponse<LLMSettings>(response);
  },

  /**
   * Get available models for each provider
   */
  async getAvailableModels(): Promise<AvailableModels> {
    const response = await fetch(`${API_BASE}/settings/models`, {
      method: 'GET',
      credentials: 'include',
    });
    return handleResponse<AvailableModels>(response);
  },
};
