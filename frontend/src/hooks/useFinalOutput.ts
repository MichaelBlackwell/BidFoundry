/**
 * useFinalOutput Hook
 *
 * Custom hook for managing the Final Output View state and actions.
 * Provides access to final generation results, export functionality,
 * and tab navigation state.
 */

import { useState, useCallback, useMemo } from 'react';
import { useSwarmStore } from '../stores/swarmStore';
import { useUIStore } from '../stores/uiStore';
import type {
  OutputTab,
  ExportFormat,
  FinalOutput,
  Critique,
  Response,
  AgentRuntimeState,
} from '../types';
import { exportDocument } from '../api/generation';

interface UseFinalOutputOptions {
  /** Document ID for export operations */
  documentId?: string;
  /** Callback after successful export */
  onExportSuccess?: (format: ExportFormat, url?: string) => void;
  /** Callback on export error */
  onExportError?: (error: Error) => void;
}

interface UseFinalOutputReturn {
  // State
  result: FinalOutput | null;
  critiques: Critique[];
  responses: Response[];
  agents: Record<string, AgentRuntimeState>;
  activeTab: OutputTab;
  isExporting: boolean;
  exportingFormat: ExportFormat | null;
  error: string | null;

  // Computed
  documentTitle: string;
  isComplete: boolean;
  requiresReview: boolean;

  // Actions
  setActiveTab: (tab: OutputTab) => void;
  exportAs: (format: ExportFormat) => Promise<void>;
  copyAsMarkdown: () => Promise<void>;
  print: () => void;
  reset: () => void;
}

export function useFinalOutput(
  options: UseFinalOutputOptions = {}
): UseFinalOutputReturn {
  const { documentId, onExportSuccess, onExportError } = options;

  // Swarm store state
  const result = useSwarmStore((s) => s.result);
  const critiques = useSwarmStore((s) => s.critiques);
  const responses = useSwarmStore((s) => s.responses);
  const agents = useSwarmStore((s) => s.agents);
  const status = useSwarmStore((s) => s.status);
  const request = useSwarmStore((s) => s.request);
  const reset = useSwarmStore((s) => s.reset);

  // UI store state
  const activeTab = useUIStore((s) => s.activeTab);
  const setActiveTab = useUIStore((s) => s.setActiveTab);

  // Local state
  const [isExporting, setIsExporting] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Computed values
  const isComplete = useMemo(() => status === 'complete', [status]);
  const requiresReview = useMemo(
    () => result?.requiresHumanReview ?? false,
    [result]
  );

  const documentTitle = useMemo(() => {
    if (!request) return 'Untitled Document';

    // Try to build title from opportunity context
    const { opportunityContext, documentType } = request;
    if (opportunityContext?.solicitationNumber) {
      return opportunityContext.solicitationNumber;
    }
    if (opportunityContext?.targetAgency) {
      return `${opportunityContext.targetAgency} Strategy`;
    }

    // Fall back to document type
    return documentType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  }, [request]);

  // Export function
  const exportAs = useCallback(
    async (format: ExportFormat) => {
      if (!documentId && !result?.documentId) {
        setError('No document ID available for export');
        return;
      }

      const id = documentId || result?.documentId;
      if (!id) return;

      setIsExporting(true);
      setExportingFormat(format);
      setError(null);

      try {
        const exportResult = await exportDocument(id, format);

        if (format === 'share') {
          // For share, we get back a URL
          onExportSuccess?.(format, exportResult.url);
        } else {
          // For other formats, trigger download
          if (exportResult.blob) {
            const url = URL.createObjectURL(exportResult.blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${documentTitle}.${getFileExtension(format)}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }
          onExportSuccess?.(format);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Export failed';
        setError(errorMessage);
        onExportError?.(err instanceof Error ? err : new Error(errorMessage));
      } finally {
        setIsExporting(false);
        setExportingFormat(null);
      }
    },
    [documentId, result?.documentId, documentTitle, onExportSuccess, onExportError]
  );

  // Copy as Markdown
  const copyAsMarkdown = useCallback(async () => {
    if (!result?.content) {
      setError('No content available to copy');
      return;
    }

    try {
      const markdown = generateMarkdown(result.content, documentTitle);
      await navigator.clipboard.writeText(markdown);
      onExportSuccess?.('markdown');
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to copy to clipboard';
      setError(errorMessage);
      onExportError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  }, [result?.content, documentTitle, onExportSuccess, onExportError]);

  // Print
  const print = useCallback(() => {
    window.print();
  }, []);

  return {
    // State
    result,
    critiques,
    responses,
    agents,
    activeTab,
    isExporting,
    exportingFormat,
    error,

    // Computed
    documentTitle,
    isComplete,
    requiresReview,

    // Actions
    setActiveTab,
    exportAs,
    copyAsMarkdown,
    print,
    reset,
  };
}

// Helper functions
function getFileExtension(format: ExportFormat): string {
  switch (format) {
    case 'word':
      return 'docx';
    case 'pdf':
      return 'pdf';
    case 'markdown':
      return 'md';
    default:
      return 'txt';
  }
}

function generateMarkdown(
  content: { sections: { title: string; content: string; confidence: number }[] },
  title: string
): string {
  let markdown = `# ${title}\n\n`;

  content.sections.forEach((section, index) => {
    markdown += `## ${index + 1}. ${section.title}\n\n`;
    markdown += `${section.content}\n\n`;
  });

  markdown += `---\n\n*Generated with Adversarial Swarm*\n`;

  return markdown;
}

export default useFinalOutput;
