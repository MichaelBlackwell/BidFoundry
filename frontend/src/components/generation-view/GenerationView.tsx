/**
 * GenerationView Component
 *
 * The combined generation view that displays the Debate Theater and Document Preview
 * side-by-side (or stacked on tablet). This is the main view during document generation.
 *
 * Based on Section 4 and Implementation Chunk F8 of the Frontend Design Document.
 */

import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { DocumentHeader } from './DocumentHeader';
import { ControlPanel } from './ControlPanel';
import { DebateTheater } from '../debate-theater';
import { DocumentPreview } from '../document-preview';
import { HumanReviewModal } from '../human-review-modal';
import { useGenerationView } from '../../hooks/useGenerationView';
import { useHumanReview } from '../../hooks/useHumanReview';
import { useUIStore } from '../../stores/uiStore';
import type { RegenerationOption } from '../human-review-modal';
import './GenerationView.css';

export interface GenerationViewProps {
  /** Request ID for the current generation */
  requestId?: string;
  /** Document ID for human review actions */
  documentId?: string;
  /** Callback when generation completes */
  onComplete?: () => void;
  /** Callback when generation is cancelled */
  onCancel?: () => void;
  /** Callback when section is clicked in preview (to sync with debate) */
  onSectionSelect?: (sectionId: string) => void;
  /** Callback when regeneration is triggered */
  onRegenerate?: (requestId: string) => void;
  /** Callback to navigate to document view */
  onViewDocument?: () => void;
  /** Optional additional CSS class */
  className?: string;
}

export const GenerationView = memo(function GenerationView({
  requestId,
  documentId,
  onComplete,
  onCancel,
  onSectionSelect,
  onRegenerate,
  onViewDocument,
  className = '',
}: GenerationViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [activePane, setActivePane] = useState<'debate' | 'preview'>('debate');

  // Get generation state from hook
  const {
    // State
    status,
    documentTitle,
    documentType,
    currentRound,
    totalRounds,
    currentPhase,
    agents,
    critiques,
    responses,
    draft,
    previousDraft,
    overallConfidence,
    isGenerating,
    error,
    connectionStatus,
    revisingSectionIds,
    // Actions
    pause,
    resume,
    cancel,
    handleExport,
  } = useGenerationView({ requestId });

  // UI state
  const debateTheaterWidth = useUIStore((s) => s.debateTheaterWidth);
  const setDebateTheaterWidth = useUIStore((s) => s.setDebateTheaterWidth);
  const previewExpanded = useUIStore((s) => s.previewExpanded);
  const setPreviewExpanded = useUIStore((s) => s.setPreviewExpanded);

  // Human review state
  const {
    isOpen: isReviewModalOpen,
    escalation,
    overallConfidence: reviewConfidence,
    isLoading: isReviewLoading,
    closeModal: closeReviewModal,
    approve: handleApprove,
    regenerate: handleRegenerateInternal,
    viewDocument: handleViewDocumentInternal,
  } = useHumanReview({
    documentId,
    onApproveSuccess: onComplete,
    onRegenerateStart: onRegenerate,
  });

  // Handle regeneration with proper type
  const handleRegenerate = useCallback(
    (option: RegenerationOption) => {
      handleRegenerateInternal(option);
    },
    [handleRegenerateInternal]
  );

  // Handle view document
  const handleViewDocument = useCallback(() => {
    handleViewDocumentInternal();
    onViewDocument?.();
  }, [handleViewDocumentInternal, onViewDocument]);

  // Handle pause/resume
  const handlePause = useCallback(() => {
    setIsPaused(true);
    pause();
  }, [pause]);

  const handleResume = useCallback(() => {
    setIsPaused(false);
    resume();
  }, [resume]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    cancel();
    onCancel?.();
  }, [cancel, onCancel]);

  // Handle section click - sync with debate theater
  const handleSectionClick = useCallback((sectionId: string) => {
    onSectionSelect?.(sectionId);
    // Could also scroll to relevant debate entry
  }, [onSectionSelect]);

  // Handle preview expand/collapse
  const handleTogglePreview = useCallback(() => {
    setPreviewExpanded(!previewExpanded);
  }, [previewExpanded, setPreviewExpanded]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't capture if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case ' ':
          // Space to pause/resume
          e.preventDefault();
          if (isPaused) {
            handleResume();
          } else if (isGenerating) {
            handlePause();
          }
          break;

        case 'Escape':
          // Escape to cancel or close expanded preview
          if (previewExpanded) {
            setPreviewExpanded(false);
          } else if (isGenerating) {
            // Could show confirmation dialog
            handleCancel();
          }
          break;

        case 'Tab':
          // Tab to switch between panes (if not expanded)
          if (!previewExpanded && !e.shiftKey && !e.ctrlKey && !e.altKey) {
            e.preventDefault();
            setActivePane((prev) => (prev === 'debate' ? 'preview' : 'debate'));
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [
    isPaused,
    isGenerating,
    previewExpanded,
    handlePause,
    handleResume,
    handleCancel,
    setPreviewExpanded,
  ]);

  // Track completion
  useEffect(() => {
    if (status === 'complete' || status === 'review') {
      onComplete?.();
    }
  }, [status, onComplete]);

  // Resizing logic for split panes
  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = debateTheaterWidth;
    const container = containerRef.current;
    if (!container) return;

    const containerWidth = container.offsetWidth;

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaPercent = (deltaX / containerWidth) * 100;
      const newWidth = Math.max(30, Math.min(70, startWidth + deltaPercent));
      setDebateTheaterWidth(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, [debateTheaterWidth, setDebateTheaterWidth]);

  // Error state
  if (error && status === 'error') {
    return (
      <div className={`generation-view generation-view--error ${className}`}>
        <div className="generation-view__error">
          <span className="generation-view__error-icon" aria-hidden="true">
            !
          </span>
          <h2 className="generation-view__error-title">Generation Failed</h2>
          <p className="generation-view__error-message">{error}</p>
          <button
            className="generation-view__error-retry"
            onClick={() => window.location.reload()}
            type="button"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Idle state - shouldn't normally render this
  if (status === 'idle' && !isGenerating) {
    return (
      <div className={`generation-view generation-view--idle ${className}`}>
        <div className="generation-view__idle">
          <p>No active generation. Start a new document to begin.</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`generation-view ${isPaused ? 'generation-view--paused' : ''} ${className}`}
      role="main"
      aria-label="Document Generation"
    >
      {/* Document Header */}
      <DocumentHeader
        title={documentTitle}
        documentType={documentType}
        status={status}
        currentRound={currentRound}
        totalRounds={totalRounds}
        currentPhase={currentPhase}
        overallConfidence={overallConfidence}
        connectionStatus={connectionStatus}
        isLive={isGenerating && !isPaused}
      />

      {/* Main Content Area */}
      <div className="generation-view__content">
        {/* Debate Theater */}
        <div
          className={`generation-view__debate-pane ${activePane === 'debate' ? 'generation-view__pane--active' : ''}`}
          style={{ width: previewExpanded ? '100%' : `${debateTheaterWidth}%` }}
        >
          <DebateTheater
            round={currentRound}
            totalRounds={totalRounds}
            phase={currentPhase}
            agents={agents}
            critiques={critiques}
            responses={responses}
            isLive={isGenerating && !isPaused}
            isPaused={isPaused}
            onPause={handlePause}
            onResume={handleResume}
          />
        </div>

        {/* Resize Handle */}
        {!previewExpanded && (
          <div
            className="generation-view__resize-handle"
            onMouseDown={handleResizeStart}
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize debate theater and preview panes"
            tabIndex={0}
          />
        )}

        {/* Document Preview */}
        {!previewExpanded && (
          <div
            className={`generation-view__preview-pane ${activePane === 'preview' ? 'generation-view__pane--active' : ''}`}
            style={{ width: `${100 - debateTheaterWidth}%` }}
          >
            <DocumentPreview
              draft={draft}
              title={documentTitle}
              critiques={critiques}
              previousDraft={previousDraft}
              revisingSectionIds={revisingSectionIds}
              isGenerating={isGenerating}
              onSectionClick={handleSectionClick}
              onExport={handleExport}
              isExpanded={previewExpanded}
              onToggleExpand={handleTogglePreview}
            />
          </div>
        )}
      </div>

      {/* Control Panel */}
      <ControlPanel
        status={status}
        isPaused={isPaused}
        isGenerating={isGenerating}
        currentRound={currentRound}
        totalRounds={totalRounds}
        onPause={handlePause}
        onResume={handleResume}
        onCancel={handleCancel}
        onExpandPreview={handleTogglePreview}
        previewExpanded={previewExpanded}
      />

      {/* Expanded Preview Overlay */}
      {previewExpanded && (
        <div className="generation-view__preview-overlay">
          <DocumentPreview
            draft={draft}
            title={documentTitle}
            critiques={critiques}
            previousDraft={previousDraft}
            revisingSectionIds={revisingSectionIds}
            isGenerating={isGenerating}
            onSectionClick={handleSectionClick}
            onExport={handleExport}
            isExpanded={previewExpanded}
            onToggleExpand={handleTogglePreview}
          />
        </div>
      )}

      {/* Connection Status Warning */}
      {connectionStatus === 'disconnected' && (
        <div
          className="generation-view__connection-warning"
          role="alert"
          aria-live="polite"
        >
          <span className="generation-view__connection-warning-icon">!</span>
          <span>Connection lost. Attempting to reconnect...</span>
        </div>
      )}

      {/* Keyboard Shortcuts Help */}
      <div className="generation-view__shortcuts-hint" aria-hidden="true">
        <kbd>Space</kbd> Pause/Resume
        <kbd>Tab</kbd> Switch Pane
        <kbd>Esc</kbd> Cancel
      </div>

      {/* Human Review Modal */}
      <HumanReviewModal
        isOpen={isReviewModalOpen}
        onClose={closeReviewModal}
        escalation={escalation}
        overallConfidence={reviewConfidence}
        documentId={documentId}
        onApprove={handleApprove}
        onRegenerate={handleRegenerate}
        onViewDocument={handleViewDocument}
        isLoading={isReviewLoading}
      />
    </div>
  );
});

export default GenerationView;
