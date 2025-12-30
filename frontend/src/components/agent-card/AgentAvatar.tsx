/**
 * AgentAvatar Component
 *
 * Displays the agent's avatar with category-specific styling
 * and state indicators.
 */

import { memo } from 'react';
import type { AgentCategory, AgentState } from '../../types';
import './AgentAvatar.css';

interface AgentAvatarProps {
  /** Agent category determines color and icon */
  category: AgentCategory;
  /** Current agent state affects visual appearance */
  state: AgentState;
  /** Agent name for accessibility */
  name: string;
  /** Size of the avatar */
  size?: 'sm' | 'md' | 'lg';
  /** Additional CSS class name */
  className?: string;
}

/**
 * Get the icon/emoji for each category
 */
function getCategoryIcon(category: AgentCategory): string {
  switch (category) {
    case 'blue':
      return '🔵';
    case 'red':
      return '🔴';
    case 'specialist':
      return '🟣';
    case 'orchestrator':
      return '⚖️';
    default:
      return '⚪';
  }
}

/**
 * Get the category label for accessibility
 */
function getCategoryLabel(category: AgentCategory): string {
  switch (category) {
    case 'blue':
      return 'Blue Team';
    case 'red':
      return 'Red Team';
    case 'specialist':
      return 'Specialist';
    case 'orchestrator':
      return 'Arbiter';
    default:
      return 'Agent';
  }
}

export const AgentAvatar = memo(function AgentAvatar({
  category,
  state,
  name,
  size = 'md',
  className = '',
}: AgentAvatarProps) {
  const icon = getCategoryIcon(category);
  const categoryLabel = getCategoryLabel(category);

  return (
    <div
      className={`agent-avatar agent-avatar--${size} agent-avatar--${category} agent-avatar--${state} ${className}`}
      role="img"
      aria-label={`${categoryLabel} agent: ${name}`}
    >
      <span className="agent-avatar__icon" aria-hidden="true">
        {icon}
      </span>
      {(state === 'thinking' || state === 'typing') && (
        <span className="agent-avatar__activity-indicator" aria-hidden="true" />
      )}
    </div>
  );
});

export default AgentAvatar;
