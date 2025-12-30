/**
 * DisputeCard Component
 *
 * Displays a single dispute between red team and blue team positions,
 * including arbiter notes when available.
 *
 * Based on Section 4.6 of the Frontend Design Document.
 */

import { memo } from 'react';
import type { Dispute } from '../../types';
import './DisputeCard.css';

export interface DisputeCardProps {
  /** The dispute to display */
  dispute: Dispute;
  /** Optional dispute number for display */
  number?: number;
  /** Whether to show expanded details by default */
  expanded?: boolean;
}

export const DisputeCard = memo(function DisputeCard({
  dispute,
  number,
  expanded = true,
}: DisputeCardProps) {
  return (
    <div className="dispute-card" role="article" aria-label={`Dispute: ${dispute.title}`}>
      {/* Header */}
      <div className="dispute-card__header">
        <h4 className="dispute-card__title">
          {number !== undefined && (
            <span className="dispute-card__number">#{number}</span>
          )}
          {dispute.title}
        </h4>
      </div>

      {expanded && (
        <div className="dispute-card__body">
          {/* Red Team Position */}
          <div className="dispute-card__position dispute-card__position--red">
            <div className="dispute-card__position-header">
              <span className="dispute-card__team-icon" aria-hidden="true">
                &#x1F534;
              </span>
              <span className="dispute-card__team-label">Red Team Position:</span>
            </div>
            <p className="dispute-card__position-content">
              "{dispute.redPosition}"
            </p>
          </div>

          {/* Blue Team Position */}
          <div className="dispute-card__position dispute-card__position--blue">
            <div className="dispute-card__position-header">
              <span className="dispute-card__team-icon" aria-hidden="true">
                &#x1F535;
              </span>
              <span className="dispute-card__team-label">Blue Team Position:</span>
            </div>
            <p className="dispute-card__position-content">
              "{dispute.bluePosition}"
            </p>
          </div>

          {/* Arbiter Note (if available) */}
          {dispute.arbiterNote && (
            <div className="dispute-card__arbiter">
              <div className="dispute-card__arbiter-header">
                <span className="dispute-card__arbiter-icon" aria-hidden="true">
                  &#x2696;&#xFE0F;
                </span>
                <span className="dispute-card__arbiter-label">Arbiter Note:</span>
              </div>
              <p className="dispute-card__arbiter-content">
                "{dispute.arbiterNote}"
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
});

export default DisputeCard;
