/**
 * ContentDiff Component
 *
 * Displays visual diff for document revisions showing old content
 * with strikethrough and new content highlighted.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useMemo } from 'react';
import './ContentDiff.css';

export interface DiffSegment {
  /** The text content of this segment */
  text: string;
  /** Type of change: 'unchanged', 'removed', 'added' */
  type: 'unchanged' | 'removed' | 'added';
}

export interface ContentDiffProps {
  /** Array of diff segments to display */
  segments: DiffSegment[];
  /** Whether to show the diff inline or in blocks */
  mode?: 'inline' | 'block';
  /** Optional additional CSS class */
  className?: string;
  /** Accessible label for the diff */
  ariaLabel?: string;
}

export const ContentDiff = memo(function ContentDiff({
  segments,
  mode = 'inline',
  className = '',
  ariaLabel = 'Content revision',
}: ContentDiffProps) {
  // Create accessible description of changes
  const changesSummary = useMemo(() => {
    const removed = segments.filter((s) => s.type === 'removed').length;
    const added = segments.filter((s) => s.type === 'added').length;
    if (removed === 0 && added === 0) {
      return 'No changes';
    }
    const parts = [];
    if (removed > 0) parts.push(`${removed} removal${removed > 1 ? 's' : ''}`);
    if (added > 0) parts.push(`${added} addition${added > 1 ? 's' : ''}`);
    return parts.join(', ');
  }, [segments]);

  if (segments.length === 0) {
    return null;
  }

  return (
    <div
      className={`content-diff content-diff--${mode} ${className}`}
      role="group"
      aria-label={ariaLabel}
    >
      <span className="sr-only">{changesSummary}</span>
      {segments.map((segment, index) => (
        <span
          key={index}
          className={`content-diff__segment content-diff__segment--${segment.type}`}
          aria-label={
            segment.type === 'removed'
              ? 'Removed text'
              : segment.type === 'added'
                ? 'Added text'
                : undefined
          }
        >
          {segment.text}
        </span>
      ))}
    </div>
  );
});

/**
 * Utility function to create diff segments from old and new text.
 * This is a simple implementation - for production use, consider a proper diff library.
 */
export function createSimpleDiff(
  oldText: string,
  newText: string
): DiffSegment[] {
  // If texts are identical, return single unchanged segment
  if (oldText === newText) {
    return [{ text: oldText, type: 'unchanged' }];
  }

  // If old text is empty, everything is added
  if (!oldText) {
    return [{ text: newText, type: 'added' }];
  }

  // If new text is empty, everything is removed
  if (!newText) {
    return [{ text: oldText, type: 'removed' }];
  }

  // Simple word-based diff
  const oldWords = oldText.split(/(\s+)/);
  const newWords = newText.split(/(\s+)/);
  const segments: DiffSegment[] = [];

  // Find longest common prefix
  let prefixEnd = 0;
  while (
    prefixEnd < oldWords.length &&
    prefixEnd < newWords.length &&
    oldWords[prefixEnd] === newWords[prefixEnd]
  ) {
    prefixEnd++;
  }

  // Find longest common suffix
  let oldSuffixStart = oldWords.length;
  let newSuffixStart = newWords.length;
  while (
    oldSuffixStart > prefixEnd &&
    newSuffixStart > prefixEnd &&
    oldWords[oldSuffixStart - 1] === newWords[newSuffixStart - 1]
  ) {
    oldSuffixStart--;
    newSuffixStart--;
  }

  // Add prefix as unchanged
  if (prefixEnd > 0) {
    segments.push({
      text: oldWords.slice(0, prefixEnd).join(''),
      type: 'unchanged',
    });
  }

  // Add removed middle section
  if (oldSuffixStart > prefixEnd) {
    segments.push({
      text: oldWords.slice(prefixEnd, oldSuffixStart).join(''),
      type: 'removed',
    });
  }

  // Add added middle section
  if (newSuffixStart > prefixEnd) {
    segments.push({
      text: newWords.slice(prefixEnd, newSuffixStart).join(''),
      type: 'added',
    });
  }

  // Add suffix as unchanged
  if (oldSuffixStart < oldWords.length) {
    segments.push({
      text: oldWords.slice(oldSuffixStart).join(''),
      type: 'unchanged',
    });
  }

  return segments;
}

export default ContentDiff;
