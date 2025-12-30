/**
 * MetricsView Component
 *
 * Displays detailed metrics and analytics about the document generation process,
 * including charts for critique distribution and agent performance.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useMemo } from 'react';
import type { GenerationMetrics, Critique, AgentRuntimeState } from '../../types';
import './MetricsView.css';

export interface MetricsViewProps {
  /** Generation metrics data */
  metrics: GenerationMetrics;
  /** All critiques for detailed breakdown */
  critiques: Critique[];
  /** Agent states for performance analysis */
  agents: Record<string, AgentRuntimeState>;
  /** Optional additional CSS class */
  className?: string;
}

interface AgentActivity {
  agentId: string;
  name: string;
  category: string;
  critiqueCount: number;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${seconds.toString().padStart(2, '0')}s`;
}

export const MetricsView = memo(function MetricsView({
  metrics,
  critiques,
  agents,
  className = '',
}: MetricsViewProps) {
  // Calculate critique distribution by round
  const critiquesByRound = useMemo(() => {
    const roundCounts: Record<number, number> = {};
    critiques.forEach((c) => {
      roundCounts[c.round] = (roundCounts[c.round] || 0) + 1;
    });
    return roundCounts;
  }, [critiques]);

  // Calculate agent activity
  const agentActivity = useMemo<AgentActivity[]>(() => {
    const activity: Record<string, AgentActivity> = {};

    critiques.forEach((c) => {
      if (!activity[c.agentId]) {
        const agent = agents[c.agentId];
        activity[c.agentId] = {
          agentId: c.agentId,
          name: agent?.name || c.agentId,
          category: agent?.category || 'unknown',
          critiqueCount: 0,
        };
      }
      activity[c.agentId].critiqueCount++;
    });

    return Object.values(activity).sort((a, b) => b.critiqueCount - a.critiqueCount);
  }, [critiques, agents]);

  // Calculate acceptance rate
  const acceptanceRate = useMemo(() => {
    if (metrics.totalCritiques === 0) return 0;
    return Math.round((metrics.acceptedCount / metrics.totalCritiques) * 100);
  }, [metrics]);

  // Calculate rebuttal rate
  const rebuttalRate = useMemo(() => {
    if (metrics.totalCritiques === 0) return 0;
    return Math.round((metrics.rebuttedCount / metrics.totalCritiques) * 100);
  }, [metrics]);

  // Bar chart helper for severity distribution
  const severityBarWidths = useMemo(() => {
    const max = Math.max(
      metrics.criticalCount,
      metrics.majorCount,
      metrics.minorCount,
      1
    );
    return {
      critical: (metrics.criticalCount / max) * 100,
      major: (metrics.majorCount / max) * 100,
      minor: (metrics.minorCount / max) * 100,
    };
  }, [metrics]);

  return (
    <div className={`metrics-view ${className}`}>
      {/* Summary Cards */}
      <div className="metrics-view__summary">
        <div className="metrics-view__card">
          <div className="metrics-view__card-value">{metrics.roundsCompleted}</div>
          <div className="metrics-view__card-label">Rounds Completed</div>
        </div>
        <div className="metrics-view__card">
          <div className="metrics-view__card-value">{formatDuration(metrics.timeElapsedMs)}</div>
          <div className="metrics-view__card-label">Time Elapsed</div>
        </div>
        <div className="metrics-view__card">
          <div className="metrics-view__card-value">{metrics.totalCritiques}</div>
          <div className="metrics-view__card-label">Total Critiques</div>
        </div>
        <div className="metrics-view__card">
          <div className="metrics-view__card-value">{acceptanceRate}%</div>
          <div className="metrics-view__card-label">Acceptance Rate</div>
        </div>
      </div>

      <div className="metrics-view__grid">
        {/* Severity Distribution */}
        <div className="metrics-view__section">
          <h3 className="metrics-view__section-title">Critique Severity Distribution</h3>
          <div className="metrics-view__chart">
            <div className="metrics-view__bar-row">
              <span className="metrics-view__bar-label">Critical</span>
              <div className="metrics-view__bar-container">
                <div
                  className="metrics-view__bar metrics-view__bar--critical"
                  style={{ width: `${severityBarWidths.critical}%` }}
                />
              </div>
              <span className="metrics-view__bar-value">{metrics.criticalCount}</span>
            </div>
            <div className="metrics-view__bar-row">
              <span className="metrics-view__bar-label">Major</span>
              <div className="metrics-view__bar-container">
                <div
                  className="metrics-view__bar metrics-view__bar--major"
                  style={{ width: `${severityBarWidths.major}%` }}
                />
              </div>
              <span className="metrics-view__bar-value">{metrics.majorCount}</span>
            </div>
            <div className="metrics-view__bar-row">
              <span className="metrics-view__bar-label">Minor</span>
              <div className="metrics-view__bar-container">
                <div
                  className="metrics-view__bar metrics-view__bar--minor"
                  style={{ width: `${severityBarWidths.minor}%` }}
                />
              </div>
              <span className="metrics-view__bar-value">{metrics.minorCount}</span>
            </div>
          </div>
        </div>

        {/* Disposition Breakdown */}
        <div className="metrics-view__section">
          <h3 className="metrics-view__section-title">Critique Disposition</h3>
          <div className="metrics-view__disposition">
            <div className="metrics-view__disposition-item">
              <div className="metrics-view__disposition-circle metrics-view__disposition-circle--accepted">
                <span className="metrics-view__disposition-value">
                  {metrics.acceptedCount}
                </span>
              </div>
              <span className="metrics-view__disposition-label">Accepted</span>
              <span className="metrics-view__disposition-percent">{acceptanceRate}%</span>
            </div>
            <div className="metrics-view__disposition-item">
              <div className="metrics-view__disposition-circle metrics-view__disposition-circle--rebutted">
                <span className="metrics-view__disposition-value">
                  {metrics.rebuttedCount}
                </span>
              </div>
              <span className="metrics-view__disposition-label">Rebutted</span>
              <span className="metrics-view__disposition-percent">{rebuttalRate}%</span>
            </div>
            <div className="metrics-view__disposition-item">
              <div className="metrics-view__disposition-circle metrics-view__disposition-circle--acknowledged">
                <span className="metrics-view__disposition-value">
                  {metrics.acknowledgedCount}
                </span>
              </div>
              <span className="metrics-view__disposition-label">Acknowledged</span>
              <span className="metrics-view__disposition-percent">
                {metrics.totalCritiques > 0
                  ? Math.round((metrics.acknowledgedCount / metrics.totalCritiques) * 100)
                  : 0}%
              </span>
            </div>
          </div>
        </div>

        {/* Critiques by Round */}
        <div className="metrics-view__section">
          <h3 className="metrics-view__section-title">Critiques by Round</h3>
          <div className="metrics-view__rounds">
            {Object.entries(critiquesByRound).map(([round, count]) => (
              <div key={round} className="metrics-view__round-item">
                <span className="metrics-view__round-label">Round {round}</span>
                <div className="metrics-view__round-bar-container">
                  <div
                    className="metrics-view__round-bar"
                    style={{
                      width: `${(count / Math.max(...Object.values(critiquesByRound), 1)) * 100}%`,
                    }}
                  />
                </div>
                <span className="metrics-view__round-value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Agent Activity */}
        <div className="metrics-view__section">
          <h3 className="metrics-view__section-title">Agent Activity</h3>
          <div className="metrics-view__agents">
            {agentActivity.length === 0 ? (
              <div className="metrics-view__empty">No agent activity recorded.</div>
            ) : (
              agentActivity.map((agent) => (
                <div key={agent.agentId} className="metrics-view__agent-item">
                  <span
                    className={`metrics-view__agent-indicator metrics-view__agent-indicator--${agent.category}`}
                    aria-hidden="true"
                  />
                  <span className="metrics-view__agent-name">{agent.name}</span>
                  <span className="metrics-view__agent-count">
                    {agent.critiqueCount} critique{agent.critiqueCount !== 1 ? 's' : ''}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Health Assessment */}
      <div className="metrics-view__health">
        <h3 className="metrics-view__section-title">Adversarial Health Assessment</h3>
        <div className="metrics-view__health-content">
          <HealthIndicator
            label="Red/Blue Tension"
            value={acceptanceRate}
            optimalRange={[40, 60]}
            description="Healthy tension when 40-60% of critiques are accepted"
          />
          <HealthIndicator
            label="Critical Issue Resolution"
            value={metrics.criticalCount > 0
              ? Math.round(((metrics.acceptedCount + metrics.acknowledgedCount) / metrics.criticalCount) * 100 * (metrics.criticalCount / metrics.totalCritiques))
              : 100}
            optimalRange={[80, 100]}
            description="High resolution rate indicates effective critique handling"
          />
          <HealthIndicator
            label="Adversarial Efficiency"
            value={Math.min(100, Math.round((metrics.totalCritiques / metrics.roundsCompleted) * 10))}
            optimalRange={[30, 70]}
            description="Critiques per round (moderate is ideal)"
          />
        </div>
      </div>
    </div>
  );
});

interface HealthIndicatorProps {
  label: string;
  value: number;
  optimalRange: [number, number];
  description: string;
}

const HealthIndicator = memo(function HealthIndicator({
  label,
  value,
  optimalRange,
  description,
}: HealthIndicatorProps) {
  const isOptimal = value >= optimalRange[0] && value <= optimalRange[1];
  const status = isOptimal ? 'optimal' : value < optimalRange[0] ? 'low' : 'high';

  return (
    <div className={`metrics-view__health-item metrics-view__health-item--${status}`}>
      <div className="metrics-view__health-header">
        <span className="metrics-view__health-label">{label}</span>
        <span className={`metrics-view__health-status metrics-view__health-status--${status}`}>
          {status === 'optimal' ? 'Healthy' : status === 'low' ? 'Low' : 'High'}
        </span>
      </div>
      <div className="metrics-view__health-bar">
        <div className="metrics-view__health-optimal" style={{
          left: `${optimalRange[0]}%`,
          width: `${optimalRange[1] - optimalRange[0]}%`,
        }} />
        <div
          className="metrics-view__health-marker"
          style={{ left: `${Math.min(100, Math.max(0, value))}%` }}
        />
      </div>
      <div className="metrics-view__health-description">{description}</div>
    </div>
  );
});

export default MetricsView;
