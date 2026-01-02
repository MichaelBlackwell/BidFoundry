/**
 * DocumentPreview Component
 *
 * Live-updating document preview pane showing sections with confidence scores,
 * revision diffs, and critique warnings.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useCallback, useMemo, useState } from 'react';
import { ConfidenceMeter } from './ConfidenceMeter';
import { SectionList, type SectionRevision } from './SectionList';
import { PreviewControls, type ExportFormat } from './PreviewControls';
import { AgentInsightsPanel } from './AgentInsightsPanel';
import type { DocumentDraft, Critique } from '../../types';
import type { AgentInsights } from '../../stores/swarmStore';
import './DocumentPreview.css';

type PreviewTab = 'document' | 'insights';

export interface DocumentPreviewProps {
  /** The current document draft */
  draft: DocumentDraft | null;
  /** Document title */
  title?: string;
  /** All critiques for cross-referencing */
  critiques?: Critique[];
  /** Previous draft for diff comparison */
  previousDraft?: DocumentDraft | null;
  /** IDs of sections currently being revised */
  revisingSectionIds?: string[];
  /** Active revision notes by section ID */
  revisionNotes?: Record<string, string>;
  /** Whether the document is still being generated */
  isGenerating?: boolean;
  /** Agent insights from blue team agents */
  agentInsights?: AgentInsights;
  /** Callback when a section is clicked (to jump to debate thread) */
  onSectionClick?: (sectionId: string) => void;
  /** Callback when export is requested */
  onExport?: (format: ExportFormat) => void;
  /** Whether the preview pane is expanded */
  isExpanded?: boolean;
  /** Callback when expand/collapse is toggled */
  onToggleExpand?: () => void;
  /** Optional additional CSS class */
  className?: string;
}

export const DocumentPreview = memo(function DocumentPreview({
  draft,
  title = 'Document Preview',
  critiques = [],
  previousDraft = null,
  revisingSectionIds = [],
  revisionNotes = {},
  isGenerating = false,
  agentInsights,
  onSectionClick,
  onExport,
  isExpanded = false,
  onToggleExpand,
  className = '',
}: DocumentPreviewProps) {
  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<PreviewTab>('document');

  // Check if there are any agent insights to show
  const hasInsights = agentInsights && (
    Object.keys(agentInsights.marketIntelligence).length > 0 ||
    Object.keys(agentInsights.captureStrategy).length > 0 ||
    Object.keys(agentInsights.complianceStatus).length > 0 ||
    agentInsights.summary.agentsContributed.length > 0
  );

  // Calculate revisions by comparing with previous draft
  const revisions = useMemo((): SectionRevision[] => {
    if (!previousDraft || !draft || !draft.sections || !previousDraft.sections) return [];

    const revisionsList: SectionRevision[] = [];

    draft.sections.forEach((section) => {
      const previousSection = previousDraft.sections.find(
        (s) => s.id === section.id
      );
      if (previousSection && previousSection.content !== section.content) {
        revisionsList.push({
          sectionId: section.id,
          previousContent: previousSection.content,
          note: revisionNotes[section.id],
        });
      }
    });

    return revisionsList;
  }, [draft, previousDraft, revisionNotes]);

  // Handle section click
  const handleSectionClick = useCallback(
    (sectionId: string) => {
      setSelectedSectionId(sectionId);
      if (onSectionClick) {
        onSectionClick(sectionId);
      }
    },
    [onSectionClick]
  );

  // Handle export
  const handleExport = useCallback(
    (format: ExportFormat) => {
      if (onExport) {
        onExport(format);
      }
    },
    [onExport]
  );

  // Handle expand toggle
  const handleToggleExpand = useCallback(() => {
    if (onToggleExpand) {
      onToggleExpand();
    }
  }, [onToggleExpand]);

  // Get sections with fallback to empty array
  const sections = draft?.sections ?? [];

  // Empty state when no draft or no sections
  if (!draft || sections.length === 0) {
    return (
      <aside
        className={`document-preview document-preview--empty ${className}`}
        role="complementary"
        aria-label="Document Preview"
      >
        <header className="document-preview__header">
          <h2 className="document-preview__title">{title}</h2>
          {onToggleExpand && (
            <PreviewControls
              isExpanded={isExpanded}
              onToggleExpand={handleToggleExpand}
              onExport={handleExport}
              exportEnabled={false}
            />
          )}
        </header>
        <div className="document-preview__empty">
          <p className="document-preview__empty-message">
            {isGenerating
              ? 'Waiting for document content...'
              : 'No document draft available.'}
          </p>
          {isGenerating && (
            <div className="document-preview__loading" aria-hidden="true">
              <span className="document-preview__loading-dot" />
              <span className="document-preview__loading-dot" />
              <span className="document-preview__loading-dot" />
            </div>
          )}
        </div>
      </aside>
    );
  }

  return (
    <aside
      className={`document-preview ${isExpanded ? 'document-preview--expanded' : ''} ${className}`}
      role="complementary"
      aria-label="Document Preview"
      aria-live="polite"
      aria-atomic="false"
      data-panel="document-preview"
      data-document-content
      tabIndex={0}
    >
      {/* Header with title and controls */}
      <header className="document-preview__header">
        <h2 className="document-preview__title">{title}</h2>
        <PreviewControls
          isExpanded={isExpanded}
          onToggleExpand={handleToggleExpand}
          onExport={handleExport}
          exportEnabled={!isGenerating}
        />
      </header>

      {/* Document info bar */}
      <div className="document-preview__info">
        <ConfidenceMeter
          confidence={draft.overallConfidence}
          size="md"
        />
        {isGenerating && (
          <span className="document-preview__status">
            <span className="document-preview__status-indicator" aria-hidden="true" />
            Updating...
          </span>
        )}
      </div>

      {/* Tab navigation */}
      {hasInsights && (
        <nav className="document-preview__tabs" role="tablist" aria-label="Preview tabs">
          <button
            role="tab"
            aria-selected={activeTab === 'document'}
            aria-controls="document-panel"
            className={`document-preview__tab ${activeTab === 'document' ? 'document-preview__tab--active' : ''}`}
            onClick={() => setActiveTab('document')}
          >
            Document
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'insights'}
            aria-controls="insights-panel"
            className={`document-preview__tab ${activeTab === 'insights' ? 'document-preview__tab--active' : ''}`}
            onClick={() => setActiveTab('insights')}
          >
            Agent Insights
            {agentInsights?.summary.agentsContributed.length > 0 && (
              <span className="document-preview__tab-badge">
                {agentInsights.summary.agentsContributed.length}
              </span>
            )}
          </button>
        </nav>
      )}

      {/* Content based on active tab */}
      <div className="document-preview__content">
        {activeTab === 'document' ? (
          <div id="document-panel" role="tabpanel" aria-labelledby="document-tab">
            <SectionList
              sections={sections}
              critiques={critiques}
              revisions={revisions}
              revisingSectionIds={revisingSectionIds}
              selectedSectionId={selectedSectionId}
              onSectionClick={handleSectionClick}
              emptyMessage="No sections in this document yet."
            />
          </div>
        ) : (
          <div id="insights-panel" role="tabpanel" aria-labelledby="insights-tab">
            {agentInsights && (
              <AgentInsightsPanel insights={agentInsights} />
            )}
          </div>
        )}
      </div>

      {/* Footer with section count */}
      <footer className="document-preview__footer">
        <span className="document-preview__section-count">
          {sections.length} section{sections.length !== 1 ? 's' : ''}
        </span>
        <span className="document-preview__updated">
          Last updated: {formatTime(draft.updatedAt)}
        </span>
      </footer>
    </aside>
  );
});

/**
 * Format a date/time for display
 */
function formatTime(date: Date): string {
  const d = new Date(date);
  return d.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default DocumentPreview;
