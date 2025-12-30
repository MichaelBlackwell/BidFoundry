/**
 * PhaseHeader Component
 *
 * Displays the current debate phase, round information, and live status indicator.
 * Part of the Debate Theater view (Section 4.3 of Frontend Design Document).
 */

import { memo } from 'react';
import type { Phase } from '../../types';
import './PhaseHeader.css';

export interface PhaseHeaderProps {
  /** Current phase of the debate */
  phase: Phase;
  /** Current round number */
  round: number;
  /** Total number of rounds */
  totalRounds: number;
  /** Whether the debate is currently live/active */
  isLive: boolean;
  /** Optional additional CSS class */
  className?: string;
}

/**
 * Get the display label for a phase
 */
function getPhaseLabel(phase: Phase): string {
  switch (phase) {
    case 'blue-build':
      return 'BLUE TEAM BUILD';
    case 'red-attack':
      return 'RED TEAM ATTACK';
    case 'blue-defense':
      return 'BLUE TEAM DEFENSE';
    case 'synthesis':
      return 'SYNTHESIS';
    default:
      return phase.toUpperCase();
  }
}

/**
 * Get the phase description for screen readers
 */
function getPhaseDescription(phase: Phase): string {
  switch (phase) {
    case 'blue-build':
      return 'Blue team agents are building the initial document';
    case 'red-attack':
      return 'Red team agents are critiquing the document';
    case 'blue-defense':
      return 'Blue team agents are responding to critiques';
    case 'synthesis':
      return 'Arbiter is synthesizing final recommendations';
    default:
      return '';
  }
}

export const PhaseHeader = memo(function PhaseHeader({
  phase,
  round,
  totalRounds,
  isLive,
  className = '',
}: PhaseHeaderProps) {
  const phaseLabel = getPhaseLabel(phase);
  const phaseDescription = getPhaseDescription(phase);

  return (
    <header
      className={`phase-header phase-header--${phase} ${className}`}
      role="banner"
      aria-label="Debate phase information"
    >
      <div className="phase-header__main">
        <div className="phase-header__phase-container">
          <span className="phase-header__phase-indicator" aria-hidden="true">
            {phase === 'blue-build' || phase === 'blue-defense' ? '🔵' : ''}
            {phase === 'red-attack' ? '🔴' : ''}
            {phase === 'synthesis' ? '⚖️' : ''}
          </span>
          <h2 className="phase-header__phase-label">
            PHASE: {phaseLabel}
          </h2>
        </div>
        <span className="visually-hidden">{phaseDescription}</span>
      </div>

      <div className="phase-header__meta">
        {isLive && (
          <div className="phase-header__live-indicator" role="status" aria-live="polite">
            <span className="phase-header__live-dot" aria-hidden="true" />
            <span className="phase-header__live-text">Live</span>
          </div>
        )}

        <div className="phase-header__round" aria-label={`Round ${round} of ${totalRounds}`}>
          <span className="phase-header__round-text">
            Round {round} of {totalRounds}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="phase-header__progress"
        role="progressbar"
        aria-valuenow={round}
        aria-valuemin={1}
        aria-valuemax={totalRounds}
        aria-label="Round progress"
      >
        <div
          className="phase-header__progress-fill"
          style={{ width: `${(round / totalRounds) * 100}%` }}
        />
      </div>
    </header>
  );
});

export default PhaseHeader;
