/**
 * AgentInsightsPanel Component
 *
 * Displays analysis data from blue team agents:
 * - Market Analyst: TAM, SAM, competitive landscape
 * - Capture Strategist: win themes, discriminators, win probability
 * - Compliance Navigator: eligibility, compliance status, OCI risk
 */

import { memo, useState } from 'react';
import type { AgentInsights } from '../../stores/swarmStore';
import './AgentInsightsPanel.css';

export interface AgentInsightsPanelProps {
  insights: AgentInsights;
}

export const AgentInsightsPanel = memo(function AgentInsightsPanel({
  insights,
}: AgentInsightsPanelProps) {
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  const toggleCard = (cardId: string) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(cardId)) {
        next.delete(cardId);
      } else {
        next.add(cardId);
      }
      return next;
    });
  };

  const { marketIntelligence, captureStrategy, complianceStatus, summary } = insights;

  const hasMarketData = Object.keys(marketIntelligence).length > 0;
  const hasCaptureData = Object.keys(captureStrategy).length > 0;
  const hasComplianceData = Object.keys(complianceStatus).length > 0;

  if (!hasMarketData && !hasCaptureData && !hasComplianceData) {
    return (
      <div className="agent-insights-panel agent-insights-panel--empty">
        <p className="agent-insights-panel__empty-message">
          Waiting for agent analysis...
        </p>
      </div>
    );
  }

  return (
    <div className="agent-insights-panel">
      {/* Summary section */}
      {summary.keyFindings.length > 0 && (
        <section className="agent-insights-panel__summary">
          <h3 className="agent-insights-panel__summary-title">Key Findings</h3>
          <ul className="agent-insights-panel__findings-list">
            {summary.keyFindings.map((finding, index) => (
              <li key={index} className="agent-insights-panel__finding">
                {finding}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Agent cards */}
      <div className="agent-insights-panel__cards">
        {/* Market Intelligence Card */}
        {hasMarketData && (
          <article className="agent-insights-card agent-insights-card--market">
            <header
              className="agent-insights-card__header"
              onClick={() => toggleCard('market')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && toggleCard('market')}
              aria-expanded={expandedCards.has('market')}
            >
              <span className="agent-insights-card__icon" aria-hidden="true">
                📊
              </span>
              <h4 className="agent-insights-card__title">Market Intelligence</h4>
              <span className="agent-insights-card__agent">Market Analyst</span>
              <span className="agent-insights-card__toggle" aria-hidden="true">
                {expandedCards.has('market') ? '▼' : '▶'}
              </span>
            </header>

            <div className="agent-insights-card__metrics">
              {marketIntelligence.tam && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">TAM</span>
                  <span className="agent-insights-card__metric-value">
                    {String(marketIntelligence.tam)}
                  </span>
                </div>
              )}
              {marketIntelligence.sam && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">SAM</span>
                  <span className="agent-insights-card__metric-value">
                    {String(marketIntelligence.sam)}
                  </span>
                </div>
              )}
              {marketIntelligence.competitiveDensity && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">Competition</span>
                  <span className="agent-insights-card__metric-value">
                    {marketIntelligence.competitiveDensity}
                  </span>
                </div>
              )}
              {marketIntelligence.opportunityCount !== undefined && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">Opportunities</span>
                  <span className="agent-insights-card__metric-value">
                    {marketIntelligence.opportunityCount}
                  </span>
                </div>
              )}
            </div>

            {expandedCards.has('market') && marketIntelligence.analysisContent && (
              <div className="agent-insights-card__content">
                <p>{marketIntelligence.analysisContent}</p>
              </div>
            )}
          </article>
        )}

        {/* Capture Strategy Card */}
        {hasCaptureData && (
          <article className="agent-insights-card agent-insights-card--capture">
            <header
              className="agent-insights-card__header"
              onClick={() => toggleCard('capture')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && toggleCard('capture')}
              aria-expanded={expandedCards.has('capture')}
            >
              <span className="agent-insights-card__icon" aria-hidden="true">
                🎯
              </span>
              <h4 className="agent-insights-card__title">Capture Strategy</h4>
              <span className="agent-insights-card__agent">Capture Strategist</span>
              <span className="agent-insights-card__toggle" aria-hidden="true">
                {expandedCards.has('capture') ? '▼' : '▶'}
              </span>
            </header>

            <div className="agent-insights-card__metrics">
              {captureStrategy.winProbability && (
                <div className="agent-insights-card__metric agent-insights-card__metric--highlight">
                  <span className="agent-insights-card__metric-label">Win Probability</span>
                  <span className="agent-insights-card__metric-value">
                    {captureStrategy.winProbability}
                  </span>
                </div>
              )}
              {captureStrategy.winThemeCount !== undefined && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">Win Themes</span>
                  <span className="agent-insights-card__metric-value">
                    {captureStrategy.winThemeCount}
                  </span>
                </div>
              )}
              {captureStrategy.discriminatorCount !== undefined && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">Discriminators</span>
                  <span className="agent-insights-card__metric-value">
                    {captureStrategy.discriminatorCount}
                  </span>
                </div>
              )}
              {captureStrategy.competitorCount !== undefined && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">Competitors</span>
                  <span className="agent-insights-card__metric-value">
                    {captureStrategy.competitorCount}
                  </span>
                </div>
              )}
            </div>

            {expandedCards.has('capture') && captureStrategy.analysisContent && (
              <div className="agent-insights-card__content">
                <p>{captureStrategy.analysisContent}</p>
              </div>
            )}
          </article>
        )}

        {/* Compliance Status Card */}
        {hasComplianceData && (
          <article className="agent-insights-card agent-insights-card--compliance">
            <header
              className="agent-insights-card__header"
              onClick={() => toggleCard('compliance')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && toggleCard('compliance')}
              aria-expanded={expandedCards.has('compliance')}
            >
              <span className="agent-insights-card__icon" aria-hidden="true">
                ✓
              </span>
              <h4 className="agent-insights-card__title">Compliance Status</h4>
              <span className="agent-insights-card__agent">Compliance Navigator</span>
              <span className="agent-insights-card__toggle" aria-hidden="true">
                {expandedCards.has('compliance') ? '▼' : '▶'}
              </span>
            </header>

            <div className="agent-insights-card__metrics">
              {complianceStatus.overallStatus && (
                <div className="agent-insights-card__metric agent-insights-card__metric--highlight">
                  <span className="agent-insights-card__metric-label">Status</span>
                  <span className={`agent-insights-card__metric-value agent-insights-card__metric-value--${getStatusClass(complianceStatus.overallStatus)}`}>
                    {complianceStatus.overallStatus}
                  </span>
                </div>
              )}
              {complianceStatus.ociRiskLevel && (
                <div className="agent-insights-card__metric">
                  <span className="agent-insights-card__metric-label">OCI Risk</span>
                  <span className={`agent-insights-card__metric-value agent-insights-card__metric-value--${getRiskClass(complianceStatus.ociRiskLevel)}`}>
                    {complianceStatus.ociRiskLevel}
                  </span>
                </div>
              )}
              {complianceStatus.eligibleSetasides && complianceStatus.eligibleSetasides.length > 0 && (
                <div className="agent-insights-card__metric agent-insights-card__metric--full">
                  <span className="agent-insights-card__metric-label">Eligible Set-Asides</span>
                  <span className="agent-insights-card__metric-value">
                    {complianceStatus.eligibleSetasides.join(', ')}
                  </span>
                </div>
              )}
            </div>

            {expandedCards.has('compliance') && complianceStatus.analysisContent && (
              <div className="agent-insights-card__content">
                <p>{complianceStatus.analysisContent}</p>
              </div>
            )}
          </article>
        )}
      </div>

      {/* Contributing agents footer */}
      {summary.agentsContributed.length > 0 && (
        <footer className="agent-insights-panel__footer">
          <span className="agent-insights-panel__footer-label">
            {summary.agentsContributed.length} agent{summary.agentsContributed.length !== 1 ? 's' : ''} contributed
          </span>
        </footer>
      )}
    </div>
  );
});

/**
 * Get CSS class for compliance status
 */
function getStatusClass(status: string): string {
  const lower = status.toLowerCase();
  if (lower.includes('compliant') || lower.includes('eligible') || lower.includes('pass')) {
    return 'success';
  }
  if (lower.includes('issue') || lower.includes('gap') || lower.includes('fail')) {
    return 'error';
  }
  return 'warning';
}

/**
 * Get CSS class for risk level
 */
function getRiskClass(risk: string): string {
  const lower = risk.toLowerCase();
  if (lower.includes('low') || lower.includes('minimal')) {
    return 'success';
  }
  if (lower.includes('high') || lower.includes('critical')) {
    return 'error';
  }
  return 'warning';
}

export default AgentInsightsPanel;
