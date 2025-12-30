/**
 * AgentCard Component
 *
 * Displays an individual agent's activity during the debate process.
 * Supports multiple visual states: idle, thinking, typing, complete, waiting.
 *
 * Based on Section 4.4 of the Frontend Design Document.
 */

import { memo, useCallback } from 'react';
import type { AgentCategory, AgentState, Severity } from '../../types';
import { AgentAvatar } from './AgentAvatar';
import { SeverityBadge } from './SeverityBadge';
import { StreamingContent } from './StreamingContent';
import { useUIStore } from '../../stores/uiStore';
import './AgentCard.css';

export interface AgentCardProps {
  /** Unique agent identifier */
  agentId: string;
  /** Display name of the agent */
  name: string;
  /** Agent's role description */
  role: string;
  /** Agent category (blue, red, specialist, orchestrator) */
  category: AgentCategory;
  /** Current agent state */
  state: AgentState;
  /** Content being displayed (streams in real-time for 'typing' state) */
  content: string | null;
  /** Target section being critiqued/responded to */
  target?: string | null;
  /** Severity level for critiques */
  severity?: Severity;
  /** Suggested remedy for the issue */
  suggestedRemedy?: string;
  /** Timestamp when the agent finished */
  timestamp?: Date;
  /** Callback when card is expanded/clicked */
  onExpand?: () => void;
  /** Whether the card is currently expanded */
  isExpanded?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Get the status text for the current agent state
 */
function getStateText(state: AgentState): string {
  switch (state) {
    case 'thinking':
      return 'Analyzing...';
    case 'typing':
      return 'Responding...';
    case 'waiting':
      return 'Waiting for round...';
    case 'idle':
      return 'Idle';
    case 'complete':
      return '';
    default:
      return '';
  }
}

/**
 * Format timestamp for display
 */
function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: false,
  });
}

export const AgentCard = memo(function AgentCard({
  agentId,
  name,
  role,
  category,
  state,
  content,
  target,
  severity,
  suggestedRemedy,
  timestamp,
  onExpand,
  isExpanded = false,
  className = '',
}: AgentCardProps) {
  const autoScrollEnabled = useUIStore((s) => s.autoScrollEnabled);

  const handleClick = useCallback(() => {
    onExpand?.();
  }, [onExpand]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onExpand?.();
      }
    },
    [onExpand]
  );

  const stateText = getStateText(state);
  const hasContent = content && content.length > 0;
  const isInteractive = state === 'complete' && onExpand;

  return (
    <article
      className={`agent-card agent-card--${state} agent-card--${category} ${
        isExpanded ? 'agent-card--expanded' : ''
      } ${className}`}
      data-agent-id={agentId}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onClick={isInteractive ? handleClick : undefined}
      onKeyDown={isInteractive ? handleKeyDown : undefined}
      aria-expanded={isInteractive ? isExpanded : undefined}
      aria-label={`${name} - ${role}`}
    >
      {/* Header */}
      <header className="agent-card__header">
        <div className="agent-card__identity">
          <AgentAvatar
            category={category}
            state={state}
            name={name}
          />
          <div className="agent-card__name-group">
            <h3 className="agent-card__name">{name}</h3>
            {role && <span className="agent-card__role">{role}</span>}
          </div>
        </div>
        {severity && <SeverityBadge severity={severity} />}
      </header>

      {/* Divider */}
      <div className="agent-card__divider" />

      {/* Target Section */}
      {target && (
        <div className="agent-card__target">
          <span className="agent-card__target-label">TARGET:</span>
          <span className="agent-card__target-value">{target}</span>
        </div>
      )}

      {/* Content */}
      <div className="agent-card__content">
        {state === 'thinking' && (
          <div className="agent-card__thinking" role="status" aria-live="polite">
            <span className="agent-card__thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </span>
            <span className="agent-card__state-text">{stateText}</span>
          </div>
        )}

        {state === 'waiting' && (
          <div className="agent-card__waiting" role="status">
            <span className="agent-card__state-text">{stateText}</span>
          </div>
        )}

        {state === 'idle' && !hasContent && (
          <div className="agent-card__idle" role="status">
            <span className="agent-card__state-text">{stateText}</span>
          </div>
        )}

        {(state === 'typing' || state === 'complete' || hasContent) && (
          <StreamingContent
            content={content || ''}
            isStreaming={state === 'typing'}
            autoScroll={autoScrollEnabled}
          />
        )}
      </div>

      {/* Suggested Remedy */}
      {suggestedRemedy && state === 'complete' && (
        <div className="agent-card__remedy">
          <span className="agent-card__remedy-label">SUGGESTED REMEDY:</span>
          <p className="agent-card__remedy-text">{suggestedRemedy}</p>
        </div>
      )}

      {/* Footer with timestamp */}
      {timestamp && state === 'complete' && (
        <footer className="agent-card__footer">
          <time
            className="agent-card__timestamp"
            dateTime={timestamp.toISOString()}
          >
            {formatTimestamp(timestamp)}
          </time>
        </footer>
      )}

      {/* State indicator for screen readers */}
      <span className="visually-hidden" role="status" aria-live="polite">
        {name} is {state}
        {state === 'complete' && hasContent ? ': ' + content?.slice(0, 100) : ''}
      </span>
    </article>
  );
});

export default AgentCard;
