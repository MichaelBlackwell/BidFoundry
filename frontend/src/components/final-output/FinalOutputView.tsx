/**
 * FinalOutputView Component
 *
 * The post-generation document view showing the completed document with full artifacts
 * including the Red Team Report, Debate Log, and detailed Metrics.
 *
 * Based on Section 4.7 (Final Output View) and Implementation Chunk F10 of the
 * Frontend Design Document.
 */

import { memo, useState, useCallback, useEffect, useMemo } from 'react';
import { TabBar } from './TabBar';
import { ConfidenceBreakdown } from './ConfidenceBreakdown';
import { GenerationStats } from './GenerationStats';
import { DocumentContent } from './DocumentContent';
import { RedTeamReportView } from './RedTeamReportView';
import { DebateLogView } from './DebateLogView';
import { MetricsView } from './MetricsView';
import { ExportOptions, type ExportFormat } from './ExportOptions';
import { AgentInsightsPanel } from '../document-preview/AgentInsightsPanel';
import type {
  OutputTab,
  FinalOutput,
  DocumentType,
  Critique,
  Response,
  AgentRuntimeState,
  AgentInsights,
} from '../../types';
import { DOCUMENT_TYPE_LABELS } from '../../types';
import type { AgentInsights as StoreAgentInsights } from '../../stores/swarmStore';
import './FinalOutputView.css';

/**
 * Convert API AgentInsights format to the store format expected by AgentInsightsPanel
 */
function convertToStoreFormat(apiInsights: AgentInsights): StoreAgentInsights {
  return {
    marketIntelligence: apiInsights.marketIntelligence as StoreAgentInsights['marketIntelligence'],
    captureStrategy: apiInsights.captureStrategy as StoreAgentInsights['captureStrategy'],
    complianceStatus: apiInsights.complianceStatus as StoreAgentInsights['complianceStatus'],
    summary: {
      agentsContributed: apiInsights.summary.agentsContributed.map((a) => a.name || a.role),
      keyFindings: apiInsights.summary.keyFindings,
    },
  };
}

export interface FinalOutputViewProps {
  /** The final output data from generation */
  result: FinalOutput;
  /** Document type for title formatting */
  documentType: DocumentType;
  /** Document title */
  title: string;
  /** All critiques from the generation */
  critiques: Critique[];
  /** All responses from the generation */
  responses: Response[];
  /** Agent states for metrics */
  agents: Record<string, AgentRuntimeState>;
  /** Callback when export is initiated */
  onExport?: (format: ExportFormat) => Promise<void>;
  /** Callback when section is clicked for detailed view */
  onSectionClick?: (sectionId: string) => void;
  /** Callback when critique is clicked */
  onCritiqueClick?: (critiqueId: string) => void;
  /** Callback when debate entry is clicked */
  onDebateEntryClick?: (entryId: string) => void;
  /** Initial active tab */
  initialTab?: OutputTab;
  /** Optional additional CSS class */
  className?: string;
  /** Hide the Agent Insights tab (e.g., when viewing from history) */
  hideInsights?: boolean;
}

export const FinalOutputView = memo(function FinalOutputView({
  result,
  documentType,
  title,
  critiques,
  responses,
  agents,
  onExport,
  onSectionClick,
  onCritiqueClick,
  onDebateEntryClick,
  initialTab = 'document',
  className = '',
  hideInsights = false,
}: FinalOutputViewProps) {
  const [activeTab, setActiveTab] = useState<OutputTab>(initialTab);
  const [isExporting, setIsExporting] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);

  // Build section titles map for confidence breakdown
  const sectionTitles = useMemo(() => {
    const titles: Record<string, string> = {};
    result.content.sections.forEach((section) => {
      titles[section.id] = section.title;
    });
    return titles;
  }, [result.content.sections]);

  // Handle export with loading state
  const handleExport = useCallback(
    async (format: ExportFormat) => {
      if (!onExport) return;

      setIsExporting(true);
      setExportingFormat(format);

      try {
        await onExport(format);
      } finally {
        setIsExporting(false);
        setExportingFormat(null);
      }
    },
    [onExport]
  );

  // Handle tab change with keyboard shortcuts
  const handleTabChange = useCallback((tab: OutputTab) => {
    setActiveTab(tab);
  }, []);

  // Keyboard shortcut for export (Cmd/Ctrl + E)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        // Default to PDF export
        handleExport('pdf');
      }

      // Copy as Markdown (Cmd/Ctrl + Shift + C)
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'c') {
        e.preventDefault();
        handleExport('markdown');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleExport]);

  // Render tab panel content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'document':
        return (
          <DocumentContent
            draft={result.content}
            title={title}
            onSectionClick={onSectionClick}
          />
        );

      case 'redteam':
        return (
          <RedTeamReportView
            report={result.redTeamReport}
            critiques={critiques}
            responses={responses}
            onCritiqueClick={onCritiqueClick}
          />
        );

      case 'debate':
        return (
          <DebateLogView
            entries={result.debateLog}
            totalRounds={result.metrics.roundsCompleted}
            onEntryClick={onDebateEntryClick}
          />
        );

      case 'metrics':
        return (
          <MetricsView
            metrics={result.metrics}
            critiques={critiques}
            agents={agents}
          />
        );

      case 'insights':
        return result.agentInsights ? (
          <AgentInsightsPanel insights={convertToStoreFormat(result.agentInsights)} />
        ) : (
          <div className="final-output__no-insights">
            <p>No agent insights available for this document.</p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`final-output ${className}`}>
      {/* Header */}
      <header className="final-output__header">
        <div className="final-output__header-content">
          <span className="final-output__status" aria-label="Document complete">
            ✓
          </span>
          <div className="final-output__header-text">
            <h1 className="final-output__title">Document Complete</h1>
            <p className="final-output__subtitle">
              {DOCUMENT_TYPE_LABELS[documentType]}: {title}
            </p>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <TabBar activeTab={activeTab} onTabChange={handleTabChange} hideInsights={hideInsights} />

      {/* Main Content Area */}
      <div className="final-output__layout">
        {/* Main Panel - Tab Content */}
        <main
          className="final-output__main"
          role="tabpanel"
          id={`tabpanel-${activeTab}`}
          aria-labelledby={`tab-${activeTab}`}
        >
          {renderTabContent()}
        </main>

        {/* Sidebar - Stats & Export */}
        <aside className="final-output__sidebar">
          <ConfidenceBreakdown
            confidence={result.confidence}
            sectionTitles={sectionTitles}
            onSectionClick={onSectionClick}
          />

          <GenerationStats metrics={result.metrics} />

          {onExport && (
            <ExportOptions
              documentId={result.documentId}
              documentTitle={title}
              onExport={handleExport}
              isExporting={isExporting}
              exportingFormat={exportingFormat}
            />
          )}
        </aside>
      </div>

      {/* Human Review Warning (if applicable) */}
      {result.requiresHumanReview && result.escalation && (
        <div className="final-output__review-notice" role="alert">
          <span className="final-output__review-icon" aria-hidden="true">
            ⚠️
          </span>
          <div className="final-output__review-content">
            <strong>Human Review Completed</strong>
            <p>
              This document was flagged for review due to:{' '}
              {result.escalation.reasons.join(', ')}
            </p>
          </div>
        </div>
      )}

      {/* Keyboard Shortcuts Hint */}
      <div className="final-output__shortcuts" aria-hidden="true">
        <kbd>1-5</kbd> Switch tabs
        <kbd>Cmd+E</kbd> Export PDF
        <kbd>Cmd+Shift+C</kbd> Copy Markdown
        <kbd>[</kbd>/<kbd>]</kbd> Navigate rounds
      </div>
    </div>
  );
});

export default FinalOutputView;
