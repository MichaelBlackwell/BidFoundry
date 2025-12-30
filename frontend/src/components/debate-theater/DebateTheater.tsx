/**
 * DebateTheater Component
 *
 * The centerpiece of the generation view: real-time visualization of agent debate.
 * Displays the current phase, agent activity, and round summaries.
 *
 * Based on Section 4.3 of the Frontend Design Document.
 */

import { memo, useMemo, useCallback, useState } from 'react';
import { PhaseHeader } from './PhaseHeader';
import { AgentCardList, type AgentCardData } from './AgentCardList';
import { RoundSummary, type CritiqueCounts } from './RoundSummary';
import type { Phase, AgentRuntimeState, Critique, Response } from '../../types';
import './DebateTheater.css';

export interface DebateTheaterProps {
  /** Current round number (1-indexed) */
  round: number;
  /** Total number of rounds */
  totalRounds: number;
  /** Current phase of the debate */
  phase: Phase;
  /** Map of agent states by agent ID */
  agents: Record<string, AgentRuntimeState>;
  /** List of critiques raised during the debate */
  critiques: Critique[];
  /** List of responses to critiques */
  responses: Response[];
  /** Whether the debate is currently live/active */
  isLive: boolean;
  /** Callback when user requests to pause the generation */
  onPause?: () => void;
  /** Callback when user requests to resume the generation */
  onResume?: () => void;
  /** Callback when user requests to skip to the next round */
  onSkipRound?: () => void;
  /** Whether generation is currently paused */
  isPaused?: boolean;
  /** Optional additional CSS class */
  className?: string;
}

export const DebateTheater = memo(function DebateTheater({
  round,
  totalRounds,
  phase,
  agents,
  critiques,
  responses,
  isLive,
  onPause,
  onResume,
  onSkipRound,
  isPaused = false,
  className = '',
}: DebateTheaterProps) {
  const [expandedAgentId, setExpandedAgentId] = useState<string | null>(null);

  // Convert agent map to array with enhanced data
  const agentList = useMemo((): AgentCardData[] => {
    return Object.values(agents).map((agent) => {
      // Find the latest critique from this agent in the current round
      const agentCritique = critiques.find(
        (c) => c.agentId === agent.id && c.round === round
      );

      return {
        ...agent,
        severity: agentCritique?.severity,
        suggestedRemedy: agentCritique?.suggestedRemedy,
        timestamp: agentCritique?.timestamp,
      } as AgentCardData;
    });
  }, [agents, critiques, round]);

  // Filter agents based on current phase
  const visibleAgents = useMemo(() => {
    // During red-attack, show red team agents prominently
    // During blue-defense, show blue team agents
    // During synthesis, show orchestrator/arbiter
    // During blue-build, show blue team agents

    const phaseAgentFilter: Record<Phase, AgentRuntimeState['category'][]> = {
      'blue-build': ['blue', 'specialist'],
      'red-attack': ['red'],
      'blue-defense': ['blue', 'specialist'],
      'synthesis': ['orchestrator'],
    };

    const allowedCategories = phaseAgentFilter[phase] || [];

    // During active phases, only show relevant agents
    // But also include any agent that is currently active (typing/thinking)
    return agentList.filter(
      (agent) =>
        allowedCategories.includes(agent.category) ||
        agent.state === 'typing' ||
        agent.state === 'thinking'
    );
  }, [agentList, phase]);

  // Create critique map for quick lookup
  const critiquesByAgent = useMemo(() => {
    const map = new Map<string, Critique>();
    critiques
      .filter((c) => c.round === round)
      .forEach((c) => {
        // Keep the latest critique per agent
        const existing = map.get(c.agentId);
        if (!existing || c.timestamp > existing.timestamp) {
          map.set(c.agentId, c);
        }
      });
    return map;
  }, [critiques, round]);

  // Calculate critique counts for the current round
  const critiqueCounts = useMemo((): CritiqueCounts => {
    const roundCritiques = critiques.filter((c) => c.round === round);
    return {
      total: roundCritiques.length,
      critical: roundCritiques.filter((c) => c.severity === 'critical').length,
      major: roundCritiques.filter((c) => c.severity === 'major').length,
      minor: roundCritiques.filter((c) => c.severity === 'minor').length,
    };
  }, [critiques, round]);

  // Count agents that have completed their work this round
  const agentProgress = useMemo(() => {
    const roundAgents = visibleAgents;
    const completed = roundAgents.filter(
      (a) => a.state === 'complete' || a.state === 'waiting'
    ).length;
    return {
      reporting: completed,
      total: roundAgents.length,
    };
  }, [visibleAgents]);

  // Handle agent expansion
  const handleAgentExpand = useCallback((agentId: string) => {
    setExpandedAgentId((prev) => (prev === agentId ? null : agentId));
  }, []);

  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === ' ' && !e.repeat) {
        e.preventDefault();
        if (isPaused && onResume) {
          onResume();
        } else if (onPause) {
          onPause();
        }
      }
    },
    [isPaused, onPause, onResume]
  );

  return (
    <section
      className={`debate-theater ${isPaused ? 'debate-theater--paused' : ''} ${className}`}
      role="region"
      aria-label="Debate Theater - Real-time agent activity"
      aria-live="polite"
      aria-atomic="false"
      data-panel="debate-theater"
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Phase Header */}
      <PhaseHeader
        phase={phase}
        round={round}
        totalRounds={totalRounds}
        isLive={isLive && !isPaused}
      />

      {/* Agent Activity Area */}
      <div className="debate-theater__content">
        <AgentCardList
          agents={visibleAgents}
          critiquesByAgent={critiquesByAgent}
          onAgentExpand={handleAgentExpand}
          expandedAgentId={expandedAgentId}
          emptyMessage={getEmptyMessage(phase)}
        />
      </div>

      {/* Round Summary */}
      <RoundSummary
        critiques={critiqueCounts}
        agentsReporting={agentProgress.reporting}
        totalAgents={agentProgress.total}
        isActive={isLive && !isPaused}
      />

      {/* Control Overlay when paused */}
      {isPaused && (
        <div className="debate-theater__paused-overlay" role="status">
          <div className="debate-theater__paused-message">
            <span className="debate-theater__paused-icon" aria-hidden="true">
              ⏸
            </span>
            <span>Generation Paused</span>
            {onResume && (
              <button
                className="debate-theater__resume-btn"
                onClick={onResume}
                type="button"
              >
                Resume
              </button>
            )}
          </div>
        </div>
      )}

      {/* Keyboard hint */}
      <div className="debate-theater__keyboard-hint">
        Press <kbd>Space</kbd> to {isPaused ? 'resume' : 'pause'}
      </div>
    </section>
  );
});

/**
 * Get an appropriate empty message based on the current phase
 */
function getEmptyMessage(phase: Phase): string {
  switch (phase) {
    case 'blue-build':
      return 'Waiting for blue team agents to begin building...';
    case 'red-attack':
      return 'Waiting for red team agents to begin critique...';
    case 'blue-defense':
      return 'Waiting for blue team agents to respond...';
    case 'synthesis':
      return 'Waiting for arbiter to synthesize results...';
    default:
      return 'No agents active in this phase.';
  }
}

export default DebateTheater;
