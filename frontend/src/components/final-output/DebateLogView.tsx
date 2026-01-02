/**
 * DebateLogView Component
 *
 * Displays a chronological log of the entire debate process,
 * organized by round and phase. Allows users to navigate through
 * the debate history.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useMemo, useState, useCallback, useEffect } from 'react';
import type { DebateEntry, Phase } from '../../types';
import './DebateLogView.css';

export interface DebateLogViewProps {
  /** All debate entries */
  entries: DebateEntry[];
  /** Total number of rounds */
  totalRounds: number;
  /** Callback when an entry is clicked */
  onEntryClick?: (entryId: string) => void;
  /** Optional additional CSS class */
  className?: string;
}

const PHASE_LABELS: Record<Phase, string> = {
  'blue-build': 'Blue Team Build',
  'red-attack': 'Red Team Attack',
  'blue-defense': 'Blue Team Defense',
  'synthesis': 'Synthesis',
};

const PHASE_ICONS: Record<Phase, string> = {
  'blue-build': '🔵',
  'red-attack': '🔴',
  'blue-defense': '🔵',
  'synthesis': '⚖️',
};

// Type icons for different entry types
const TYPE_ICONS: Record<string, string> = {
  'critique': '⚔️',
  'response': '🛡️',
  'draft': '📝',
  'orchestrator': '🎯',
  'round-marker': '🔔',
  'synthesis': '📋',
};

// Type labels for display
const TYPE_LABELS: Record<string, string> = {
  'critique': 'CRITIQUE',
  'response': 'RESPONSE',
  'draft': 'DRAFT',
  'orchestrator': 'ORCHESTRATOR',
  'round-marker': 'ROUND',
  'synthesis': 'SYNTHESIS',
};

interface RoundData {
  round: number;
  phases: {
    phase: Phase;
    entries: DebateEntry[];
  }[];
}

function formatTime(date: Date): string {
  return new Date(date).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export const DebateLogView = memo(function DebateLogView({
  entries,
  totalRounds,
  onEntryClick,
  className = '',
}: DebateLogViewProps) {
  const [currentRound, setCurrentRound] = useState<number>(1);
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  // Group entries by round and phase
  const roundsData = useMemo<RoundData[]>(() => {
    const rounds: RoundData[] = [];

    for (let round = 1; round <= totalRounds; round++) {
      const roundEntries = entries.filter((e) => e.round === round);
      const phases: RoundData['phases'] = [];

      // Group by phase in order
      // Skip blue-defense phase for round 1 (no critiques to respond to yet)
      const phaseOrder: Phase[] = ['blue-build', 'red-attack', 'blue-defense', 'synthesis'];
      phaseOrder.forEach((phase) => {
        if (phase === 'blue-defense' && round === 1) {
          return; // Skip blue-defense in round 1
        }
        const phaseEntries = roundEntries.filter((e) => e.phase === phase);
        if (phaseEntries.length > 0) {
          phases.push({ phase, entries: phaseEntries });
        }
      });

      if (phases.length > 0) {
        rounds.push({ round, phases });
      }
    }

    return rounds;
  }, [entries, totalRounds]);

  // Keyboard navigation for rounds
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === '[') {
        e.preventDefault();
        setCurrentRound((prev) => Math.max(1, prev - 1));
      } else if (e.key === ']') {
        e.preventDefault();
        setCurrentRound((prev) => Math.min(totalRounds, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [totalRounds]);

  const togglePhase = useCallback((phaseKey: string) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(phaseKey)) {
        next.delete(phaseKey);
      } else {
        next.add(phaseKey);
      }
      return next;
    });
  }, []);

  const handleEntryClick = (entryId: string) => () => {
    onEntryClick?.(entryId);
  };

  const handleEntryKeyDown = (entryId: string) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onEntryClick?.(entryId);
    }
  };

  const currentRoundData = roundsData.find((r) => r.round === currentRound);

  return (
    <div className={`debate-log ${className}`}>
      {/* Round Navigation */}
      <div className="debate-log__nav">
        <button
          className="debate-log__nav-btn"
          onClick={() => setCurrentRound((prev) => Math.max(1, prev - 1))}
          disabled={currentRound <= 1}
          aria-label="Previous round"
          type="button"
        >
          <span aria-hidden="true">&larr;</span>
        </button>

        <div className="debate-log__nav-rounds">
          {roundsData.map((rd) => (
            <button
              key={rd.round}
              className={`debate-log__round-btn ${rd.round === currentRound ? 'debate-log__round-btn--active' : ''}`}
              onClick={() => setCurrentRound(rd.round)}
              type="button"
            >
              Round {rd.round}
            </button>
          ))}
        </div>

        <button
          className="debate-log__nav-btn"
          onClick={() => setCurrentRound((prev) => Math.min(totalRounds, prev + 1))}
          disabled={currentRound >= totalRounds}
          aria-label="Next round"
          type="button"
        >
          <span aria-hidden="true">&rarr;</span>
        </button>
      </div>

      {/* Keyboard Hint */}
      <div className="debate-log__hint" aria-hidden="true">
        <kbd>[</kbd> / <kbd>]</kbd> to navigate rounds
      </div>

      {/* Round Content */}
      <div className="debate-log__content">
        {currentRoundData ? (
          <div className="debate-log__round">
            <h3 className="debate-log__round-title">
              Round {currentRound} of {totalRounds}
            </h3>

            {currentRoundData.phases.map((phaseData) => {
              const phaseKey = `${currentRound}-${phaseData.phase}`;
              const isExpanded = expandedPhases.has(phaseKey);

              return (
                <div
                  key={phaseKey}
                  className={`debate-log__phase debate-log__phase--${phaseData.phase}`}
                >
                  <button
                    className="debate-log__phase-header"
                    onClick={() => togglePhase(phaseKey)}
                    aria-expanded={isExpanded}
                    type="button"
                  >
                    <span className="debate-log__phase-icon" aria-hidden="true">
                      {PHASE_ICONS[phaseData.phase]}
                    </span>
                    <span className="debate-log__phase-label">
                      {PHASE_LABELS[phaseData.phase]}
                    </span>
                    <span className="debate-log__phase-count">
                      ({phaseData.entries.length} entries)
                    </span>
                    <span
                      className={`debate-log__phase-toggle ${isExpanded ? 'debate-log__phase-toggle--expanded' : ''}`}
                      aria-hidden="true"
                    >
                      ▼
                    </span>
                  </button>

                  {isExpanded && (
                    <div className="debate-log__entries">
                      {phaseData.entries.map((entry) => (
                        <div
                          key={entry.id}
                          className={`debate-log__entry debate-log__entry--${entry.type} ${entry.category ? `debate-log__entry--category-${entry.category}` : ''} ${onEntryClick ? 'debate-log__entry--clickable' : ''}`}
                          onClick={onEntryClick ? handleEntryClick(entry.id) : undefined}
                          onKeyDown={onEntryClick ? handleEntryKeyDown(entry.id) : undefined}
                          tabIndex={onEntryClick ? 0 : undefined}
                          role={onEntryClick ? 'button' : undefined}
                        >
                          <div className="debate-log__entry-header">
                            <span className="debate-log__entry-icon" aria-hidden="true">
                              {TYPE_ICONS[entry.type] || '📄'}
                            </span>
                            <span className="debate-log__entry-agent">
                              {entry.agentId}
                            </span>
                            <span className={`debate-log__entry-type debate-log__entry-type--${entry.category || 'default'}`}>
                              {TYPE_LABELS[entry.type] || entry.type.toUpperCase()}
                            </span>
                            <span className="debate-log__entry-time">
                              {formatTime(entry.timestamp)}
                            </span>
                          </div>
                          <div className="debate-log__entry-content">
                            {entry.content}
                          </div>
                          {/* Show metadata for orchestrator entries */}
                          {entry.category === 'orchestrator' && entry.metadata && (
                            <div className="debate-log__entry-metadata">
                              {entry.metadata.consensus_reached === true && (
                                <span className="debate-log__consensus-badge">Consensus</span>
                              )}
                              {typeof entry.metadata.resolution_rate === 'number' && (
                                <span className="debate-log__resolution">
                                  Resolution: {entry.metadata.resolution_rate}%
                                </span>
                              )}
                              {typeof entry.metadata.critique_count === 'number' && (
                                <span className="debate-log__stat">
                                  Critiques: {entry.metadata.critique_count}
                                </span>
                              )}
                              {typeof entry.metadata.response_count === 'number' && (
                                <span className="debate-log__stat">
                                  Responses: {entry.metadata.response_count}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="debate-log__empty">
            No debate entries for Round {currentRound}.
          </div>
        )}
      </div>
    </div>
  );
});

export default DebateLogView;
