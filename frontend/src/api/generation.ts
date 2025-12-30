/**
 * Generation API Service
 *
 * REST API client for document generation endpoints.
 * Based on Section 7.1 of the Frontend Design Document.
 */

import type {
  DocumentRequest,
  FinalOutput,
  GeneratedDocument,
  SwarmConfig,
} from '../types';

// API base URL - can be configured via environment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// ============================================================================
// Types
// ============================================================================

export interface GenerationStartResponse {
  requestId: string;
  status: 'queued' | 'started';
  estimatedDuration?: number;
}

export interface GenerationStatusResponse {
  requestId: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'review';
  progress?: {
    currentRound: number;
    totalRounds: number;
    phase: string;
  };
  result?: FinalOutput;
  error?: string;
}

export interface RegenerationOptions {
  retryWithSameConfig?: boolean;
  retryWithHigherRounds?: boolean;
  newConfig?: Partial<SwarmConfig>;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Error Handling
// ============================================================================

export class GenerationApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(
    message: string,
    code: string,
    status: number,
    details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'GenerationApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let error: ApiError;
    try {
      const errorData = await response.json();
      console.error('[API] Error response:', errorData);
      // Handle FastAPI's validation error format
      if (errorData.detail) {
        if (typeof errorData.detail === 'string') {
          error = { code: 'API_ERROR', message: errorData.detail };
        } else if (Array.isArray(errorData.detail)) {
          // Pydantic validation errors
          const messages = errorData.detail.map((e: { loc?: string[]; msg?: string }) =>
            `${e.loc?.join('.')}: ${e.msg}`
          ).join('; ');
          error = { code: 'VALIDATION_ERROR', message: messages, details: { errors: errorData.detail } };
        } else {
          error = {
            code: errorData.detail.code || 'API_ERROR',
            message: errorData.detail.message || JSON.stringify(errorData.detail)
          };
        }
      } else {
        error = errorData;
      }
    } catch {
      error = {
        code: 'UNKNOWN_ERROR',
        message: response.statusText || 'An unknown error occurred',
      };
    }
    throw new GenerationApiError(
      error.message,
      error.code,
      response.status,
      error.details
    );
  }
  return response.json();
}

// ============================================================================
// Document Generation Endpoints
// ============================================================================

/**
 * Transform frontend SwarmConfig to backend-compatible format
 *
 * The frontend uses kebab-case agent IDs in dictionaries,
 * but the backend expects camelCase field names in typed schemas.
 */
function transformRequestForBackend(request: DocumentRequest): Record<string, unknown> {
  const config = request.config;

  // Transform blueTeam from {'strategy-architect': true} to {strategyArchitect: true}
  const blueTeam = {
    strategyArchitect: config.blueTeam['strategy-architect'] ?? true,
    marketAnalyst: config.blueTeam['market-analyst'] ?? false,
    complianceNavigator: config.blueTeam['compliance-navigator'] ?? true,
    captureStrategist: config.blueTeam['capture-strategist'] ?? false,
  };

  // Transform redTeam from {'devils-advocate': true} to {devilsAdvocate: true}
  const redTeam = {
    devilsAdvocate: config.redTeam['devils-advocate'] ?? true,
    competitorSimulator: config.redTeam['competitor-simulator'] ?? false,
    evaluatorSimulator: config.redTeam['evaluator-simulator'] ?? true,
    riskAssessor: config.redTeam['risk-assessor'] ?? false,
  };

  return {
    documentType: request.documentType,
    companyProfileId: request.companyProfileId,
    opportunityContext: request.opportunityContext,
    config: {
      intensity: config.intensity,
      rounds: config.rounds,
      consensus: config.consensus,
      blueTeam,
      redTeam,
      specialists: config.specialists,
      riskTolerance: config.riskTolerance,
      escalationThresholds: config.escalationThresholds,
    },
  };
}

/**
 * Start a new document generation
 *
 * @param request - The document generation request
 * @param connectionId - WebSocket connection ID for receiving real-time updates
 */
export async function startGeneration(
  request: DocumentRequest,
  connectionId: string
): Promise<GenerationStartResponse> {
  const url = new URL(`${API_BASE}/documents/generate`, window.location.origin);
  url.searchParams.set('connectionId', connectionId);

  // Transform to backend format
  const backendRequest = transformRequestForBackend(request);

  const response = await fetch(url.toString(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(backendRequest),
  });

  return handleResponse<GenerationStartResponse>(response);
}

/**
 * Get the status of a generation request
 */
export async function getGenerationStatus(
  requestId: string
): Promise<GenerationStatusResponse> {
  const response = await fetch(`${API_BASE}/documents/generate/${requestId}/status`, {
    method: 'GET',
    credentials: 'include',
  });

  return handleResponse<GenerationStatusResponse>(response);
}

/**
 * Get a document by ID
 */
export async function getDocument(documentId: string): Promise<FinalOutput> {
  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: 'GET',
    credentials: 'include',
  });

  return handleResponse<FinalOutput>(response);
}

/**
 * List user's documents with optional filtering
 */
export async function listDocuments(options?: {
  limit?: number;
  offset?: number;
  status?: 'draft' | 'approved' | 'rejected';
  type?: string;
}): Promise<{
  documents: GeneratedDocument[];
  total: number;
  hasMore: boolean;
}> {
  const params = new URLSearchParams();
  if (options?.limit) params.set('limit', options.limit.toString());
  if (options?.offset) params.set('offset', options.offset.toString());
  if (options?.status) params.set('status', options.status);
  if (options?.type) params.set('type', options.type);

  const response = await fetch(`${API_BASE}/documents?${params}`, {
    method: 'GET',
    credentials: 'include',
  });

  return handleResponse(response);
}

/**
 * Regenerate a document with new options
 */
export async function regenerateDocument(
  documentId: string,
  options: RegenerationOptions
): Promise<GenerationStartResponse> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/regenerate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(options),
  });

  return handleResponse<GenerationStartResponse>(response);
}

/**
 * Approve a document after human review
 */
export async function approveDocument(
  documentId: string,
  notes?: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/approve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ notes }),
  });

  return handleResponse(response);
}

/**
 * Reject a document after human review
 */
export async function rejectDocument(
  documentId: string,
  reason?: string
): Promise<{ success: boolean }> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/reject`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ reason }),
  });

  return handleResponse(response);
}

// ============================================================================
// Export Endpoints
// ============================================================================

import type { ExportFormat } from '../types';

export interface ExportResult {
  blob?: Blob;
  url?: string;
  format: ExportFormat;
}

/**
 * Export a document in the specified format
 */
export async function exportDocument(
  documentId: string,
  format: ExportFormat
): Promise<ExportResult> {
  // Handle share format separately
  if (format === 'share') {
    const shareResult = await createShareLink(documentId);
    return {
      url: shareResult.url,
      format: 'share',
    };
  }

  const response = await fetch(
    `${API_BASE}/documents/${documentId}/export?format=${format}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      code: 'EXPORT_ERROR',
      message: 'Failed to export document',
    }));
    throw new GenerationApiError(
      error.message,
      error.code,
      response.status,
      error.details
    );
  }

  return {
    blob: await response.blob(),
    format,
  };
}

/**
 * Get a shareable link for a document
 */
export async function createShareLink(
  documentId: string,
  options?: {
    expiresIn?: number; // Hours until expiration
    password?: string;
  }
): Promise<{ url: string; expiresAt: Date }> {
  const response = await fetch(`${API_BASE}/documents/${documentId}/share`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(options || {}),
  });

  return handleResponse(response);
}

// Re-export API functions
export const generationApi = {
  startGeneration,
  getGenerationStatus,
  getDocument,
  listDocuments,
  regenerateDocument,
  approveDocument,
  rejectDocument,
  exportDocument,
  createShareLink,
};

export default generationApi;
