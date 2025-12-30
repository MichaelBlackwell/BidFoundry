/**
 * SectionCard Component
 *
 * Displays a document section with its confidence score, content,
 * diff visualization for revisions, and critique warnings.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useMemo, useState, useCallback } from 'react';
import { ContentDiff, type DiffSegment } from './ContentDiff';
import type { DocumentSection, Critique } from '../../types';
import './SectionCard.css';

export interface SectionCardProps {
  /** The document section to display */
  section: DocumentSection;
  /** Optional previous version for diff display */
  previousContent?: string;
  /** Critiques related to this section */
  critiques?: Critique[];
  /** Whether this section is currently being revised */
  isRevising?: boolean;
  /** Revision note to display (e.g., "Accepting critique #C-2024") */
  revisionNote?: string;
  /** Callback when user clicks on the section */
  onClick?: (sectionId: string) => void;
  /** Whether the card is currently selected/focused */
  isSelected?: boolean;
  /** Optional additional CSS class */
  className?: string;
}

export const SectionCard = memo(function SectionCard({
  section,
  previousContent,
  critiques = [],
  isRevising = false,
  revisionNote,
  onClick,
  isSelected = false,
  className = '',
}: SectionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate unresolved critiques for this section
  const unresolvedCritiques = useMemo(
    () =>
      critiques.filter(
        (c) =>
          c.target?.includes(section.title) &&
          (c.status === 'pending' || !c.status)
      ),
    [critiques, section.title]
  );

  // Create diff segments if we have previous content
  const diffSegments = useMemo((): DiffSegment[] | null => {
    if (!previousContent || previousContent === section.content) {
      return null;
    }

    // Simple diff: show removed and added portions
    return [
      { text: previousContent, type: 'removed' as const },
      { text: ' ', type: 'unchanged' as const },
      { text: section.content, type: 'added' as const },
    ];
  }, [previousContent, section.content]);

  // Get confidence level for styling
  const confidenceLevel = useMemo(() => {
    if (section.confidence >= 85) return 'high';
    if (section.confidence >= 70) return 'medium';
    return 'low';
  }, [section.confidence]);

  // Handle card click
  const handleClick = useCallback(() => {
    if (onClick) {
      onClick(section.id);
    }
  }, [onClick, section.id]);

  // Handle keyboard interaction
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick();
      }
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        setIsExpanded((prev) => !prev);
      }
    },
    [handleClick]
  );

  // Toggle expansion
  const toggleExpanded = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((prev) => !prev);
  }, []);

  // Content to display (truncated or full based on expansion)
  const displayContent = useMemo(() => {
    const maxLength = 200;
    if (isExpanded || section.content.length <= maxLength) {
      return section.content;
    }
    return section.content.substring(0, maxLength) + '...';
  }, [section.content, isExpanded]);

  const hasLongContent = section.content.length > 200;

  return (
    <article
      className={`section-card ${isSelected ? 'section-card--selected' : ''} ${isRevising ? 'section-card--revising' : ''} ${className}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={onClick ? 0 : -1}
      role={onClick ? 'button' : 'article'}
      aria-expanded={isExpanded}
      aria-label={`Section: ${section.title}, Confidence: ${section.confidence}%`}
    >
      {/* Section Header */}
      <header className="section-card__header">
        <h3 className="section-card__title">{section.title}</h3>
        <div
          className={`section-card__confidence section-card__confidence--${confidenceLevel}`}
          title={`Confidence: ${section.confidence}%`}
          aria-label={`${section.confidence}% confidence`}
        >
          [{section.confidence}%]
        </div>
      </header>

      {/* Warning Badges */}
      {(unresolvedCritiques.length > 0 || isRevising) && (
        <div className="section-card__warnings" role="status">
          {unresolvedCritiques.length > 0 && (
            <span
              className="section-card__warning section-card__warning--critiques"
              aria-label={`${unresolvedCritiques.length} unresolved critiques`}
            >
              <span aria-hidden="true">&#9888;</span>{' '}
              {unresolvedCritiques.length} unresolved critique
              {unresolvedCritiques.length !== 1 ? 's' : ''}
            </span>
          )}
          {isRevising && (
            <span className="section-card__warning section-card__warning--revising">
              <span className="section-card__revising-indicator" aria-hidden="true" />
              Revising...
            </span>
          )}
        </div>
      )}

      {/* Section Content */}
      <div className="section-card__content">
        {diffSegments ? (
          <ContentDiff
            segments={diffSegments}
            mode="block"
            ariaLabel={`Revision for ${section.title}`}
          />
        ) : (
          <p className="section-card__text">{displayContent}</p>
        )}

        {/* Expand/Collapse Button for long content */}
        {hasLongContent && !diffSegments && (
          <button
            type="button"
            className="section-card__expand-btn"
            onClick={toggleExpanded}
            aria-expanded={isExpanded}
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Revision Note */}
      {revisionNote && (
        <div className="section-card__revision-note" role="status">
          [{revisionNote}]
        </div>
      )}
    </article>
  );
});

export default SectionCard;
