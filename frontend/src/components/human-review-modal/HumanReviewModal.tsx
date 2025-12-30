/**
 * HumanReviewModal Component
 *
 * Modal dialog displayed when generation escalation thresholds are triggered
 * and human review is required. Shows escalation reasons, unresolved disputes,
 * and action options for the user.
 *
 * Based on Section 4.6 of the Frontend Design Document.
 */

import { memo, useState, useCallback } from 'react';
import { Modal, ModalFooter } from '../ui/Modal';
import { Button } from '../ui/Button';
import { DisputeCard } from './DisputeCard';
import type { EscalationInfo, SwarmConfig } from '../../types';
import './HumanReviewModal.css';

export type RegenerationOption =
  | 'same-config'
  | 'higher-rounds'
  | 'modified-agents';

export interface HumanReviewModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal is closed */
  onClose: () => void;
  /** Escalation information with reasons and disputes */
  escalation: EscalationInfo | null;
  /** Overall document confidence score (0-100) */
  overallConfidence: number;
  /** Document ID for API actions */
  documentId?: string;
  /** Callback when user approves the document as-is */
  onApprove: () => void;
  /** Callback when user rejects and requests regeneration */
  onRegenerate: (option: RegenerationOption, newConfig?: Partial<SwarmConfig>) => void;
  /** Callback to view the full document */
  onViewDocument: () => void;
  /** Whether an action is currently in progress */
  isLoading?: boolean;
}

export const HumanReviewModal = memo(function HumanReviewModal({
  isOpen,
  onClose,
  escalation,
  overallConfidence,
  documentId: _documentId,
  onApprove,
  onRegenerate,
  onViewDocument,
  isLoading = false,
}: HumanReviewModalProps) {
  // Note: documentId is passed for API context but actions are handled by parent via callbacks
  void _documentId;
  const [selectedOption, setSelectedOption] = useState<RegenerationOption>('same-config');
  const [showRegenerateOptions, setShowRegenerateOptions] = useState(false);

  // Handle approve action
  const handleApprove = useCallback(() => {
    onApprove();
  }, [onApprove]);

  // Handle regenerate action
  const handleRegenerate = useCallback(() => {
    onRegenerate(selectedOption);
  }, [onRegenerate, selectedOption]);

  // Toggle regeneration options visibility
  const handleShowRegenerateOptions = useCallback(() => {
    setShowRegenerateOptions(true);
  }, []);

  // Handle back from regeneration options
  const handleBackToActions = useCallback(() => {
    setShowRegenerateOptions(false);
  }, []);

  // Format confidence as percentage
  const confidencePercent = Math.round(overallConfidence);
  const confidenceColor =
    confidencePercent >= 80
      ? 'var(--color-success)'
      : confidencePercent >= 60
        ? 'var(--color-warning)'
        : 'var(--color-error)';

  if (!escalation) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Human Review Required"
      size="lg"
    >
      <div className="human-review-modal">
        {/* Warning Icon and Summary */}
        <div className="human-review-modal__summary">
          <span className="human-review-modal__warning-icon" aria-hidden="true">
            &#x26A0;&#xFE0F;
          </span>
          <div className="human-review-modal__summary-text">
            <p className="human-review-modal__summary-message">
              The swarm was unable to reach consensus on this document.
            </p>
            <p className="human-review-modal__confidence">
              Overall confidence:{' '}
              <span
                className="human-review-modal__confidence-value"
                style={{ color: confidenceColor }}
              >
                {confidencePercent}%
              </span>
            </p>
          </div>
        </div>

        {/* Escalation Triggers */}
        <div className="human-review-modal__triggers">
          <h3 className="human-review-modal__section-title">Escalation Triggers:</h3>
          <ul className="human-review-modal__trigger-list">
            {escalation.reasons.map((reason, index) => (
              <li key={index} className="human-review-modal__trigger-item">
                <span className="human-review-modal__trigger-bullet" aria-hidden="true">
                  &#x2022;
                </span>
                {reason}
              </li>
            ))}
          </ul>
        </div>

        <hr className="human-review-modal__divider" />

        {/* Unresolved Disputes */}
        {!showRegenerateOptions && (
          <div className="human-review-modal__disputes">
            <h3 className="human-review-modal__section-title">Unresolved Disputes:</h3>
            <div className="human-review-modal__dispute-list">
              {escalation.disputes.map((dispute, index) => (
                <DisputeCard
                  key={dispute.id}
                  dispute={dispute}
                  number={index + 1}
                />
              ))}
            </div>
          </div>
        )}

        {/* Regeneration Options */}
        {showRegenerateOptions && (
          <div className="human-review-modal__regenerate-options">
            <h3 className="human-review-modal__section-title">Regeneration Options:</h3>
            <div className="human-review-modal__option-list">
              <label className="human-review-modal__option">
                <input
                  type="radio"
                  name="regenerate-option"
                  value="same-config"
                  checked={selectedOption === 'same-config'}
                  onChange={() => setSelectedOption('same-config')}
                  className="human-review-modal__option-radio"
                />
                <div className="human-review-modal__option-content">
                  <span className="human-review-modal__option-label">
                    Retry with same configuration
                  </span>
                  <span className="human-review-modal__option-desc">
                    Run the generation again with identical settings
                  </span>
                </div>
              </label>

              <label className="human-review-modal__option">
                <input
                  type="radio"
                  name="regenerate-option"
                  value="higher-rounds"
                  checked={selectedOption === 'higher-rounds'}
                  onChange={() => setSelectedOption('higher-rounds')}
                  className="human-review-modal__option-radio"
                />
                <div className="human-review-modal__option-content">
                  <span className="human-review-modal__option-label">
                    Retry with higher adversarial rounds
                  </span>
                  <span className="human-review-modal__option-desc">
                    Increase debate rounds for more thorough analysis
                  </span>
                </div>
              </label>

              <label className="human-review-modal__option">
                <input
                  type="radio"
                  name="regenerate-option"
                  value="modified-agents"
                  checked={selectedOption === 'modified-agents'}
                  onChange={() => setSelectedOption('modified-agents')}
                  className="human-review-modal__option-radio"
                />
                <div className="human-review-modal__option-content">
                  <span className="human-review-modal__option-label">
                    Retry with modified agent selection
                  </span>
                  <span className="human-review-modal__option-desc">
                    Adjust which agents participate in the debate
                  </span>
                </div>
              </label>
            </div>
          </div>
        )}
      </div>

      <ModalFooter>
        {!showRegenerateOptions ? (
          <>
            <Button
              variant="secondary"
              onClick={onViewDocument}
              disabled={isLoading}
            >
              View Full Document
            </Button>
            <Button
              variant="danger"
              onClick={handleShowRegenerateOptions}
              disabled={isLoading}
            >
              Reject & Regenerate
            </Button>
            <Button
              variant="primary"
              onClick={handleApprove}
              loading={isLoading}
            >
              Approve as-is
            </Button>
          </>
        ) : (
          <>
            <Button
              variant="ghost"
              onClick={handleBackToActions}
              disabled={isLoading}
            >
              Back
            </Button>
            <Button
              variant="primary"
              onClick={handleRegenerate}
              loading={isLoading}
            >
              Regenerate
            </Button>
          </>
        )}
      </ModalFooter>
    </Modal>
  );
});

export default HumanReviewModal;
