/**
 * RedTeamReportView Component
 *
 * Displays the Red Team report showing all critiques raised during generation,
 * their disposition (accepted, rebutted, acknowledged), and any residual risks.
 *
 * Based on Section 4.7 and Section 6.2 of the Adversarial Swarm Design Document.
 */

import { memo, useMemo, useState } from 'react';
import type { Critique, Response, RedTeamReport as RedTeamReportType } from '../../types';
import './RedTeamReportView.css';

export interface RedTeamReportViewProps {
  /** Red team report data */
  report: RedTeamReportType;
  /** All critiques from the generation */
  critiques: Critique[];
  /** All responses from the generation */
  responses: Response[];
  /** Callback when a critique is clicked */
  onCritiqueClick?: (critiqueId: string) => void;
  /** Optional additional CSS class */
  className?: string;
}

type FilterType = 'all' | 'accepted' | 'rebutted' | 'acknowledged' | 'unresolved';
type SeverityFilter = 'all' | 'critical' | 'major' | 'minor';

interface CritiqueWithResponse {
  critique: Critique;
  response?: Response;
}

export const RedTeamReportView = memo(function RedTeamReportView({
  report,
  critiques,
  responses,
  onCritiqueClick,
  className = '',
}: RedTeamReportViewProps) {
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');

  // Pair critiques with their responses
  const critiquesWithResponses = useMemo<CritiqueWithResponse[]>(() => {
    return critiques.map((critique) => ({
      critique,
      response: responses.find((r) => r.critiqueId === critique.id),
    }));
  }, [critiques, responses]);

  // Apply filters
  const filteredCritiques = useMemo(() => {
    return critiquesWithResponses.filter((item) => {
      // Filter by disposition
      if (filterType !== 'all') {
        const status = item.critique.status || 'pending';
        if (filterType === 'unresolved' && status !== 'pending') return false;
        if (filterType === 'accepted' && status !== 'accepted') return false;
        if (filterType === 'rebutted' && status !== 'rebutted') return false;
        if (filterType === 'acknowledged' && status !== 'acknowledged') return false;
      }

      // Filter by severity
      if (severityFilter !== 'all' && item.critique.severity !== severityFilter) {
        return false;
      }

      return true;
    });
  }, [critiquesWithResponses, filterType, severityFilter]);

  // Summary counts
  const summaryCounts = useMemo(() => {
    const counts = {
      total: critiques.length,
      critical: 0,
      major: 0,
      minor: 0,
      accepted: 0,
      rebutted: 0,
      acknowledged: 0,
      unresolved: 0,
    };

    critiques.forEach((c) => {
      counts[c.severity]++;
      const status = c.status || 'pending';
      if (status === 'pending') counts.unresolved++;
      else if (status === 'accepted') counts.accepted++;
      else if (status === 'rebutted') counts.rebutted++;
      else if (status === 'acknowledged') counts.acknowledged++;
    });

    return counts;
  }, [critiques]);

  const handleCritiqueClick = (critiqueId: string) => () => {
    onCritiqueClick?.(critiqueId);
  };

  const handleKeyDown = (critiqueId: string) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onCritiqueClick?.(critiqueId);
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'accepted':
        return '✓';
      case 'rebutted':
        return '✗';
      case 'acknowledged':
        return '~';
      default:
        return '?';
    }
  };

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'accepted':
        return 'Accepted';
      case 'rebutted':
        return 'Rebutted';
      case 'acknowledged':
        return 'Acknowledged';
      default:
        return 'Unresolved';
    }
  };

  return (
    <div className={`red-team-report ${className}`}>
      {/* Summary Section */}
      {report.summary && (
        <div className="red-team-report__summary">
          <h3 className="red-team-report__summary-title">Summary</h3>
          <p className="red-team-report__summary-text">{report.summary}</p>
        </div>
      )}

      {/* Stats Bar */}
      <div className="red-team-report__stats">
        <div className="red-team-report__stat-group">
          <span className="red-team-report__stat red-team-report__stat--total">
            {summaryCounts.total} Challenges
          </span>
          <span className="red-team-report__stat red-team-report__stat--critical">
            {summaryCounts.critical} Critical
          </span>
          <span className="red-team-report__stat red-team-report__stat--major">
            {summaryCounts.major} Major
          </span>
          <span className="red-team-report__stat red-team-report__stat--minor">
            {summaryCounts.minor} Minor
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="red-team-report__filters">
        <div className="red-team-report__filter-group">
          <label className="red-team-report__filter-label">Disposition:</label>
          <select
            className="red-team-report__filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
          >
            <option value="all">All ({summaryCounts.total})</option>
            <option value="accepted">Accepted ({summaryCounts.accepted})</option>
            <option value="rebutted">Rebutted ({summaryCounts.rebutted})</option>
            <option value="acknowledged">Acknowledged ({summaryCounts.acknowledged})</option>
            <option value="unresolved">Unresolved ({summaryCounts.unresolved})</option>
          </select>
        </div>

        <div className="red-team-report__filter-group">
          <label className="red-team-report__filter-label">Severity:</label>
          <select
            className="red-team-report__filter-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
          >
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="major">Major</option>
            <option value="minor">Minor</option>
          </select>
        </div>
      </div>

      {/* Critiques List */}
      <div className="red-team-report__list">
        {filteredCritiques.length === 0 ? (
          <div className="red-team-report__empty">
            No critiques match the selected filters.
          </div>
        ) : (
          filteredCritiques.map(({ critique, response }) => (
            <div
              key={critique.id}
              className={`red-team-report__critique red-team-report__critique--${critique.severity} ${onCritiqueClick ? 'red-team-report__critique--clickable' : ''}`}
              onClick={onCritiqueClick ? handleCritiqueClick(critique.id) : undefined}
              onKeyDown={onCritiqueClick ? handleKeyDown(critique.id) : undefined}
              tabIndex={onCritiqueClick ? 0 : undefined}
              role={onCritiqueClick ? 'button' : undefined}
            >
              <div className="red-team-report__critique-header">
                <span className={`red-team-report__severity red-team-report__severity--${critique.severity}`}>
                  {critique.severity.toUpperCase()}
                </span>
                <span className="red-team-report__agent">{critique.agentId}</span>
                <span
                  className={`red-team-report__status red-team-report__status--${critique.status || 'pending'}`}
                >
                  <span className="red-team-report__status-icon">
                    {getStatusIcon(critique.status)}
                  </span>
                  {getStatusLabel(critique.status)}
                </span>
              </div>

              <div className="red-team-report__critique-target">
                Target: {critique.target}
              </div>

              <div className="red-team-report__critique-content">
                {critique.content}
              </div>

              {critique.suggestedRemedy && (
                <div className="red-team-report__critique-remedy">
                  <strong>Suggested Remedy:</strong> {critique.suggestedRemedy}
                </div>
              )}

              {response && (
                <div className="red-team-report__response">
                  <div className="red-team-report__response-header">
                    Blue Team Response:
                  </div>
                  <div className="red-team-report__response-content">
                    {response.content}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
});

export default RedTeamReportView;
