/**
 * SectionList Component
 *
 * Scrollable list of document sections with virtualization support
 * for performance with many sections.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useCallback, useMemo, useRef, useEffect } from 'react';
import { SectionCard } from './SectionCard';
import type { DocumentSection, Critique } from '../../types';
import './SectionList.css';

export interface SectionRevision {
  sectionId: string;
  previousContent: string;
  note?: string;
}

export interface SectionListProps {
  /** Array of document sections to display */
  sections: DocumentSection[];
  /** All critiques for cross-referencing with sections */
  critiques?: Critique[];
  /** Map of section IDs to their previous content for diff display */
  revisions?: SectionRevision[];
  /** IDs of sections currently being revised */
  revisingSectionIds?: string[];
  /** Currently selected section ID */
  selectedSectionId?: string | null;
  /** Callback when a section is clicked */
  onSectionClick?: (sectionId: string) => void;
  /** Empty state message */
  emptyMessage?: string;
  /** Optional additional CSS class */
  className?: string;
}

export const SectionList = memo(function SectionList({
  sections,
  critiques = [],
  revisions = [],
  revisingSectionIds = [],
  selectedSectionId = null,
  onSectionClick,
  emptyMessage = 'No sections available yet.',
  className = '',
}: SectionListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  // Create a map for quick revision lookup
  const revisionMap = useMemo(() => {
    const map = new Map<string, SectionRevision>();
    revisions.forEach((rev) => map.set(rev.sectionId, rev));
    return map;
  }, [revisions]);

  // Create a set for quick revising check
  const revisingSet = useMemo(
    () => new Set(revisingSectionIds),
    [revisingSectionIds]
  );

  // Scroll selected section into view
  useEffect(() => {
    if (selectedSectionId && listRef.current) {
      const selectedElement = listRef.current.querySelector(
        `[data-section-id="${selectedSectionId}"]`
      );
      if (selectedElement) {
        selectedElement.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [selectedSectionId]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (!onSectionClick || sections.length === 0) return;

      const currentIndex = sections.findIndex(
        (s) => s.id === selectedSectionId
      );

      if (event.key === 'ArrowDown') {
        event.preventDefault();
        const nextIndex =
          currentIndex < sections.length - 1 ? currentIndex + 1 : 0;
        onSectionClick(sections[nextIndex].id);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        const prevIndex =
          currentIndex > 0 ? currentIndex - 1 : sections.length - 1;
        onSectionClick(sections[prevIndex].id);
      } else if (event.key === 'Home') {
        event.preventDefault();
        onSectionClick(sections[0].id);
      } else if (event.key === 'End') {
        event.preventDefault();
        onSectionClick(sections[sections.length - 1].id);
      }
    },
    [sections, selectedSectionId, onSectionClick]
  );

  if (sections.length === 0) {
    return (
      <div className={`section-list section-list--empty ${className}`}>
        <p className="section-list__empty-message">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div
      ref={listRef}
      className={`section-list ${className}`}
      role="listbox"
      aria-label="Document sections"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {sections.map((section, index) => {
        const revision = revisionMap.get(section.id);
        const isRevising = revisingSet.has(section.id);
        const isSelected = section.id === selectedSectionId;

        return (
          <div
            key={section.id}
            data-section-id={section.id}
            className="section-list__item"
            role="option"
            aria-selected={isSelected}
          >
            <SectionCard
              section={section}
              critiques={critiques}
              previousContent={revision?.previousContent}
              revisionNote={revision?.note}
              isRevising={isRevising}
              isSelected={isSelected}
              onClick={onSectionClick}
            />
          </div>
        );
      })}
    </div>
  );
});

export default SectionList;
