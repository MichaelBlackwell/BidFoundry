/**
 * useDocumentPreview Hook
 *
 * Custom hook for connecting the DocumentPreview component to the swarm store.
 * Provides computed values and callbacks for document preview functionality.
 */

import { useCallback, useMemo } from 'react';
import { useSwarmStore, selectLatestDraft, selectUnresolvedCritiques } from '../stores/swarmStore';
import { useUIStore } from '../stores/uiStore';
import type { ExportFormat } from '../components/document-preview/PreviewControls';
import type { DocumentDraft } from '../types';

export interface UseDocumentPreviewReturn {
  /** Current document draft */
  draft: DocumentDraft | null;
  /** Previous document draft for diff comparison */
  previousDraft: DocumentDraft | null;
  /** All critiques from the swarm */
  critiques: ReturnType<typeof useSwarmStore>['critiques'];
  /** Whether document is currently being generated */
  isGenerating: boolean;
  /** IDs of sections currently being revised */
  revisingSectionIds: string[];
  /** Whether preview pane is expanded */
  isExpanded: boolean;
  /** Toggle preview expansion */
  toggleExpand: () => void;
  /** Handle section click (for jumping to debate thread) */
  handleSectionClick: (sectionId: string) => void;
  /** Handle export request */
  handleExport: (format: ExportFormat) => void;
  /** Document title based on request type */
  documentTitle: string;
}

export function useDocumentPreview(): UseDocumentPreviewReturn {
  // Swarm store state
  const status = useSwarmStore((state) => state.status);
  const request = useSwarmStore((state) => state.request);
  const drafts = useSwarmStore((state) => state.drafts);
  const critiques = useSwarmStore((state) => state.critiques);
  const agents = useSwarmStore((state) => state.agents);

  // UI store state
  const previewExpanded = useUIStore((state) => state.previewExpanded);
  const setPreviewExpanded = useUIStore((state) => state.setPreviewExpanded);

  // Get latest and previous drafts
  const draft = useMemo(() => {
    return drafts.length > 0 ? drafts[drafts.length - 1] : null;
  }, [drafts]);

  const previousDraft = useMemo(() => {
    return drafts.length > 1 ? drafts[drafts.length - 2] : null;
  }, [drafts]);

  // Determine if generation is running
  const isGenerating = status === 'running';

  // Find sections being revised (from agents in 'typing' state targeting sections)
  const revisingSectionIds = useMemo(() => {
    const revisingIds: string[] = [];
    Object.values(agents).forEach((agent) => {
      if (agent.state === 'typing' && agent.target) {
        // Extract section ID from target (assumes format like "Section 3.2" or "section-id")
        const sectionMatch = agent.target.match(/Section\s+(\d+\.?\d*)/i);
        if (sectionMatch) {
          // Map to section by title match
          draft?.sections.forEach((section) => {
            if (section.title.includes(sectionMatch[0]) || section.title.includes(sectionMatch[1])) {
              revisingIds.push(section.id);
            }
          });
        } else {
          // Direct section ID reference
          revisingIds.push(agent.target);
        }
      }
    });
    return revisingIds;
  }, [agents, draft]);

  // Generate document title from request
  const documentTitle = useMemo(() => {
    if (!request) return 'Document Preview';

    const typeLabels: Record<string, string> = {
      'capability-statement': 'Capability Statement',
      'swot-analysis': 'SWOT Analysis',
      'competitive-analysis': 'Competitive Analysis',
      'bd-pipeline-plan': 'BD Pipeline Plan',
      'proposal-strategy': 'Proposal Strategy',
      'go-to-market-strategy': 'Go-to-Market Strategy',
      'teaming-strategy': 'Teaming Strategy',
    };

    return typeLabels[request.documentType] || 'Document Preview';
  }, [request]);

  // Toggle expand/collapse
  const toggleExpand = useCallback(() => {
    setPreviewExpanded(!previewExpanded);
  }, [previewExpanded, setPreviewExpanded]);

  // Handle section click - could navigate to debate thread
  const handleSectionClick = useCallback((sectionId: string) => {
    // Find critiques related to this section and potentially scroll to them
    // This is a placeholder - actual implementation would integrate with debate theater
    console.log('Section clicked:', sectionId);

    // Could emit an event or update state to highlight related debate entries
  }, []);

  // Handle export request
  const handleExport = useCallback((format: ExportFormat) => {
    if (!draft) return;

    switch (format) {
      case 'word':
        exportToWord(draft, documentTitle);
        break;
      case 'pdf':
        exportToPdf(draft, documentTitle);
        break;
      case 'markdown':
        exportToMarkdown(draft, documentTitle);
        break;
      case 'share':
        generateShareLink(draft);
        break;
    }
  }, [draft, documentTitle]);

  return {
    draft,
    previousDraft,
    critiques,
    isGenerating,
    revisingSectionIds,
    isExpanded: previewExpanded,
    toggleExpand,
    handleSectionClick,
    handleExport,
    documentTitle,
  };
}

// Export helper functions (placeholders for actual implementation)

function exportToWord(draft: DocumentDraft, title: string) {
  console.log('Exporting to Word:', title);
  // Implementation would use a library like docx to generate Word files
  alert('Word export coming soon!');
}

function exportToPdf(draft: DocumentDraft, title: string) {
  console.log('Exporting to PDF:', title);
  // Implementation would use a library like jsPDF or call a backend service
  alert('PDF export coming soon!');
}

function exportToMarkdown(draft: DocumentDraft, title: string) {
  console.log('Exporting to Markdown:', title);

  // Generate markdown content
  let markdown = `# ${title}\n\n`;
  markdown += `*Confidence: ${draft.overallConfidence}%*\n\n`;
  markdown += `---\n\n`;

  draft.sections.forEach((section) => {
    markdown += `## ${section.title}\n\n`;
    markdown += `*Confidence: ${section.confidence}%*\n\n`;
    markdown += `${section.content}\n\n`;
  });

  // Copy to clipboard
  navigator.clipboard.writeText(markdown).then(() => {
    alert('Markdown copied to clipboard!');
  }).catch(() => {
    // Fallback: download as file
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, '-')}.md`;
    a.click();
    URL.revokeObjectURL(url);
  });
}

function generateShareLink(draft: DocumentDraft) {
  console.log('Generating share link');
  // Implementation would call backend to generate a shareable link
  alert('Share link generation coming soon!');
}

export default useDocumentPreview;
