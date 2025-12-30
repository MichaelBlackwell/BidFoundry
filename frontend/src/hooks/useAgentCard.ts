/**
 * useAgentCard Hook
 *
 * Provides real-time agent state and content updates for AgentCard components.
 * Connects to the WebSocket provider and Swarm store.
 */

import { useCallback, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useSwarmStore, selectAgentById } from '../stores/swarmStore';
import type { AgentCardProps } from '../components/agent-card';
import type { AgentRuntimeState, Critique } from '../types';

interface UseAgentCardOptions {
  /** Agent ID to track */
  agentId: string;
}

interface UseAgentCardResult {
  /** Props to spread onto AgentCard component */
  cardProps: Omit<AgentCardProps, 'onExpand' | 'isExpanded' | 'className'>;
  /** Current agent state from store */
  agentState: AgentRuntimeState | undefined;
  /** Latest critique from this agent (if any) */
  latestCritique: Critique | undefined;
  /** Whether agent is currently active */
  isActive: boolean;
}

/**
 * Hook to get AgentCard props from the swarm store state
 */
export function useAgentCard({ agentId }: UseAgentCardOptions): UseAgentCardResult {
  // Get agent state from store
  const agentState = useSwarmStore(selectAgentById(agentId));

  // Get critiques from this agent
  const critiques = useSwarmStore((state) => state.critiques);
  const latestCritique = useMemo(
    () => critiques.filter((c) => c.agentId === agentId).pop(),
    [critiques, agentId]
  );

  // Determine if agent is actively working
  const isActive = agentState?.state === 'thinking' || agentState?.state === 'typing';

  // Build card props from agent state
  const cardProps = useMemo((): UseAgentCardResult['cardProps'] => {
    if (!agentState) {
      return {
        agentId,
        name: 'Unknown Agent',
        role: '',
        category: 'blue',
        state: 'idle',
        content: null,
      };
    }

    return {
      agentId,
      name: agentState.name,
      role: agentState.role,
      category: agentState.category,
      state: agentState.state,
      content: agentState.currentContent,
      target: agentState.target ?? undefined,
      severity: latestCritique?.severity,
      suggestedRemedy: latestCritique?.suggestedRemedy,
      timestamp: latestCritique?.timestamp ? new Date(latestCritique.timestamp) : undefined,
    };
  }, [agentId, agentState, latestCritique]);

  return {
    cardProps,
    agentState,
    latestCritique,
    isActive,
  };
}

/**
 * Hook to get all agent cards for a specific category
 */
export function useAgentCardsByCategory(category: AgentRuntimeState['category']) {
  const agents = useSwarmStore(
    useShallow((state) =>
      Object.values(state.agents).filter((a) => a.category === category)
    )
  );

  return agents;
}

/**
 * Hook to get all active (thinking/typing) agents
 */
export function useActiveAgents() {
  const agents = useSwarmStore(
    useShallow((state) =>
      Object.values(state.agents).filter(
        (a) => a.state === 'thinking' || a.state === 'typing'
      )
    )
  );

  return agents;
}

/**
 * Hook to manage expanded state for agent cards
 */
export function useAgentCardExpansion() {
  const expandedAgentId = useSwarmStore(() => {
    // This would need to be added to the UI store
    // For now, returning null as a placeholder
    return null as string | null;
  });

  const setExpandedAgentId = useCallback((agentId: string | null) => {
    // This would need to be implemented in the UI store
    console.log('Setting expanded agent:', agentId);
  }, []);

  const toggleExpanded = useCallback(
    (agentId: string) => {
      setExpandedAgentId(expandedAgentId === agentId ? null : agentId);
    },
    [expandedAgentId, setExpandedAgentId]
  );

  return {
    expandedAgentId,
    setExpandedAgentId,
    toggleExpanded,
    isExpanded: (agentId: string) => expandedAgentId === agentId,
  };
}

export default useAgentCard;
