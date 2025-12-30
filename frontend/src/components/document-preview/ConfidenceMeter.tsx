/**
 * ConfidenceMeter Component
 *
 * Visual progress bar showing overall document confidence level.
 *
 * Based on Section 4.5 of the Frontend Design Document.
 */

import { memo, useMemo } from 'react';
import './ConfidenceMeter.css';

export interface ConfidenceMeterProps {
  /** Confidence percentage (0-100) */
  confidence: number;
  /** Whether to show the percentage label */
  showLabel?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Optional additional CSS class */
  className?: string;
}

export const ConfidenceMeter = memo(function ConfidenceMeter({
  confidence,
  showLabel = true,
  size = 'md',
  className = '',
}: ConfidenceMeterProps) {
  // Clamp confidence to 0-100
  const clampedConfidence = Math.min(100, Math.max(0, confidence));

  // Determine confidence level for styling
  const level = useMemo(() => {
    if (clampedConfidence >= 85) return 'high';
    if (clampedConfidence >= 70) return 'medium';
    return 'low';
  }, [clampedConfidence]);

  // Calculate filled segments for the visual bar
  const segments = useMemo(() => {
    const totalSegments = 10;
    const filledSegments = Math.round((clampedConfidence / 100) * totalSegments);
    return { filled: filledSegments, total: totalSegments };
  }, [clampedConfidence]);

  return (
    <div
      className={`confidence-meter confidence-meter--${size} confidence-meter--${level} ${className}`}
      role="meter"
      aria-valuenow={clampedConfidence}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Confidence: ${clampedConfidence}%`}
    >
      {showLabel && (
        <span className="confidence-meter__label">Confidence:</span>
      )}
      <div className="confidence-meter__bar" aria-hidden="true">
        {Array.from({ length: segments.total }).map((_, index) => (
          <span
            key={index}
            className={`confidence-meter__segment ${
              index < segments.filled
                ? 'confidence-meter__segment--filled'
                : 'confidence-meter__segment--empty'
            }`}
          />
        ))}
      </div>
      <span className="confidence-meter__value">{clampedConfidence}%</span>
    </div>
  );
});

export default ConfidenceMeter;
