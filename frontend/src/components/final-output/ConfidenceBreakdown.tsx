/**
 * ConfidenceBreakdown Component
 *
 * Displays a breakdown of confidence scores for each document section,
 * with visual progress bars and warning indicators.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import React, { memo, useMemo } from 'react';
import type { ConfidenceReport } from '../../types';
import './ConfidenceBreakdown.css';

export interface ConfidenceBreakdownProps {
  /** Confidence report with overall and per-section scores */
  confidence: ConfidenceReport;
  /** Section titles for display */
  sectionTitles?: Record<string, string>;
  /** Callback when a section is clicked */
  onSectionClick?: (sectionId: string) => void;
  /** Optional additional CSS class */
  className?: string;
}

interface ConfidenceLevel {
  level: 'high' | 'medium' | 'low';
  label: string;
}

function getConfidenceLevel(score: number): ConfidenceLevel {
  if (score >= 85) return { level: 'high', label: 'High' };
  if (score >= 70) return { level: 'medium', label: 'Medium' };
  return { level: 'low', label: 'Low' };
}

function renderSegmentBar(score: number): React.ReactElement {
  const totalSegments = 10;
  const filledSegments = Math.round((score / 100) * totalSegments);
  const level = getConfidenceLevel(score).level;

  return (
    <div className="confidence-breakdown__bar" aria-hidden="true">
      {Array.from({ length: totalSegments }).map((_, index) => (
        <span
          key={index}
          className={`confidence-breakdown__segment confidence-breakdown__segment--${level} ${
            index < filledSegments
              ? 'confidence-breakdown__segment--filled'
              : 'confidence-breakdown__segment--empty'
          }`}
        />
      ))}
    </div>
  );
}

export const ConfidenceBreakdown = memo(function ConfidenceBreakdown({
  confidence,
  sectionTitles = {},
  onSectionClick,
  className = '',
}: ConfidenceBreakdownProps) {
  const overallLevel = useMemo(
    () => getConfidenceLevel(confidence.overall),
    [confidence.overall]
  );

  const sortedSections = useMemo(() => {
    return Object.entries(confidence.sections).sort(([, a], [, b]) => b - a);
  }, [confidence.sections]);

  const handleSectionClick = (sectionId: string) => () => {
    onSectionClick?.(sectionId);
  };

  const handleKeyDown = (sectionId: string) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSectionClick?.(sectionId);
    }
  };

  return (
    <div className={`confidence-breakdown ${className}`}>
      <h3 className="confidence-breakdown__title">Confidence Breakdown</h3>

      {/* Overall Confidence */}
      <div
        className={`confidence-breakdown__overall confidence-breakdown__overall--${overallLevel.level}`}
        role="meter"
        aria-valuenow={confidence.overall}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Overall confidence: ${confidence.overall}%`}
      >
        <div className="confidence-breakdown__overall-header">
          <span className="confidence-breakdown__overall-label">Overall:</span>
          <span className="confidence-breakdown__overall-value">
            {confidence.overall}%
          </span>
        </div>
        {renderSegmentBar(confidence.overall)}
      </div>

      {/* Section Breakdown */}
      <div className="confidence-breakdown__sections">
        {sortedSections.map(([sectionId, score]) => {
          const level = getConfidenceLevel(score);
          const title = sectionTitles[sectionId] || sectionId;
          const isClickable = !!onSectionClick;

          return (
            <div
              key={sectionId}
              className={`confidence-breakdown__section confidence-breakdown__section--${level.level} ${
                isClickable ? 'confidence-breakdown__section--clickable' : ''
              }`}
              role={isClickable ? 'button' : 'meter'}
              aria-valuenow={score}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`${title}: ${score}%`}
              tabIndex={isClickable ? 0 : undefined}
              onClick={isClickable ? handleSectionClick(sectionId) : undefined}
              onKeyDown={isClickable ? handleKeyDown(sectionId) : undefined}
            >
              <div className="confidence-breakdown__section-header">
                <span className="confidence-breakdown__section-title">
                  {title}:
                </span>
                <span className="confidence-breakdown__section-value">
                  {score}%
                  {level.level === 'low' && (
                    <span
                      className="confidence-breakdown__warning"
                      title="Low confidence"
                      aria-label="Warning: Low confidence"
                    >
                      !
                    </span>
                  )}
                </span>
              </div>
              {renderSegmentBar(score)}
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default ConfidenceBreakdown;
