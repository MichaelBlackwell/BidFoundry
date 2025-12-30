/**
 * AgentCardList Component
 *
 * Container component that renders a list of AgentCards with proper layout,
 * virtualization considerations, and accessibility features.
 *
 * Part of the Debate Theater view (Section 4.3 of Frontend Design Document).
 */

import { memo, useCallback, useState, useMemo } from 'react';
import { AgentCard } from '../agent-card';
import type { AgentRuntimeState, Severity, Critique } from '../../types';
import './AgentCardList.css';

export interface AgentCardData extends AgentRuntimeState {
  /** Severity for critiques (red team agents) */
  severity?: Severity;
  /** Suggested remedy if this is a critique */
  suggestedRemedy?: string;
  /** Timestamp when the agent finished */
  timestamp?: Date;
}

export interface AgentCardListProps {
  /** List of agents to display */
  agents: AgentCardData[];
  /** Map of critiques by agent ID for quick lookup */
  critiquesByAgent?: Map<string, Critique>;
  /** Callback when an agent card is expanded */
  onAgentExpand?: (agentId: string) => void;
  /** ID of the currently expanded agent (if any) */
  expandedAgentId?: string | null;
  /** Whether to enable virtualization for large lists */
  virtualize?: boolean;
  /** Empty state message when no agents are present */
  emptyMessage?: string;
  /** Optional additional CSS class */
  className?: string;
}

export const AgentCardList = memo(function AgentCardList({
  agents,
  critiquesByAgent,
  onAgentExpand,
  expandedAgentId,
  emptyMessage = 'No agents active in this phase.',
  className = '',
}: AgentCardListProps) {
  // Track which agents are expanded locally if no external control
  const [localExpandedId, setLocalExpandedId] = useState<string | null>(null);

  const effectiveExpandedId = expandedAgentId !== undefined
    ? expandedAgentId
    : localExpandedId;

  const handleAgentExpand = useCallback(
    (agentId: string) => {
      if (onAgentExpand) {
        onAgentExpand(agentId);
      } else {
        setLocalExpandedId((prev) => (prev === agentId ? null : agentId));
      }
    },
    [onAgentExpand]
  );

  // Sort agents: active agents first, then by category, then by name
  const sortedAgents = useMemo(() => {
    return [...agents].sort((a, b) => {
      // Active states (thinking, typing) come first
      const stateOrder = { typing: 0, thinking: 1, complete: 2, waiting: 3, idle: 4 };
      const aOrder = stateOrder[a.state] ?? 5;
      const bOrder = stateOrder[b.state] ?? 5;

      if (aOrder !== bOrder) return aOrder - bOrder;

      // Then by category (red team agents together, blue team together)
      const categoryOrder = { red: 0, blue: 1, specialist: 2, orchestrator: 3 };
      const aCatOrder = categoryOrder[a.category] ?? 4;
      const bCatOrder = categoryOrder[b.category] ?? 4;

      if (aCatOrder !== bCatOrder) return aCatOrder - bCatOrder;

      // Finally by name
      const aName = a.name ?? '';
      const bName = b.name ?? '';
      return aName.localeCompare(bName);
    });
  }, [agents]);

  // Count active agents for screen reader announcement
  const activeCount = useMemo(
    () => agents.filter((a) => a.state === 'thinking' || a.state === 'typing').length,
    [agents]
  );

  if (agents.length === 0) {
    return (
      <div
        className={`agent-card-list agent-card-list--empty ${className}`}
        role="region"
        aria-label="Agent activity list"
      >
        <p className="agent-card-list__empty-message">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div
      className={`agent-card-list ${className}`}
      role="region"
      aria-label={`Agent activity list, ${agents.length} agents, ${activeCount} active`}
    >
      {/* Screen reader status for active agents */}
      <div className="visually-hidden" role="status" aria-live="polite">
        {activeCount > 0
          ? `${activeCount} agent${activeCount === 1 ? ' is' : 's are'} currently active`
          : 'All agents are waiting or complete'}
      </div>

      <ul className="agent-card-list__list" role="list">
        {sortedAgents.map((agent) => {
          const critique = critiquesByAgent?.get(agent.id);

          return (
            <li key={agent.id} className="agent-card-list__item">
              <AgentCard
                agentId={agent.id}
                name={agent.name}
                role={agent.role}
                category={agent.category}
                state={agent.state}
                content={agent.currentContent}
                target={agent.target}
                severity={critique?.severity ?? agent.severity}
                suggestedRemedy={critique?.suggestedRemedy ?? agent.suggestedRemedy}
                timestamp={critique?.timestamp ? new Date(critique.timestamp) : agent.timestamp}
                onExpand={() => handleAgentExpand(agent.id)}
                isExpanded={effectiveExpandedId === agent.id}
              />
            </li>
          );
        })}
      </ul>
    </div>
  );
});

export default AgentCardList;
