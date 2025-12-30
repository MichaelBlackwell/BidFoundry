/**
 * DocumentContent Component
 *
 * Renders the final document content with sections, allowing users
 * to view the completed strategy document.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useCallback } from 'react';
import type { DocumentDraft, DocumentSection } from '../../types';
import './DocumentContent.css';

export interface DocumentContentProps {
  /** The final document draft */
  draft: DocumentDraft;
  /** Document title */
  title: string;
  /** Callback when a section is clicked */
  onSectionClick?: (sectionId: string) => void;
  /** Optional additional CSS class */
  className?: string;
}

interface SectionProps {
  section: DocumentSection;
  index: number;
  onClick?: () => void;
}

const Section = memo(function Section({
  section,
  index,
  onClick,
}: SectionProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.key === 'Enter' || e.key === ' ') && onClick) {
      e.preventDefault();
      onClick();
    }
  };

  const confidenceLevel =
    section.confidence >= 85
      ? 'high'
      : section.confidence >= 70
        ? 'medium'
        : 'low';

  return (
    <section
      className={`document-content__section ${onClick ? 'document-content__section--clickable' : ''}`}
      onClick={onClick}
      onKeyDown={onClick ? handleKeyDown : undefined}
      tabIndex={onClick ? 0 : undefined}
      role={onClick ? 'button' : undefined}
      aria-label={onClick ? `View details for ${section.title}` : undefined}
    >
      <div className="document-content__section-header">
        <h3 className="document-content__section-title">
          {index + 1}. {section.title}
        </h3>
        <span
          className={`document-content__section-confidence document-content__section-confidence--${confidenceLevel}`}
        >
          [{section.confidence}%]
        </span>
        {section.unresolvedCritiques > 0 && (
          <span
            className="document-content__section-warning"
            title={`${section.unresolvedCritiques} unresolved critique${section.unresolvedCritiques > 1 ? 's' : ''}`}
            aria-label={`Warning: ${section.unresolvedCritiques} unresolved critique${section.unresolvedCritiques > 1 ? 's' : ''}`}
          >
            !
          </span>
        )}
      </div>
      <div className="document-content__section-body">
        {section.content.split('\n\n').map((paragraph, pIndex) => (
          <p key={pIndex} className="document-content__paragraph">
            {paragraph}
          </p>
        ))}
      </div>
    </section>
  );
});

export const DocumentContent = memo(function DocumentContent({
  draft,
  title,
  onSectionClick,
  className = '',
}: DocumentContentProps) {
  const handleSectionClick = useCallback(
    (sectionId: string) => () => {
      onSectionClick?.(sectionId);
    },
    [onSectionClick]
  );

  return (
    <article className={`document-content ${className}`}>
      <header className="document-content__header">
        <h2 className="document-content__title">{title}</h2>
        <div className="document-content__separator" aria-hidden="true">
          ═══════════════════════════════════════════════════════════
        </div>
      </header>

      <div className="document-content__body">
        {draft.sections.map((section, index) => (
          <Section
            key={section.id}
            section={section}
            index={index}
            onClick={onSectionClick ? handleSectionClick(section.id) : undefined}
          />
        ))}
      </div>
    </article>
  );
});

export default DocumentContent;
