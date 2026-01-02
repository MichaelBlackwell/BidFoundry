/**
 * useGenerationView Hook
 *
 * Unified hook for the GenerationView component that combines state from
 * multiple sources: swarm store, WebSocket, and UI store.
 *
 * This hook provides a single interface for all generation view data and actions.
 */

import { useCallback, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useSwarmStore, selectCritiqueSummary, selectAgentInsights, type AgentInsights } from '../stores/swarmStore';
import { useUIStore } from '../stores/uiStore';
import { useSwarmWebSocket } from './useSwarmWebSocket';
import type { ExportFormat } from '../components/document-preview/PreviewControls';
import type {
  DocumentType,
  GenerationStatus,
  Phase,
  AgentRuntimeState,
  Critique,
  Response,
  DocumentDraft,
} from '../types';
import type { ConnectionStatus } from '../types/websocket';

export interface UseGenerationViewOptions {
  /** Request ID for the current generation */
  requestId?: string;
  /** Callback when generation completes */
  onComplete?: () => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
}

export interface UseGenerationViewReturn {
  // Generation State
  /** Current generation status */
  status: GenerationStatus;
  /** Whether generation is actively running */
  isGenerating: boolean;
  /** Current document title */
  documentTitle: string;
  /** Current document type */
  documentType: DocumentType | undefined;
  /** Current round number (1-indexed) */
  currentRound: number;
  /** Total number of rounds */
  totalRounds: number;
  /** Current phase */
  currentPhase: Phase;
  /** Overall document confidence (0-100) */
  overallConfidence: number;
  /** Error message if any */
  error: string | null;

  // Agent State
  /** Map of agent states by ID */
  agents: Record<string, AgentRuntimeState>;
  /** List of all critiques */
  critiques: Critique[];
  /** List of all responses */
  responses: Response[];
  /** Summary of critiques by severity/status */
  critiqueSummary: {
    total: number;
    critical: number;
    major: number;
    minor: number;
    accepted: number;
    rebutted: number;
    pending: number;
  };

  // Document State
  /** Current document draft */
  draft: DocumentDraft | null;
  /** Previous document draft for diff comparison */
  previousDraft: DocumentDraft | null;
  /** IDs of sections currently being revised */
  revisingSectionIds: string[];
  /** Agent insights from blue team agents */
  agentInsights: AgentInsights;

  // Connection State
  /** WebSocket connection status */
  connectionStatus: ConnectionStatus;

  // Actions
  /** Pause generation */
  pause: () => void;
  /** Resume generation */
  resume: () => void;
  /** Cancel generation */
  cancel: () => void;
  /** Handle export request */
  handleExport: (format: ExportFormat) => void;
  /** Reset state */
  reset: () => void;
}

export function useGenerationView(
  options: UseGenerationViewOptions = {}
): UseGenerationViewReturn {
  const { requestId } = options;

  // ============================================================================
  // Swarm Store State
  // ============================================================================

  const status = useSwarmStore((s) => s.status);
  const request = useSwarmStore((s) => s.request);
  const currentRound = useSwarmStore((s) => s.currentRound);
  const totalRounds = useSwarmStore((s) => s.totalRounds);
  const currentPhase = useSwarmStore((s) => s.currentPhase);
  const agents = useSwarmStore((s) => s.agents);
  const critiques = useSwarmStore((s) => s.critiques);
  const responses = useSwarmStore((s) => s.responses);
  const drafts = useSwarmStore((s) => s.drafts);
  const storeError = useSwarmStore((s) => s.error);
  const critiqueSummary = useSwarmStore(useShallow(selectCritiqueSummary));
  const agentInsights = useSwarmStore(selectAgentInsights);
  const storeReset = useSwarmStore((s) => s.reset);

  // ============================================================================
  // WebSocket
  // ============================================================================

  const {
    pauseGeneration,
    resumeGeneration,
    cancelGeneration,
    connectionStatus,
    isGenerating,
  } = useSwarmWebSocket({
    requestId,
  });

  // ============================================================================
  // Computed Values
  // ============================================================================

  // Get latest and previous drafts
  const draft = useMemo(() => {
    return drafts.length > 0 ? drafts[drafts.length - 1] : null;
  }, [drafts]);

  const previousDraft = useMemo(() => {
    return drafts.length > 1 ? drafts[drafts.length - 2] : null;
  }, [drafts]);

  // Overall confidence from latest draft
  const overallConfidence = draft?.overallConfidence ?? 0;

  // Document title from request
  const documentTitle = useMemo(() => {
    if (!request) return 'Document Generation';

    const typeLabels: Record<string, string> = {
      'capability-statement': 'Capability Statement',
      'swot-analysis': 'SWOT Analysis',
      'competitive-analysis': 'Competitive Analysis',
      'bd-pipeline-plan': 'BD Pipeline Plan',
      'proposal-strategy': 'Proposal Strategy',
      'go-to-market-strategy': 'Go-to-Market Strategy',
      'teaming-strategy': 'Teaming Strategy',
    };

    return typeLabels[request.documentType] || 'Document Generation';
  }, [request]);

  // Document type
  const documentType = request?.documentType;

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
            if (
              section.title.includes(sectionMatch[0]) ||
              section.title.includes(sectionMatch[1])
            ) {
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

  // ============================================================================
  // Actions
  // ============================================================================

  const pause = useCallback(() => {
    pauseGeneration();
  }, [pauseGeneration]);

  const resume = useCallback(() => {
    resumeGeneration();
  }, [resumeGeneration]);

  const cancel = useCallback(() => {
    cancelGeneration();
  }, [cancelGeneration]);

  const reset = useCallback(() => {
    storeReset();
  }, [storeReset]);

  // Export handler
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

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // Generation State
    status,
    isGenerating,
    documentTitle,
    documentType,
    currentRound,
    totalRounds,
    currentPhase,
    overallConfidence,
    error: storeError,

    // Agent State
    agents,
    critiques,
    responses,
    critiqueSummary,

    // Document State
    draft,
    previousDraft,
    revisingSectionIds,
    agentInsights,

    // Connection State
    connectionStatus,

    // Actions
    pause,
    resume,
    cancel,
    handleExport,
    reset,
  };
}

// ============================================================================
// Export Helpers
// ============================================================================

function exportToWord(draft: DocumentDraft, title: string) {
  console.log('Exporting to Word:', title);
  // Implementation would use a library like docx to generate Word files
  // For now, show a placeholder message
  alert('Word export will be available in the final output view.');
}

function exportToPdf(draft: DocumentDraft, title: string) {
  console.log('Exporting to PDF:', title);
  // Implementation would use a library like jsPDF or call a backend service
  alert('PDF export will be available in the final output view.');
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
  navigator.clipboard
    .writeText(markdown)
    .then(() => {
      alert('Markdown copied to clipboard!');
    })
    .catch(() => {
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
  alert('Share link generation will be available in the final output view.');
}

export default useGenerationView;
