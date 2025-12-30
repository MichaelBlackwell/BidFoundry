/**
 * PreviewControls Component
 *
 * Control buttons for the document preview pane including
 * expand/collapse toggle and export options.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useState, useCallback, useRef, useEffect } from 'react';
import './PreviewControls.css';

export type ExportFormat = 'word' | 'pdf' | 'markdown' | 'share';

export interface PreviewControlsProps {
  /** Whether the preview is currently expanded */
  isExpanded: boolean;
  /** Callback when expand/collapse is toggled */
  onToggleExpand: () => void;
  /** Callback when export is requested */
  onExport: (format: ExportFormat) => void;
  /** Whether export actions are currently available */
  exportEnabled?: boolean;
  /** Optional additional CSS class */
  className?: string;
}

const EXPORT_OPTIONS: { format: ExportFormat; label: string; icon: string }[] = [
  { format: 'word', label: 'Word (.docx)', icon: '📄' },
  { format: 'pdf', label: 'PDF', icon: '📊' },
  { format: 'markdown', label: 'Markdown', icon: '📋' },
  { format: 'share', label: 'Share Link', icon: '🔗' },
];

export const PreviewControls = memo(function PreviewControls({
  isExpanded,
  onToggleExpand,
  onExport,
  exportEnabled = true,
  className = '',
}: PreviewControlsProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen]);

  // Close dropdown on Escape
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && isDropdownOpen) {
        setIsDropdownOpen(false);
        buttonRef.current?.focus();
      }
    }

    if (isDropdownOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isDropdownOpen]);

  const toggleDropdown = useCallback(() => {
    setIsDropdownOpen((prev) => !prev);
  }, []);

  const handleExport = useCallback(
    (format: ExportFormat) => {
      onExport(format);
      setIsDropdownOpen(false);
    },
    [onExport]
  );

  const handleDropdownKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const items = dropdownRef.current?.querySelectorAll('button');
        if (!items?.length) return;

        const currentIndex = Array.from(items).findIndex(
          (item) => item === document.activeElement
        );
        let nextIndex: number;

        if (event.key === 'ArrowDown') {
          nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
        } else {
          nextIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
        }

        items[nextIndex]?.focus();
      }
    },
    []
  );

  return (
    <div className={`preview-controls ${className}`}>
      {/* Expand/Collapse Button */}
      <button
        type="button"
        className="preview-controls__btn preview-controls__expand-btn"
        onClick={onToggleExpand}
        aria-pressed={isExpanded}
        title={isExpanded ? 'Collapse preview' : 'Expand preview'}
      >
        <span className="preview-controls__btn-icon" aria-hidden="true">
          {isExpanded ? '⊟' : '⊞'}
        </span>
        <span className="preview-controls__btn-label">
          {isExpanded ? 'Collapse' : 'Expand'}
        </span>
      </button>

      {/* Export Dropdown */}
      <div className="preview-controls__dropdown-container">
        <button
          ref={buttonRef}
          type="button"
          className={`preview-controls__btn preview-controls__export-btn ${isDropdownOpen ? 'preview-controls__export-btn--open' : ''}`}
          onClick={toggleDropdown}
          disabled={!exportEnabled}
          aria-expanded={isDropdownOpen}
          aria-haspopup="listbox"
          aria-label="Export document"
        >
          <span className="preview-controls__btn-label">Export</span>
          <span className="preview-controls__dropdown-arrow" aria-hidden="true">
            {isDropdownOpen ? '▲' : '▼'}
          </span>
        </button>

        {isDropdownOpen && (
          <div
            ref={dropdownRef}
            className="preview-controls__dropdown"
            role="listbox"
            aria-label="Export format options"
            onKeyDown={handleDropdownKeyDown}
          >
            {EXPORT_OPTIONS.map((option) => (
              <button
                key={option.format}
                type="button"
                className="preview-controls__dropdown-item"
                onClick={() => handleExport(option.format)}
                role="option"
              >
                <span className="preview-controls__dropdown-icon" aria-hidden="true">
                  {option.icon}
                </span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
});

export default PreviewControls;
