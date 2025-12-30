/**
 * DocumentHeader Component
 *
 * Displays document information, status, round progress, and confidence
 * at the top of the generation view.
 *
 * Based on Section 5.1 Component Hierarchy from the Frontend Design Document.
 */

import { memo } from 'react';
import { ConfidenceMeter } from '../document-preview/ConfidenceMeter';
import type { GenerationStatus, Phase, DocumentType } from '../../types';
import type { ConnectionStatus } from '../../types/websocket';
import './DocumentHeader.css';

export interface DocumentHeaderProps {
  /** Document title */
  title: string;
  /** Document type */
  documentType?: DocumentType;
  /** Current generation status */
  status: GenerationStatus;
  /** Current round number (1-indexed) */
  currentRound: number;
  /** Total number of rounds */
  totalRounds: number;
  /** Current phase of the debate */
  currentPhase: Phase;
  /** Overall document confidence (0-100) */
  overallConfidence: number;
  /** WebSocket connection status */
  connectionStatus: ConnectionStatus;
  /** Whether generation is actively running */
  isLive: boolean;
  /** Optional additional CSS class */
  className?: string;
}

const PHASE_LABELS: Record<Phase, string> = {
  'blue-build': 'Blue Team Building',
  'red-attack': 'Red Team Attack',
  'blue-defense': 'Blue Team Defense',
  'synthesis': 'Synthesis',
};

const STATUS_LABELS: Record<GenerationStatus, string> = {
  idle: 'Ready',
  configuring: 'Configuring',
  running: 'Generating',
  review: 'Needs Review',
  complete: 'Complete',
  error: 'Error',
};

const STATUS_COLORS: Record<GenerationStatus, string> = {
  idle: 'neutral',
  configuring: 'info',
  running: 'success',
  review: 'warning',
  complete: 'success',
  error: 'error',
};

export const DocumentHeader = memo(function DocumentHeader({
  title,
  documentType,
  status,
  currentRound,
  totalRounds,
  currentPhase,
  overallConfidence,
  connectionStatus,
  isLive,
  className = '',
}: DocumentHeaderProps) {
  const roundProgress = totalRounds > 0
    ? Math.round((currentRound / totalRounds) * 100)
    : 0;

  return (
    <header className={`document-header ${className}`} role="banner">
      {/* Left Section: Title and Type */}
      <div className="document-header__left">
        <h1 className="document-header__title">{title}</h1>
        {documentType && (
          <span className="document-header__type">
            {formatDocumentType(documentType)}
          </span>
        )}
      </div>

      {/* Center Section: Status and Progress */}
      <div className="document-header__center">
        {/* Status Badge */}
        <div
          className={`document-header__status document-header__status--${STATUS_COLORS[status]}`}
          role="status"
          aria-live="polite"
        >
          {isLive && (
            <span
              className="document-header__status-dot"
              aria-hidden="true"
            />
          )}
          <span>{STATUS_LABELS[status]}</span>
        </div>

        {/* Round Indicator */}
        {(status === 'running' || status === 'review') && (
          <div className="document-header__round" aria-label={`Round ${currentRound} of ${totalRounds}`}>
            <span className="document-header__round-label">Round</span>
            <span className="document-header__round-value">
              {currentRound}
              <span className="document-header__round-separator">/</span>
              {totalRounds}
            </span>
            <div
              className="document-header__round-progress"
              role="progressbar"
              aria-valuenow={roundProgress}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="document-header__round-progress-bar"
                style={{ width: `${roundProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Phase Indicator */}
        {status === 'running' && (
          <div
            className={`document-header__phase document-header__phase--${getPhaseCategory(currentPhase)}`}
            aria-label={`Current phase: ${PHASE_LABELS[currentPhase]}`}
          >
            <span className="document-header__phase-icon" aria-hidden="true">
              {getPhaseIcon(currentPhase)}
            </span>
            <span className="document-header__phase-label">
              {PHASE_LABELS[currentPhase]}
            </span>
          </div>
        )}
      </div>

      {/* Right Section: Confidence */}
      <div className="document-header__right">
        <div className="document-header__confidence">
          <span className="document-header__confidence-label">Confidence</span>
          <ConfidenceMeter
            confidence={overallConfidence}
            size="sm"
            showLabel={false}
          />
          <span className="document-header__confidence-value">
            {overallConfidence}%
          </span>
        </div>

        {/* Connection Status */}
        <div
          className={`document-header__connection document-header__connection--${connectionStatus}`}
          title={`Connection: ${connectionStatus}`}
          aria-label={`Connection status: ${connectionStatus}`}
        >
          <span className="document-header__connection-icon" aria-hidden="true">
            {getConnectionIcon(connectionStatus)}
          </span>
        </div>
      </div>
    </header>
  );
});

/**
 * Format document type for display
 */
function formatDocumentType(type: DocumentType): string {
  const typeLabels: Record<DocumentType, string> = {
    'capability-statement': 'Capability Statement',
    'swot-analysis': 'SWOT Analysis',
    'competitive-analysis': 'Competitive Analysis',
    'bd-pipeline-plan': 'BD Pipeline Plan',
    'proposal-strategy': 'Proposal Strategy',
    'go-to-market-strategy': 'Go-to-Market Strategy',
    'teaming-strategy': 'Teaming Strategy',
  };
  return typeLabels[type] || type;
}

/**
 * Get the category (color scheme) for a phase
 */
function getPhaseCategory(phase: Phase): 'blue' | 'red' | 'gold' {
  switch (phase) {
    case 'blue-build':
    case 'blue-defense':
      return 'blue';
    case 'red-attack':
      return 'red';
    case 'synthesis':
      return 'gold';
  }
}

/**
 * Get icon for a phase
 */
function getPhaseIcon(phase: Phase): string {
  switch (phase) {
    case 'blue-build':
      return '\u{1F528}'; // Hammer
    case 'red-attack':
      return '\u{2694}'; // Crossed swords
    case 'blue-defense':
      return '\u{1F6E1}'; // Shield
    case 'synthesis':
      return '\u{2696}'; // Balance scale
  }
}

/**
 * Get icon for connection status
 */
function getConnectionIcon(status: ConnectionStatus): string {
  switch (status) {
    case 'connected':
      return '\u{1F7E2}'; // Green circle
    case 'connecting':
    case 'reconnecting':
      return '\u{1F7E1}'; // Yellow circle
    case 'disconnected':
    case 'error':
      return '\u{1F534}'; // Red circle
    default:
      return '\u{26AA}'; // White circle
  }
}

export default DocumentHeader;
