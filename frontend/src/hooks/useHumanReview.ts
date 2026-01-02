/**
 * useHumanReview Hook
 *
 * Manages the state and actions for the human review modal.
 * Integrates with the swarm store and generation API to handle
 * approve, reject, and regenerate actions.
 */

import { useState, useCallback, useMemo } from 'react';
import { useSwarmStore } from '../stores/swarmStore';
import { generationApi, type RegenerationOptions } from '../api/generation';
import type { EscalationInfo, SwarmConfig } from '../types';
import type { RegenerationOption } from '../components/human-review-modal/HumanReviewModal';

export interface UseHumanReviewOptions {
  /** Document ID for API operations */
  documentId?: string;
  /** Callback when approve succeeds */
  onApproveSuccess?: () => void;
  /** Callback when regeneration starts */
  onRegenerateStart?: (requestId: string) => void;
  /** Callback when an error occurs */
  onError?: (error: string) => void;
}

export interface UseHumanReviewReturn {
  /** Whether the review modal should be open */
  isOpen: boolean;
  /** Escalation info from the store */
  escalation: EscalationInfo | null;
  /** Overall confidence score */
  overallConfidence: number;
  /** Whether an action is in progress */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Open the review modal */
  openModal: () => void;
  /** Close the review modal */
  closeModal: () => void;
  /** Approve the document as-is */
  approve: () => Promise<void>;
  /** Regenerate with specified option */
  regenerate: (option: RegenerationOption, newConfig?: Partial<SwarmConfig>) => Promise<void>;
  /** View the full document (closes modal) */
  viewDocument: () => void;
  /** Clear any error */
  clearError: () => void;
}

export function useHumanReview(options: UseHumanReviewOptions = {}): UseHumanReviewReturn {
  const { documentId, onApproveSuccess, onRegenerateStart, onError } = options;

  // Local state
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Store state
  const status = useSwarmStore((s) => s.status);
  const escalation = useSwarmStore((s) => s.escalation);
  const result = useSwarmStore((s) => s.result);
  const drafts = useSwarmStore((s) => s.drafts);
  const setStatus = useSwarmStore((s) => s.setStatus);
  const reset = useSwarmStore((s) => s.reset);

  // Compute overall confidence from latest draft
  const overallConfidence = useMemo(() => {
    if (result?.confidence?.overall !== undefined) {
      return result.confidence.overall;
    }
    const latestDraft = drafts[drafts.length - 1];
    return latestDraft?.overallConfidence ?? 0;
  }, [result, drafts]);

  // Auto-open modal when status becomes 'review'
  const shouldBeOpen = status === 'review' && escalation !== null;

  // Open modal handler
  const openModal = useCallback(() => {
    setIsOpen(true);
    setError(null);
  }, []);

  // Close modal handler
  const closeModal = useCallback(() => {
    setIsOpen(false);
    // If we're in review status, transition to complete to prevent modal from reopening
    if (status === 'review') {
      setStatus('complete');
    }
  }, [status, setStatus]);

  // Approve handler
  const approve = useCallback(async () => {
    if (!documentId && !result?.documentId) {
      setError('No document ID available for approval');
      onError?.('No document ID available for approval');
      return;
    }

    const docId = documentId || result?.documentId || '';

    setIsLoading(true);
    setError(null);

    try {
      await generationApi.approveDocument(docId);
      setStatus('complete');
      setIsOpen(false);
      onApproveSuccess?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to approve document';
      setError(message);
      onError?.(message);
    } finally {
      setIsLoading(false);
    }
  }, [documentId, result, setStatus, onApproveSuccess, onError]);

  // Regenerate handler
  const regenerate = useCallback(
    async (option: RegenerationOption, newConfig?: Partial<SwarmConfig>) => {
      if (!documentId && !result?.documentId) {
        setError('No document ID available for regeneration');
        onError?.('No document ID available for regeneration');
        return;
      }

      const docId = documentId || result?.documentId || '';

      setIsLoading(true);
      setError(null);

      try {
        // Map option to API format
        const apiOptions: RegenerationOptions = {};

        switch (option) {
          case 'same-config':
            apiOptions.retryWithSameConfig = true;
            break;
          case 'higher-rounds':
            apiOptions.retryWithHigherRounds = true;
            break;
          case 'modified-agents':
            if (newConfig) {
              apiOptions.newConfig = newConfig;
            } else {
              // For now, just retry with same config if no new config provided
              apiOptions.retryWithSameConfig = true;
            }
            break;
        }

        const response = await generationApi.regenerateDocument(docId, apiOptions);

        // Reset store and trigger new generation
        reset();
        setIsOpen(false);
        onRegenerateStart?.(response.requestId);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to start regeneration';
        setError(message);
        onError?.(message);
      } finally {
        setIsLoading(false);
      }
    },
    [documentId, result, reset, onRegenerateStart, onError]
  );

  // View document handler
  const viewDocument = useCallback(() => {
    setIsOpen(false);
    // The parent component should handle navigation to document view
  }, []);

  // Clear error handler
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    isOpen: isOpen || shouldBeOpen,
    escalation,
    overallConfidence,
    isLoading,
    error,
    openModal,
    closeModal,
    approve,
    regenerate,
    viewDocument,
    clearError,
  };
}

export default useHumanReview;
