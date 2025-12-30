/**
 * ControlPanel Component
 *
 * Provides controls for pausing, resuming, skipping rounds, and canceling
 * document generation. Also includes quick actions like expanding the preview.
 *
 * Based on Section 5.1 Component Hierarchy from the Frontend Design Document.
 */

import { memo, useCallback, useState } from 'react';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { useUIStore } from '../../stores/uiStore';
import type { GenerationStatus } from '../../types';
import './ControlPanel.css';

export interface ControlPanelProps {
  /** Current generation status */
  status: GenerationStatus;
  /** Whether generation is paused */
  isPaused: boolean;
  /** Whether generation is actively running */
  isGenerating: boolean;
  /** Current round number */
  currentRound: number;
  /** Total rounds */
  totalRounds: number;
  /** Callback when pause is requested */
  onPause: () => void;
  /** Callback when resume is requested */
  onResume: () => void;
  /** Callback when cancel is requested */
  onCancel: () => void;
  /** Callback when skip round is requested (optional) */
  onSkipRound?: () => void;
  /** Callback to expand/collapse preview */
  onExpandPreview: () => void;
  /** Whether preview is expanded */
  previewExpanded: boolean;
  /** Optional additional CSS class */
  className?: string;
}

export const ControlPanel = memo(function ControlPanel({
  status,
  isPaused,
  isGenerating,
  currentRound,
  totalRounds,
  onPause,
  onResume,
  onCancel,
  onSkipRound,
  onExpandPreview,
  previewExpanded,
  className = '',
}: ControlPanelProps) {
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const autoScrollEnabled = useUIStore((s) => s.autoScrollEnabled);
  const toggleAutoScroll = useUIStore((s) => s.toggleAutoScroll);

  // Handle cancel with confirmation
  const handleCancelClick = useCallback(() => {
    setShowCancelConfirm(true);
  }, []);

  const handleCancelConfirm = useCallback(() => {
    setShowCancelConfirm(false);
    onCancel();
  }, [onCancel]);

  const handleCancelDismiss = useCallback(() => {
    setShowCancelConfirm(false);
  }, []);

  // Don't show controls if not generating
  if (status === 'idle' || status === 'complete' || status === 'error') {
    return null;
  }

  return (
    <>
      <div className={`control-panel ${className}`} role="toolbar" aria-label="Generation controls">
        {/* Left: Primary Actions */}
        <div className="control-panel__primary">
          {/* Pause/Resume Button */}
          {isGenerating && !isPaused && (
            <Button
              variant="secondary"
              size="sm"
              onClick={onPause}
              aria-label="Pause generation"
              className="control-panel__btn control-panel__btn--pause"
            >
              <span className="control-panel__btn-icon" aria-hidden="true">
                {'\u23F8'}
              </span>
              <span className="control-panel__btn-label">Pause</span>
            </Button>
          )}

          {isPaused && (
            <Button
              variant="primary"
              size="sm"
              onClick={onResume}
              aria-label="Resume generation"
              className="control-panel__btn control-panel__btn--resume"
            >
              <span className="control-panel__btn-icon" aria-hidden="true">
                {'\u25B6'}
              </span>
              <span className="control-panel__btn-label">Resume</span>
            </Button>
          )}

          {/* Skip Round Button (if supported) */}
          {onSkipRound && isGenerating && currentRound < totalRounds && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onSkipRound}
              aria-label="Skip to next round"
              className="control-panel__btn control-panel__btn--skip"
            >
              <span className="control-panel__btn-icon" aria-hidden="true">
                {'\u23ED'}
              </span>
              <span className="control-panel__btn-label">Skip Round</span>
            </Button>
          )}

          {/* Cancel Button */}
          {(isGenerating || status === 'review') && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCancelClick}
              aria-label="Cancel generation"
              className="control-panel__btn control-panel__btn--cancel"
            >
              <span className="control-panel__btn-icon" aria-hidden="true">
                {'\u2715'}
              </span>
              <span className="control-panel__btn-label">Cancel</span>
            </Button>
          )}

          {/* Auto-scroll Toggle */}
          {isGenerating && (
            <Button
              variant={autoScrollEnabled ? 'secondary' : 'ghost'}
              size="sm"
              onClick={toggleAutoScroll}
              aria-label={autoScrollEnabled ? 'Disable auto-scroll' : 'Enable auto-scroll'}
              aria-pressed={autoScrollEnabled}
              className={`control-panel__btn control-panel__btn--autoscroll ${autoScrollEnabled ? 'control-panel__btn--autoscroll-active' : ''}`}
            >
              <span className="control-panel__btn-icon" aria-hidden="true">
                {autoScrollEnabled ? '\u2B07' : '\u23F8'}
              </span>
              <span className="control-panel__btn-label">Auto-scroll</span>
            </Button>
          )}
        </div>

        {/* Center: Progress Info */}
        <div className="control-panel__info">
          {isGenerating && (
            <span className="control-panel__progress">
              {isPaused ? (
                <span className="control-panel__progress-paused">Paused</span>
              ) : (
                <>
                  <span className="control-panel__progress-dot" aria-hidden="true" />
                  <span>Processing round {currentRound} of {totalRounds}...</span>
                </>
              )}
            </span>
          )}
          {status === 'review' && (
            <span className="control-panel__review-notice">
              <span className="control-panel__review-icon" aria-hidden="true">
                {'\u26A0'}
              </span>
              Human review required
            </span>
          )}
        </div>

        {/* Right: View Actions */}
        <div className="control-panel__secondary">
          {/* Expand/Collapse Preview */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onExpandPreview}
            aria-label={previewExpanded ? 'Collapse preview' : 'Expand preview'}
            aria-pressed={previewExpanded}
            className="control-panel__btn control-panel__btn--expand"
          >
            <span className="control-panel__btn-icon" aria-hidden="true">
              {previewExpanded ? '\u2716' : '\u26F6'}
            </span>
            <span className="control-panel__btn-label">
              {previewExpanded ? 'Close' : 'Expand'}
            </span>
          </Button>

          {/* Keyboard shortcuts hint */}
          <div className="control-panel__shortcuts" aria-hidden="true">
            <kbd>Space</kbd>
            <span>pause</span>
          </div>
        </div>
      </div>

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={showCancelConfirm}
        onClose={handleCancelDismiss}
        title="Cancel Generation?"
        size="sm"
      >
        <div className="control-panel__cancel-modal">
          <p className="control-panel__cancel-message">
            Are you sure you want to cancel? All progress will be lost and you'll
            need to start a new generation.
          </p>
          <div className="control-panel__cancel-actions">
            <Button variant="secondary" onClick={handleCancelDismiss}>
              Keep Generating
            </Button>
            <Button variant="danger" onClick={handleCancelConfirm}>
              Yes, Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
});

export default ControlPanel;
