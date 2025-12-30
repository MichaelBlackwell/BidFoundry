/**
 * GenerationStats Component
 *
 * Displays statistics about the document generation process including
 * rounds completed, critique counts, and time elapsed.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useMemo } from 'react';
import type { GenerationMetrics } from '../../types';
import './GenerationStats.css';

export interface GenerationStatsProps {
  /** Generation metrics data */
  metrics: GenerationMetrics;
  /** Optional additional CSS class */
  className?: string;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`;
}

export const GenerationStats = memo(function GenerationStats({
  metrics,
  className = '',
}: GenerationStatsProps) {
  const critiqueBreakdown = useMemo(() => {
    return [
      { label: 'Critical', count: metrics.criticalCount, color: 'critical' },
      { label: 'Major', count: metrics.majorCount, color: 'major' },
      { label: 'Minor', count: metrics.minorCount, color: 'minor' },
    ];
  }, [metrics]);

  const dispositionBreakdown = useMemo(() => {
    return [
      { label: 'Accepted', count: metrics.acceptedCount },
      { label: 'Rebutted', count: metrics.rebuttedCount },
      { label: 'Acknowledged', count: metrics.acknowledgedCount },
    ];
  }, [metrics]);

  return (
    <div className={`generation-stats ${className}`}>
      <h3 className="generation-stats__title">Generation Stats</h3>

      <div className="generation-stats__grid">
        {/* Rounds Completed */}
        <div className="generation-stats__stat">
          <span className="generation-stats__stat-icon" aria-hidden="true">
            &#x21BB;
          </span>
          <div className="generation-stats__stat-content">
            <span className="generation-stats__stat-label">
              Rounds completed:
            </span>
            <span className="generation-stats__stat-value">
              {metrics.roundsCompleted}
            </span>
          </div>
        </div>

        {/* Time Elapsed */}
        <div className="generation-stats__stat">
          <span className="generation-stats__stat-icon" aria-hidden="true">
            &#x23F1;
          </span>
          <div className="generation-stats__stat-content">
            <span className="generation-stats__stat-label">Time elapsed:</span>
            <span className="generation-stats__stat-value">
              {formatDuration(metrics.timeElapsedMs)}
            </span>
          </div>
        </div>
      </div>

      {/* Critiques Summary */}
      <div className="generation-stats__section">
        <h4 className="generation-stats__section-title">
          Total critiques:{' '}
          <span className="generation-stats__highlight">
            {metrics.totalCritiques}
          </span>
        </h4>
        <div className="generation-stats__breakdown">
          {critiqueBreakdown.map((item) => (
            <span
              key={item.label}
              className={`generation-stats__breakdown-item generation-stats__breakdown-item--${item.color}`}
            >
              {item.count} {item.label}
            </span>
          ))}
        </div>
      </div>

      {/* Disposition Summary */}
      <div className="generation-stats__section">
        <h4 className="generation-stats__section-title">Disposition:</h4>
        <div className="generation-stats__disposition">
          {dispositionBreakdown.map((item, index) => (
            <span key={item.label} className="generation-stats__disposition-item">
              {item.label}: {item.count}
              {index < dispositionBreakdown.length - 1 && (
                <span className="generation-stats__separator">|</span>
              )}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
});

export default GenerationStats;
