/**
 * RoundSummary Component
 *
 * Displays a summary of critiques and agent activity for the current round.
 * Part of the Debate Theater view (Section 4.3 of Frontend Design Document).
 */

import { memo, useMemo } from 'react';
import type { Severity } from '../../types';
import './RoundSummary.css';

export interface CritiqueCounts {
  total: number;
  critical: number;
  major: number;
  minor: number;
}

export interface RoundSummaryProps {
  /** Critique counts by severity */
  critiques: CritiqueCounts;
  /** Number of agents that have reported */
  agentsReporting: number;
  /** Total number of agents in this round */
  totalAgents: number;
  /** Whether the round is still in progress */
  isActive?: boolean;
  /** Optional additional CSS class */
  className?: string;
}

interface SeverityDisplayConfig {
  label: string;
  colorVar: string;
}

const SEVERITY_CONFIG: Record<Severity, SeverityDisplayConfig> = {
  critical: { label: 'Critical', colorVar: '--color-severity-critical' },
  major: { label: 'Major', colorVar: '--color-severity-major' },
  minor: { label: 'Minor', colorVar: '--color-severity-minor' },
};

export const RoundSummary = memo(function RoundSummary({
  critiques,
  agentsReporting,
  totalAgents,
  isActive = false,
  className = '',
}: RoundSummaryProps) {
  // Build critique breakdown string
  const critiqueBreakdown = useMemo(() => {
    const parts: string[] = [];
    if (critiques.critical > 0) {
      parts.push(`${critiques.critical} Critical`);
    }
    if (critiques.major > 0) {
      parts.push(`${critiques.major} Major`);
    }
    if (critiques.minor > 0) {
      parts.push(`${critiques.minor} Minor`);
    }
    return parts.join(', ');
  }, [critiques]);

  const hasAnyCritiques = critiques.total > 0;

  return (
    <footer
      className={`round-summary ${isActive ? 'round-summary--active' : ''} ${className}`}
      role="contentinfo"
      aria-label="Round summary"
    >
      <div className="round-summary__divider" aria-hidden="true" />

      <div className="round-summary__content">
        {/* Critique Summary */}
        <div className="round-summary__critiques">
          <span className="round-summary__label">Critiques:</span>
          <span className="round-summary__value">
            {critiques.total} total
            {hasAnyCritiques && (
              <span className="round-summary__breakdown">
                {' '}({critiqueBreakdown})
              </span>
            )}
          </span>
        </div>

        {/* Severity Pills */}
        {hasAnyCritiques && (
          <div className="round-summary__severity-pills" aria-label="Critiques by severity">
            {(Object.entries(SEVERITY_CONFIG) as [Severity, SeverityDisplayConfig][]).map(
              ([severity, config]) => {
                const count = critiques[severity];
                if (count === 0) return null;
                return (
                  <span
                    key={severity}
                    className={`round-summary__pill round-summary__pill--${severity}`}
                    style={{ '--pill-color': `var(${config.colorVar})` } as React.CSSProperties}
                  >
                    {count} {config.label}
                  </span>
                );
              }
            )}
          </div>
        )}

        {/* Agent Progress */}
        <div className="round-summary__agents">
          <span className="round-summary__label">Agents reporting:</span>
          <span className="round-summary__value">
            {agentsReporting}/{totalAgents}
          </span>
          {isActive && agentsReporting < totalAgents && (
            <span className="round-summary__pending" aria-live="polite">
              ({totalAgents - agentsReporting} pending)
            </span>
          )}
        </div>

        {/* Progress indicator for agents */}
        <div
          className="round-summary__progress"
          role="progressbar"
          aria-valuenow={agentsReporting}
          aria-valuemin={0}
          aria-valuemax={totalAgents}
          aria-label="Agent reporting progress"
        >
          <div
            className="round-summary__progress-fill"
            style={{ width: `${(agentsReporting / Math.max(totalAgents, 1)) * 100}%` }}
          />
        </div>
      </div>
    </footer>
  );
});

export default RoundSummary;
