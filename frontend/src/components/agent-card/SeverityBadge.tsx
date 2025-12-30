/**
 * SeverityBadge Component
 *
 * Displays a severity indicator for critiques.
 * Colors and styling convey the importance level.
 */

import { memo } from 'react';
import type { Severity } from '../../types';
import './SeverityBadge.css';

interface SeverityBadgeProps {
  /** Severity level */
  severity: Severity;
  /** Whether to show the full label or just icon */
  showLabel?: boolean;
  /** Size variant */
  size?: 'sm' | 'md';
  /** Additional CSS class name */
  className?: string;
}

/**
 * Get the label text for each severity level
 */
function getSeverityLabel(severity: Severity): string {
  switch (severity) {
    case 'critical':
      return 'Critical';
    case 'major':
      return 'Major';
    case 'minor':
      return 'Minor';
    default:
      return severity;
  }
}

/**
 * Get accessibility description for severity
 */
function getSeverityDescription(severity: Severity): string {
  switch (severity) {
    case 'critical':
      return 'Critical severity - requires immediate attention';
    case 'major':
      return 'Major severity - should be addressed';
    case 'minor':
      return 'Minor severity - low priority';
    default:
      return `${severity} severity`;
  }
}

export const SeverityBadge = memo(function SeverityBadge({
  severity,
  showLabel = true,
  size = 'md',
  className = '',
}: SeverityBadgeProps) {
  const label = getSeverityLabel(severity);
  const description = getSeverityDescription(severity);

  return (
    <span
      className={`severity-badge severity-badge--${severity} severity-badge--${size} ${className}`}
      role="status"
      aria-label={description}
    >
      <span className="severity-badge__indicator" aria-hidden="true" />
      {showLabel && <span className="severity-badge__label">{label}</span>}
    </span>
  );
});

export default SeverityBadge;
