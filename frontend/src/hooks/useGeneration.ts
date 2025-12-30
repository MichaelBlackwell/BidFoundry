/**
 * useGeneration Hook
 *
 * High-level hook for managing document generation workflow.
 * Combines REST API calls with WebSocket real-time updates.
 *
 * Features:
 * - Start generation via REST, track via WebSocket
 * - Pause/resume/cancel generation
 * - Handle human review workflow
 * - Export completed documents
 */

import { useCallback, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSwarmStore } from '../stores/swarmStore';
import { useSwarmWebSocket } from './useSwarmWebSocket';
import {
  generationApi,
  type GenerationStartResponse,
  type RegenerationOptions,
  GenerationApiError,
} from '../api/generation';
import type { DocumentRequest, FinalOutput, GenerationStatus, Phase, AgentRuntimeState, EscalationInfo, ExportFormat } from '../types';
import type { ConnectionStatus } from '../types/websocket';

// ============================================================================
// Types
// ============================================================================

export interface UseGenerationOptions {
  /** Auto-navigate to generation view on start */
  autoNavigate?: boolean;
  /** Callback when generation starts */
  onStart?: (requestId: string) => void;
  /** Callback when generation completes */
  onComplete?: (result: FinalOutput) => void;
  /** Callback when generation errors */
  onError?: (error: Error) => void;
  /** Callback when escalation is triggered */
  onEscalation?: () => void;
}

export interface UseGenerationReturn {
  // State
  /** Current generation status */
  status: GenerationStatus;
  /** Whether generation is currently running */
  isGenerating: boolean;
  /** Current request ID */
  requestId: string | null;
  /** Current round number */
  currentRound: number;
  /** Total rounds */
  totalRounds: number;
  /** Current phase */
  currentPhase: Phase;
  /** Active agents */
  agents: Record<string, AgentRuntimeState>;
  /** Generation result */
  result: FinalOutput | null;
  /** Escalation info if triggered */
  escalation: EscalationInfo | null;
  /** Error message if any */
  error: string | null;
  /** Connection status */
  connectionStatus: ConnectionStatus;

  // Actions
  /** Start a new generation */
  startGeneration: (request: DocumentRequest) => Promise<string>;
  /** Pause the current generation */
  pauseGeneration: () => void;
  /** Resume a paused generation */
  resumeGeneration: () => void;
  /** Cancel the current generation */
  cancelGeneration: () => void;
  /** Approve a document after review */
  approveDocument: (notes?: string) => Promise<void>;
  /** Reject a document after review */
  rejectDocument: (reason?: string) => Promise<void>;
  /** Regenerate a document */
  regenerateDocument: (options: RegenerationOptions) => Promise<string>;
  /** Export a document */
  exportDocument: (format: ExportFormat) => Promise<Blob | null>;
  /** Reset to initial state */
  reset: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useGeneration(
  options: UseGenerationOptions = {}
): UseGenerationReturn {
  const { onStart, onComplete, onError, onEscalation } = options;

  const queryClient = useQueryClient();
  const [requestId, setRequestId] = useState<string | null>(null);

  // Get state from swarm store
  const status = useSwarmStore((s) => s.status);
  const currentRound = useSwarmStore((s) => s.currentRound);
  const totalRounds = useSwarmStore((s) => s.totalRounds);
  const currentPhase = useSwarmStore((s) => s.currentPhase);
  const agents = useSwarmStore((s) => s.agents);
  const result = useSwarmStore((s) => s.result);
  const escalation = useSwarmStore((s) => s.escalation);
  const storeError = useSwarmStore((s) => s.error);
  const storeReset = useSwarmStore((s) => s.reset);
  const startStoreGeneration = useSwarmStore((s) => s.startGeneration);
  const setStatus = useSwarmStore((s) => s.setStatus);

  // WebSocket integration
  const {
    startGeneration: wsStartGeneration,
    pauseGeneration,
    resumeGeneration,
    cancelGeneration: wsCancelGeneration,
    connectionStatus,
    isGenerating,
  } = useSwarmWebSocket({
    requestId: requestId ?? undefined,
    onComplete: (finalResult) => {
      onComplete?.(finalResult);
      // Invalidate document queries
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error) => {
      onError?.(new Error(error.error));
    },
    onEscalation: () => {
      onEscalation?.();
    },
  });

  // ============================================================================
  // Mutations
  // ============================================================================

  // Start generation mutation
  const startMutation = useMutation({
    mutationFn: async (request: DocumentRequest) => {
      return generationApi.startGeneration(request);
    },
    onSuccess: (data: GenerationStartResponse, request: DocumentRequest) => {
      setRequestId(data.requestId);
      startStoreGeneration(request);
      wsStartGeneration(data.requestId, request.config);
      onStart?.(data.requestId);
    },
    onError: (error: Error) => {
      onError?.(error);
    },
  });

  // Approve document mutation
  const approveMutation = useMutation({
    mutationFn: async ({ documentId, notes }: { documentId: string; notes?: string }) => {
      return generationApi.approveDocument(documentId, notes);
    },
    onSuccess: () => {
      setStatus('complete');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Reject document mutation
  const rejectMutation = useMutation({
    mutationFn: async ({ documentId, reason }: { documentId: string; reason?: string }) => {
      return generationApi.rejectDocument(documentId, reason);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Regenerate document mutation
  const regenerateMutation = useMutation({
    mutationFn: async ({
      documentId,
      options,
    }: {
      documentId: string;
      options: RegenerationOptions;
    }) => {
      return generationApi.regenerateDocument(documentId, options);
    },
    onSuccess: (data: GenerationStartResponse) => {
      setRequestId(data.requestId);
      setStatus('running');
      onStart?.(data.requestId);
    },
  });

  // ============================================================================
  // Actions
  // ============================================================================

  const startGeneration = useCallback(
    async (request: DocumentRequest): Promise<string> => {
      const response = await startMutation.mutateAsync(request);
      return response.requestId;
    },
    [startMutation]
  );

  const cancelGeneration = useCallback(() => {
    wsCancelGeneration();
    storeReset();
    setRequestId(null);
  }, [wsCancelGeneration, storeReset]);

  const approveDocument = useCallback(
    async (notes?: string): Promise<void> => {
      if (!result?.documentId) {
        throw new Error('No document to approve');
      }
      await approveMutation.mutateAsync({
        documentId: result.documentId,
        notes,
      });
    },
    [result?.documentId, approveMutation]
  );

  const rejectDocument = useCallback(
    async (reason?: string): Promise<void> => {
      if (!result?.documentId) {
        throw new Error('No document to reject');
      }
      await rejectMutation.mutateAsync({
        documentId: result.documentId,
        reason,
      });
    },
    [result?.documentId, rejectMutation]
  );

  const regenerateDocument = useCallback(
    async (regenerateOptions: RegenerationOptions): Promise<string> => {
      if (!result?.documentId) {
        throw new Error('No document to regenerate');
      }
      const response = await regenerateMutation.mutateAsync({
        documentId: result.documentId,
        options: regenerateOptions,
      });
      return response.requestId;
    },
    [result?.documentId, regenerateMutation]
  );

  const exportDocument = useCallback(
    async (format: ExportFormat): Promise<Blob | null> => {
      if (!result?.documentId) {
        throw new Error('No document to export');
      }
      const exportResult = await generationApi.exportDocument(result.documentId, format);
      return exportResult.blob ?? null;
    },
    [result?.documentId]
  );

  const reset = useCallback(() => {
    storeReset();
    setRequestId(null);
  }, [storeReset]);

  // ============================================================================
  // Computed State
  // ============================================================================

  const error = useMemo(() => {
    if (storeError) return storeError;
    if (startMutation.error instanceof GenerationApiError) {
      return startMutation.error.message;
    }
    if (startMutation.error) return 'Failed to start generation';
    return null;
  }, [storeError, startMutation.error]);

  return {
    // State
    status,
    isGenerating,
    requestId,
    currentRound,
    totalRounds,
    currentPhase,
    agents,
    result,
    escalation,
    error,
    connectionStatus,

    // Actions
    startGeneration,
    pauseGeneration,
    resumeGeneration,
    cancelGeneration,
    approveDocument,
    rejectDocument,
    regenerateDocument,
    exportDocument,
    reset,
  };
}

// ============================================================================
// Additional Hooks
// ============================================================================

/**
 * Hook to fetch a specific document
 */
export function useDocument(documentId: string | undefined) {
  return useQuery({
    queryKey: ['documents', documentId],
    queryFn: () =>
      documentId ? generationApi.getDocument(documentId) : Promise.reject(),
    enabled: !!documentId,
  });
}

/**
 * Hook to list documents with filtering
 */
export function useDocuments(options?: {
  limit?: number;
  offset?: number;
  status?: 'draft' | 'approved' | 'rejected';
  type?: string;
}) {
  return useQuery({
    queryKey: ['documents', 'list', options],
    queryFn: () => generationApi.listDocuments(options),
  });
}

/**
 * Hook for document export functionality
 */
export function useDocumentExport(documentId: string | undefined) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const exportAs = useCallback(
    async (format: ExportFormat): Promise<void> => {
      if (!documentId) {
        setExportError('No document to export');
        return;
      }

      setIsExporting(true);
      setExportError(null);

      try {
        const exportResult = await generationApi.exportDocument(documentId, format);

        // Handle share link format
        if (format === 'share' && exportResult.url) {
          await navigator.clipboard.writeText(exportResult.url);
          return;
        }

        // Create download link for file exports
        if (exportResult.blob) {
          const url = window.URL.createObjectURL(exportResult.blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `document.${format === 'word' ? 'docx' : format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }
      } catch (err) {
        setExportError(err instanceof Error ? err.message : 'Export failed');
      } finally {
        setIsExporting(false);
      }
    },
    [documentId]
  );

  return {
    exportAs,
    isExporting,
    exportError,
  };
}
