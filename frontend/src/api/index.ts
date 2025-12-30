/**
 * API Module Exports
 *
 * Centralized exports for all API services.
 */

export { profilesApi, type CreateProfileInput, type UpdateProfileInput } from './profiles';

export {
  generationApi,
  type GenerationStartResponse,
  type GenerationStatusResponse,
  type RegenerationOptions,
  type ApiError,
  type ExportResult,
  GenerationApiError,
} from './generation';

export {
  documentsApi,
  type DocumentsListParams,
  type DocumentsListResponse,
  type DeleteDocumentResponse,
  DocumentsApiError,
} from './documents';

export {
  settingsApi,
  type LLMProvider,
  type ProviderInfo,
  type LLMSettings,
  type LLMSettingsUpdate,
  type AvailableModels,
} from './settings';
