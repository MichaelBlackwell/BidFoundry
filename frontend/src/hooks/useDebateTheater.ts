/**
 * useDebateTheater Hook
 *
 * Provides a unified interface for the DebateTheater component,
 * connecting to the swarm store and WebSocket for real-time updates.
 *
 * This hook abstracts away the complexity of state management and
 * WebSocket events, providing a simple API for the DebateTheater component.
 */

import { useMemo, useCallback } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { useSwarmStore, selectAgents, selectCritiqueSummary } from '../stores/swarmStore';
import { useSwarmWebSocket } from './useSwarmWebSocket';
import type { Phase, AgentRuntimeState, Critique, Response } from '../types';

export interface UseDebateTheaterReturn {
  /** Current round number (1-indexed) */
  round: number;
  /** Total number of rounds configured */
  totalRounds: number;
  /** Current phase of the debate */
  phase: Phase;
  /** Map of agent states by agent ID */
  agents: Record<string, AgentRuntimeState>;
  /** List of critiques raised during the debate */
  critiques: Critique[];
  /** List of responses to critiques */
  responses: Response[];
  /** Whether the debate is currently live/running */
  isLive: boolean;
  /** Whether generation is paused */
  isPaused: boolean;
  /** Pause the generation */
  pause: () => void;
  /** Resume the generation */
  resume: () => void;
  /** Cancel the generation */
  cancel: () => void;
  /** Critique counts by severity for the current round */
  critiqueSummary: {
    total: number;
    critical: number;
    major: number;
    minor: number;
    accepted: number;
    rebutted: number;
    pending: number;
  };
  /** WebSocket connection status */
  connectionStatus: string;
}

export function useDebateTheater(): UseDebateTheaterReturn {
  // Get state from swarm store
  const currentRound = useSwarmStore((s) => s.currentRound);
  const totalRounds = useSwarmStore((s) => s.totalRounds);
  const currentPhase = useSwarmStore((s) => s.currentPhase);
  const agents = useSwarmStore((s) => s.agents);
  const critiques = useSwarmStore((s) => s.critiques);
  const responses = useSwarmStore((s) => s.responses);
  const status = useSwarmStore((s) => s.status);
  const critiqueSummary = useSwarmStore(useShallow(selectCritiqueSummary));

  // Get WebSocket controls
  const {
    pauseGeneration,
    resumeGeneration,
    cancelGeneration,
    connectionStatus,
    isGenerating,
  } = useSwarmWebSocket();

  // Computed state
  const isLive = status === 'running';
  const isPaused = status === 'configuring'; // We'll use configuring as paused state for now

  // Memoized callbacks
  const pause = useCallback(() => {
    pauseGeneration();
  }, [pauseGeneration]);

  const resume = useCallback(() => {
    resumeGeneration();
  }, [resumeGeneration]);

  const cancel = useCallback(() => {
    cancelGeneration();
  }, [cancelGeneration]);

  return {
    round: currentRound,
    totalRounds,
    phase: currentPhase,
    agents,
    critiques,
    responses,
    isLive,
    isPaused,
    pause,
    resume,
    cancel,
    critiqueSummary,
    connectionStatus,
  };
}

/**
 * Hook for filtering critiques by various criteria
 */
export function useCritiqueFilters() {
  const critiques = useSwarmStore((s) => s.critiques);
  const currentRound = useSwarmStore((s) => s.currentRound);

  const currentRoundCritiques = useMemo(
    () => critiques.filter((c) => c.round === currentRound),
    [critiques, currentRound]
  );

  const unresolvedCritiques = useMemo(
    () => critiques.filter((c) => c.status === 'pending' || !c.status),
    [critiques]
  );

  const criticalCritiques = useMemo(
    () => critiques.filter((c) => c.severity === 'critical'),
    [critiques]
  );

  const getCritiquesForAgent = useCallback(
    (agentId: string) => critiques.filter((c) => c.agentId === agentId),
    [critiques]
  );

  const getCritiquesForSection = useCallback(
    (sectionId: string) => critiques.filter((c) => c.target === sectionId),
    [critiques]
  );

  return {
    allCritiques: critiques,
    currentRoundCritiques,
    unresolvedCritiques,
    criticalCritiques,
    getCritiquesForAgent,
    getCritiquesForSection,
  };
}

/**
 * Hook for tracking agent activity during debate
 */
export function useAgentActivity() {
  const agents = useSwarmStore(useShallow(selectAgents));
  const currentPhase = useSwarmStore((s) => s.currentPhase);

  const activeAgents = useMemo(
    () => agents.filter((a) => a.state === 'thinking' || a.state === 'typing'),
    [agents]
  );

  const completedAgents = useMemo(
    () => agents.filter((a) => a.state === 'complete'),
    [agents]
  );

  const waitingAgents = useMemo(
    () => agents.filter((a) => a.state === 'waiting' || a.state === 'idle'),
    [agents]
  );

  const agentsByCategory = useMemo(() => {
    return {
      blue: agents.filter((a) => a.category === 'blue'),
      red: agents.filter((a) => a.category === 'red'),
      specialist: agents.filter((a) => a.category === 'specialist'),
      orchestrator: agents.filter((a) => a.category === 'orchestrator'),
    };
  }, [agents]);

  const phaseRelevantAgents = useMemo(() => {
    switch (currentPhase) {
      case 'blue-build':
      case 'blue-defense':
        return [...agentsByCategory.blue, ...agentsByCategory.specialist];
      case 'red-attack':
        return agentsByCategory.red;
      case 'synthesis':
        return agentsByCategory.orchestrator;
      default:
        return agents;
    }
  }, [currentPhase, agentsByCategory, agents]);

  return {
    allAgents: agents,
    activeAgents,
    completedAgents,
    waitingAgents,
    agentsByCategory,
    phaseRelevantAgents,
    activeCount: activeAgents.length,
    completedCount: completedAgents.length,
    totalCount: agents.length,
  };
}

export default useDebateTheater;
