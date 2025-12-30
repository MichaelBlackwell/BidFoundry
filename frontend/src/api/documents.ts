/**
 * Documents API Service
 *
 * REST API client for document management endpoints.
 * Provides mock data support for development.
 * Based on Section 7.1 of the Frontend Design Document.
 */

import type {
  DocumentType,
  GeneratedDocument,
  FinalOutput,
  ExportFormat,
  GenerationMetrics,
  Phase,
} from '../types';

// API base URL - can be configured via environment
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Flag to enable mock mode for development - disabled to use real database
const MOCK_ENABLED = import.meta.env.VITE_MOCK_API === 'true';

// ============================================================================
// Types
// ============================================================================

export interface DocumentsListParams {
  limit?: number;
  offset?: number;
  status?: 'draft' | 'approved' | 'rejected';
  type?: DocumentType;
  search?: string;
  sortBy?: 'createdAt' | 'updatedAt' | 'title' | 'confidence';
  sortOrder?: 'asc' | 'desc';
}

export interface DocumentsListResponse {
  documents: GeneratedDocument[];
  total: number;
  hasMore: boolean;
}

export interface DeleteDocumentResponse {
  success: boolean;
}

// ============================================================================
// Error Handling
// ============================================================================

export class DocumentsApiError extends Error {
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
    this.name = 'DocumentsApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let error: { code: string; message: string; details?: Record<string, unknown> };
    try {
      error = await response.json();
    } catch {
      error = {
        code: 'UNKNOWN_ERROR',
        message: response.statusText || 'An unknown error occurred',
      };
    }
    throw new DocumentsApiError(
      error.message,
      error.code,
      response.status,
      error.details
    );
  }
  return response.json();
}

// ============================================================================
// Mock Data (used when VITE_MOCK_API=true)
// ============================================================================

const STORAGE_KEY = 'adversarial-swarm-documents';

function getMockDocuments(): GeneratedDocument[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed.map((doc: GeneratedDocument) => ({
        ...doc,
        createdAt: new Date(doc.createdAt),
        updatedAt: new Date(doc.updatedAt),
      }));
    }
  } catch {
    // Ignore parse errors
  }

  // Return seed data if nothing stored
  const seedData = generateSeedDocuments();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(seedData));
  return seedData;
}

function saveMockDocuments(documents: GeneratedDocument[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(documents));
}

function generateSeedDocuments(): GeneratedDocument[] {
  const now = new Date();
  const day = 24 * 60 * 60 * 1000;

  return [
    {
      id: 'doc-001',
      type: 'competitive-analysis',
      title: 'DHS EAGLE II Recompete - Competitive Analysis',
      companyProfileId: 'profile-001',
      status: 'approved',
      confidence: 82,
      createdAt: new Date(now.getTime() - 2 * day),
      updatedAt: new Date(now.getTime() - 2 * day),
    },
    {
      id: 'doc-002',
      type: 'capability-statement',
      title: 'Acme Federal Capability Statement - Cybersecurity',
      companyProfileId: 'profile-001',
      status: 'approved',
      confidence: 91,
      createdAt: new Date(now.getTime() - 5 * day),
      updatedAt: new Date(now.getTime() - 4 * day),
    },
    {
      id: 'doc-003',
      type: 'proposal-strategy',
      title: 'VA EHR Modernization - Proposal Strategy',
      companyProfileId: 'profile-001',
      status: 'draft',
      confidence: 68,
      createdAt: new Date(now.getTime() - 1 * day),
      updatedAt: new Date(now.getTime() - 1 * day),
    },
    {
      id: 'doc-004',
      type: 'swot-analysis',
      title: 'Q1 2025 Strategic Position - SWOT Analysis',
      companyProfileId: 'profile-002',
      status: 'approved',
      confidence: 87,
      createdAt: new Date(now.getTime() - 10 * day),
      updatedAt: new Date(now.getTime() - 8 * day),
    },
    {
      id: 'doc-005',
      type: 'teaming-strategy',
      title: 'DoD JEDI Follow-on Teaming Strategy',
      companyProfileId: 'profile-001',
      status: 'rejected',
      confidence: 54,
      createdAt: new Date(now.getTime() - 7 * day),
      updatedAt: new Date(now.getTime() - 6 * day),
    },
    {
      id: 'doc-006',
      type: 'go-to-market-strategy',
      title: 'GSA IT Schedule 70 Entry Strategy',
      companyProfileId: 'profile-002',
      status: 'approved',
      confidence: 79,
      createdAt: new Date(now.getTime() - 14 * day),
      updatedAt: new Date(now.getTime() - 12 * day),
    },
    {
      id: 'doc-007',
      type: 'bd-pipeline-plan',
      title: 'FY25 BD Pipeline - Federal Civilian',
      companyProfileId: 'profile-001',
      status: 'draft',
      confidence: 73,
      createdAt: new Date(now.getTime() - 3 * day),
      updatedAt: new Date(now.getTime() - 3 * day),
    },
    {
      id: 'doc-008',
      type: 'competitive-analysis',
      title: 'NASA SEWP VI - Competitive Landscape',
      companyProfileId: 'profile-002',
      status: 'approved',
      confidence: 85,
      createdAt: new Date(now.getTime() - 20 * day),
      updatedAt: new Date(now.getTime() - 18 * day),
    },
  ];
}

// Simulate network delay
function mockDelay(min = 150, max = 400): Promise<void> {
  const delay = Math.random() * (max - min) + min;
  return new Promise((resolve) => setTimeout(resolve, delay));
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * List documents with optional filtering and pagination
 */
async function listDocuments(
  params?: DocumentsListParams
): Promise<DocumentsListResponse> {
  if (MOCK_ENABLED) {
    await mockDelay();
    let documents = getMockDocuments();

    // Apply filters
    if (params?.status) {
      documents = documents.filter((d) => d.status === params.status);
    }
    if (params?.type) {
      documents = documents.filter((d) => d.type === params.type);
    }
    if (params?.search) {
      const search = params.search.toLowerCase();
      documents = documents.filter(
        (d) =>
          d.title.toLowerCase().includes(search) ||
          d.type.toLowerCase().includes(search)
      );
    }

    // Apply sorting
    const sortBy = params?.sortBy || 'updatedAt';
    const sortOrder = params?.sortOrder || 'desc';
    documents.sort((a, b) => {
      let aVal: string | number | Date;
      let bVal: string | number | Date;

      switch (sortBy) {
        case 'title':
          aVal = a.title;
          bVal = b.title;
          break;
        case 'confidence':
          aVal = a.confidence;
          bVal = b.confidence;
          break;
        case 'createdAt':
          aVal = new Date(a.createdAt);
          bVal = new Date(b.createdAt);
          break;
        case 'updatedAt':
        default:
          aVal = new Date(a.updatedAt);
          bVal = new Date(b.updatedAt);
          break;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    // Apply pagination
    const total = documents.length;
    const offset = params?.offset || 0;
    const limit = params?.limit || 20;
    const paginated = documents.slice(offset, offset + limit);

    return {
      documents: paginated,
      total,
      hasMore: offset + limit < total,
    };
  }

  // Real API call
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.status) searchParams.set('status', params.status);
  if (params?.type) searchParams.set('type', params.type);
  if (params?.search) searchParams.set('search', params.search);
  if (params?.sortBy) searchParams.set('sortBy', params.sortBy);
  if (params?.sortOrder) searchParams.set('sortOrder', params.sortOrder);

  const response = await fetch(`${API_BASE}/documents?${searchParams}`, {
    method: 'GET',
    credentials: 'include',
  });

  const data = await handleResponse<{
    documents: Array<{
      id: string;
      type: string;
      title: string;
      status: string;
      confidence: number;
      companyProfileId?: string;
      requiresHumanReview: boolean;
      createdAt: string;
      updatedAt: string;
    }>;
    total: number;
  }>(response);

  // Transform backend response to frontend format
  const documents: GeneratedDocument[] = data.documents.map((doc) => ({
    id: doc.id,
    type: doc.type as DocumentType,
    title: doc.title,
    companyProfileId: doc.companyProfileId || '',
    status: doc.status as 'draft' | 'approved' | 'rejected',
    confidence: doc.confidence,
    createdAt: new Date(doc.createdAt),
    updatedAt: new Date(doc.updatedAt),
  }));

  const limit = params?.limit || 20;
  const offset = params?.offset || 0;

  return {
    documents,
    total: data.total,
    hasMore: offset + limit < data.total,
  };
}

/**
 * Get a single document by ID
 */
async function getDocument(documentId: string): Promise<FinalOutput | null> {
  if (MOCK_ENABLED) {
    await mockDelay();
    const documents = getMockDocuments();
    const doc = documents.find((d) => d.id === documentId);
    if (!doc) return null;

    // Return a mock FinalOutput based on the document
    return {
      documentId: doc.id,
      content: {
        id: doc.id,
        sections: [
          {
            id: 'sec-1',
            title: 'Executive Summary',
            content: 'This is a placeholder executive summary for the document.',
            confidence: doc.confidence + 5,
            unresolvedCritiques: 0,
          },
          {
            id: 'sec-2',
            title: 'Analysis',
            content: 'Detailed analysis content would appear here.',
            confidence: doc.confidence - 3,
            unresolvedCritiques: 1,
          },
          {
            id: 'sec-3',
            title: 'Recommendations',
            content: 'Strategic recommendations based on the analysis.',
            confidence: doc.confidence,
            unresolvedCritiques: 0,
          },
        ],
        overallConfidence: doc.confidence,
        updatedAt: doc.updatedAt,
      },
      confidence: {
        overall: doc.confidence,
        sections: {
          'sec-1': doc.confidence + 5,
          'sec-2': doc.confidence - 3,
          'sec-3': doc.confidence,
        },
      },
      redTeamReport: {
        entries: [],
        summary: 'Red team analysis completed with moderate challenges addressed.',
      },
      debateLog: [],
      metrics: {
        roundsCompleted: 3,
        totalCritiques: 12,
        criticalCount: 2,
        majorCount: 5,
        minorCount: 5,
        acceptedCount: 8,
        rebuttedCount: 3,
        acknowledgedCount: 1,
        timeElapsedMs: 245000,
      },
      requiresHumanReview: doc.status === 'draft' && doc.confidence < 70,
    };
  }

  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: 'GET',
    credentials: 'include',
  });

  const data = await handleResponse<{
    documentId: string;
    content?: {
      id: string;
      sections: Array<{
        id: string;
        title: string;
        content: string;
        confidence: number;
        unresolvedCritiques: number;
      }>;
      overallConfidence: number;
      updatedAt: string;
    };
    confidence?: {
      overall: number;
      sections: Record<string, number>;
    };
    redTeamReport?: {
      entries: Array<{
        id: string;
        round: number;
        phase: string;
        agentId: string;
        type: string;
        content: string;
        timestamp: string;
      }>;
      summary: string;
    };
    debateLog: Array<{
      id: string;
      round: number;
      phase: string;
      agentId: string;
      type: string;
      content: string;
      timestamp: string;
    }>;
    metrics?: GenerationMetrics;
    requiresHumanReview: boolean;
  }>(response);

  // Transform backend response to frontend format
  return {
    documentId: data.documentId,
    content: data.content ? {
      id: data.content.id,
      sections: data.content.sections,
      overallConfidence: data.content.overallConfidence,
      updatedAt: new Date(data.content.updatedAt),
    } : {
      id: data.documentId,
      sections: [],
      overallConfidence: 0,
      updatedAt: new Date(),
    },
    confidence: data.confidence || { overall: 0, sections: {} },
    redTeamReport: data.redTeamReport ? {
      entries: data.redTeamReport.entries.map((e) => ({
        ...e,
        phase: e.phase as Phase,
        type: e.type as 'critique' | 'response' | 'synthesis',
        timestamp: new Date(e.timestamp),
      })),
      summary: data.redTeamReport.summary,
    } : { entries: [], summary: '' },
    debateLog: data.debateLog.map((e) => ({
      ...e,
      phase: e.phase as Phase,
      type: e.type as 'critique' | 'response' | 'synthesis',
      timestamp: new Date(e.timestamp),
    })),
    metrics: data.metrics || {
      roundsCompleted: 0,
      totalCritiques: 0,
      criticalCount: 0,
      majorCount: 0,
      minorCount: 0,
      acceptedCount: 0,
      rebuttedCount: 0,
      acknowledgedCount: 0,
      timeElapsedMs: 0,
    },
    requiresHumanReview: data.requiresHumanReview,
  };
}

/**
 * Delete a document by ID
 */
async function deleteDocument(documentId: string): Promise<DeleteDocumentResponse> {
  if (MOCK_ENABLED) {
    await mockDelay();
    const documents = getMockDocuments();
    const filtered = documents.filter((d) => d.id !== documentId);
    if (filtered.length === documents.length) {
      throw new DocumentsApiError('Document not found', 'NOT_FOUND', 404);
    }
    saveMockDocuments(filtered);
    return { success: true };
  }

  const response = await fetch(`${API_BASE}/documents/${documentId}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  // Backend returns 204 No Content on success
  if (!response.ok) {
    let error: { code: string; message: string; details?: Record<string, unknown> };
    try {
      error = await response.json();
    } catch {
      error = {
        code: 'UNKNOWN_ERROR',
        message: response.statusText || 'An unknown error occurred',
      };
    }
    throw new DocumentsApiError(
      error.message,
      error.code,
      response.status,
      error.details
    );
  }

  return { success: true };
}

/**
 * Duplicate a document (creates a new draft from an existing document)
 */
async function duplicateDocument(documentId: string): Promise<GeneratedDocument> {
  if (MOCK_ENABLED) {
    await mockDelay(300, 600);
    const documents = getMockDocuments();
    const original = documents.find((d) => d.id === documentId);
    if (!original) {
      throw new DocumentsApiError('Document not found', 'NOT_FOUND', 404);
    }

    const now = new Date();
    const duplicate: GeneratedDocument = {
      ...original,
      id: `doc-${Date.now()}`,
      title: `${original.title} (Copy)`,
      status: 'draft',
      createdAt: now,
      updatedAt: now,
    };

    documents.unshift(duplicate);
    saveMockDocuments(documents);
    return duplicate;
  }

  const response = await fetch(`${API_BASE}/documents/${documentId}/duplicate`, {
    method: 'POST',
    credentials: 'include',
  });

  const data = await handleResponse<{
    id: string;
    type: string;
    title: string;
    status: string;
    confidence: number;
    companyProfileId?: string;
    createdAt: string;
    updatedAt: string;
  }>(response);

  return {
    id: data.id,
    type: data.type as DocumentType,
    title: data.title,
    companyProfileId: data.companyProfileId || '',
    status: data.status as 'draft' | 'approved' | 'rejected',
    confidence: data.confidence,
    createdAt: new Date(data.createdAt),
    updatedAt: new Date(data.updatedAt),
  };
}

/**
 * Update document status (for approving/rejecting after review)
 */
async function updateDocumentStatus(
  documentId: string,
  status: 'approved' | 'rejected',
  notes?: string
): Promise<GeneratedDocument> {
  if (MOCK_ENABLED) {
    await mockDelay();
    const documents = getMockDocuments();
    const index = documents.findIndex((d) => d.id === documentId);
    if (index === -1) {
      throw new DocumentsApiError('Document not found', 'NOT_FOUND', 404);
    }

    documents[index] = {
      ...documents[index],
      status,
      updatedAt: new Date(),
    };
    saveMockDocuments(documents);
    return documents[index];
  }

  const response = await fetch(`${API_BASE}/documents/${documentId}/${status}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ reviewNotes: notes }),
  });

  const data = await handleResponse<{
    id: string;
    type: string;
    title: string;
    status: string;
    confidence: number;
    companyProfileId?: string;
    createdAt: string;
    updatedAt: string;
  }>(response);

  return {
    id: data.id,
    type: data.type as DocumentType,
    title: data.title,
    companyProfileId: data.companyProfileId || '',
    status: data.status as 'draft' | 'approved' | 'rejected',
    confidence: data.confidence,
    createdAt: new Date(data.createdAt),
    updatedAt: new Date(data.updatedAt),
  };
}

/**
 * Export a document in the specified format
 */
async function exportDocument(
  documentId: string,
  format: ExportFormat
): Promise<{ blob?: Blob; url?: string }> {
  if (MOCK_ENABLED) {
    await mockDelay(500, 1000);

    if (format === 'share') {
      return {
        url: `${window.location.origin}/shared/${documentId}?token=${Date.now()}`,
      };
    }

    // Return a mock blob for download formats
    const content = `Mock ${format.toUpperCase()} export for document ${documentId}`;
    const blob = new Blob([content], { type: 'text/plain' });
    return { blob };
  }

  if (format === 'share') {
    const response = await fetch(`${API_BASE}/documents/${documentId}/share`, {
      method: 'POST',
      credentials: 'include',
    });
    const result = await handleResponse<{ url: string }>(response);
    return { url: result.url };
  }

  const response = await fetch(
    `${API_BASE}/documents/${documentId}/export?format=${format}`,
    {
      method: 'GET',
      credentials: 'include',
    }
  );

  if (!response.ok) {
    throw new DocumentsApiError('Export failed', 'EXPORT_ERROR', response.status);
  }

  return { blob: await response.blob() };
}

// ============================================================================
// Export API Object
// ============================================================================

export const documentsApi = {
  list: listDocuments,
  get: getDocument,
  delete: deleteDocument,
  duplicate: duplicateDocument,
  updateStatus: updateDocumentStatus,
  export: exportDocument,
};

export default documentsApi;
