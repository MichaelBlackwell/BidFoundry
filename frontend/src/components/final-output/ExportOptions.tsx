/**
 * ExportOptions Component
 *
 * Provides export options for the completed document including
 * Word, PDF, Markdown, and shareable link generation.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useState, useCallback } from 'react';
import { Button } from '../ui/Button';
import './ExportOptions.css';

export type ExportFormat = 'word' | 'pdf' | 'markdown' | 'share';

export interface ExportOptionsProps {
  /** Document ID for export */
  documentId: string;
  /** Document title for filename */
  documentTitle: string;
  /** Callback when export is initiated */
  onExport: (format: ExportFormat) => Promise<void>;
  /** Whether export is currently in progress */
  isExporting?: boolean;
  /** Current export format being processed */
  exportingFormat?: ExportFormat | null;
  /** Optional additional CSS class */
  className?: string;
}

interface ExportOption {
  format: ExportFormat;
  label: string;
  icon: string;
  description: string;
  shortcut?: string;
}

const EXPORT_OPTIONS: ExportOption[] = [
  {
    format: 'word',
    label: 'Word',
    icon: '📄',
    description: 'Microsoft Word document (.docx)',
    shortcut: 'Cmd+Shift+W',
  },
  {
    format: 'pdf',
    label: 'PDF',
    icon: '📊',
    description: 'Portable Document Format (.pdf)',
    shortcut: 'Cmd+Shift+P',
  },
  {
    format: 'markdown',
    label: 'Markdown',
    icon: '📋',
    description: 'Markdown text format (.md)',
    shortcut: 'Cmd+Shift+M',
  },
  {
    format: 'share',
    label: 'Share Link',
    icon: '🔗',
    description: 'Generate shareable link',
    shortcut: 'Cmd+Shift+S',
  },
];

export const ExportOptions = memo(function ExportOptions({
  documentId,
  // documentTitle is available via props for future filename customization
  onExport,
  isExporting = false,
  exportingFormat = null,
  className = '',
}: ExportOptionsProps) {
  const [copiedLink, setCopiedLink] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);

  const handleExport = useCallback(
    (format: ExportFormat) => async () => {
      if (isExporting) return;

      if (format === 'share') {
        // Handle share link generation
        await onExport(format);
        // Simulate getting a share link - in real app this would come from the API
        const link = `${window.location.origin}/share/${documentId}`;
        setShareLink(link);

        // Copy to clipboard
        try {
          await navigator.clipboard.writeText(link);
          setCopiedLink(true);
          setTimeout(() => setCopiedLink(false), 3000);
        } catch (err) {
          console.error('Failed to copy link:', err);
        }
      } else {
        await onExport(format);
      }
    },
    [documentId, isExporting, onExport]
  );

  const handleCopyLink = useCallback(async () => {
    if (!shareLink) return;

    try {
      await navigator.clipboard.writeText(shareLink);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 3000);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  }, [shareLink]);

  return (
    <div className={`export-options ${className}`}>
      <h3 className="export-options__title">Export Options</h3>

      <div className="export-options__grid">
        {EXPORT_OPTIONS.map((option) => {
          const isCurrentlyExporting =
            isExporting && exportingFormat === option.format;

          return (
            <button
              key={option.format}
              className={`export-options__button ${isCurrentlyExporting ? 'export-options__button--loading' : ''}`}
              onClick={handleExport(option.format)}
              disabled={isExporting}
              type="button"
              aria-label={`Export as ${option.label}`}
            >
              <span className="export-options__button-icon" aria-hidden="true">
                {isCurrentlyExporting ? '⏳' : option.icon}
              </span>
              <span className="export-options__button-label">{option.label}</span>
              {option.shortcut && (
                <kbd className="export-options__button-shortcut" aria-hidden="true">
                  {option.shortcut.replace('Cmd', '⌘')}
                </kbd>
              )}
            </button>
          );
        })}
      </div>

      {/* Share Link Display */}
      {shareLink && (
        <div className="export-options__share-link">
          <div className="export-options__share-link-header">
            <span className="export-options__share-link-label">Share Link:</span>
            {copiedLink && (
              <span className="export-options__share-link-copied">Copied!</span>
            )}
          </div>
          <div className="export-options__share-link-row">
            <input
              type="text"
              className="export-options__share-link-input"
              value={shareLink}
              readOnly
              onClick={(e) => e.currentTarget.select()}
              aria-label="Share link"
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={handleCopyLink}
              aria-label="Copy share link"
            >
              {copiedLink ? 'Copied' : 'Copy'}
            </Button>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="export-options__quick-actions">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => window.print()}
          aria-label="Print document"
        >
          <span aria-hidden="true">🖨️</span> Print
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleExport('markdown')}
          disabled={isExporting}
          aria-label="Copy as Markdown"
        >
          <span aria-hidden="true">📋</span> Copy as Markdown
        </Button>
      </div>
    </div>
  );
});

export default ExportOptions;
