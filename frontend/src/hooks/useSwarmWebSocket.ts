/**
 * useSwarmWebSocket Hook
 *
 * Bridges WebSocket events to the swarmStore, providing a unified interface
 * for real-time document generation updates.
 *
 * This hook:
 * - Subscribes to all relevant server events
 * - Updates the swarmStore accordingly
 * - Provides methods to send client events
 * - Handles agent state transitions
 */

import { useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from '../providers/EnhancedWebSocketProvider';
import { useSwarmStore } from '../stores/swarmStore';
import type {
  ServerEventType,
  ServerEvents,
  RoundStartPayload,
  RoundEndPayload,
  PhaseChangePayload,
  AgentRegisteredPayload,
  AgentThinkingPayload,
  AgentStreamingPayload,
  AgentCompletePayload,
  DraftUpdatePayload,
  ConfidenceUpdatePayload,
  EscalationTriggeredPayload,
  GenerationCompletePayload,
  GenerationErrorPayload,
  GenerationStartPayload,
  ClientEvents,
} from '../types/websocket';
import type { AgentRuntimeState, DocumentRequest, DocumentDraft } from '../types';

interface UseSwarmWebSocketOptions {
  /** Request ID for the current generation session */
  requestId?: string;
  /** Called when generation completes successfully */
  onComplete?: (result: GenerationCompletePayload['result']) => void;
  /** Called when an error occurs */
  onError?: (error: GenerationErrorPayload) => void;
  /** Called when escalation is triggered */
  onEscalation?: (escalation: EscalationTriggeredPayload) => void;
}

interface UseSwarmWebSocketReturn {
  /** Start a new generation session */
  startGeneration: (requestId: string, request: DocumentRequest) => void;
  /** Pause the current generation */
  pauseGeneration: () => void;
  /** Resume a paused generation */
  resumeGeneration: () => void;
  /** Cancel the current generation */
  cancelGeneration: () => void;
  /** Current WebSocket connection status */
  connectionStatus: ReturnType<typeof useWebSocket>['status'];
  /** Connection ID from the server */
  connectionId: string | null;
  /** Whether generation is currently active */
  isGenerating: boolean;
}

export function useSwarmWebSocket(
  options: UseSwarmWebSocketOptions = {}
): UseSwarmWebSocketReturn {
  const { requestId, onComplete, onError, onEscalation } = options;
  const { status: connectionStatus, connectionId, send, subscribe } = useWebSocket();

  // Get store actions
  const setRound = useSwarmStore((s) => s.setRound);
  const setPhase = useSwarmStore((s) => s.setPhase);
  const updateAgent = useSwarmStore((s) => s.updateAgent);
  const addDraft = useSwarmStore((s) => s.addDraft);
  const updateDraft = useSwarmStore((s) => s.updateDraft);
  const addCritique = useSwarmStore((s) => s.addCritique);
  const addResponse = useSwarmStore((s) => s.addResponse);
  const setResult = useSwarmStore((s) => s.setResult);
  const setEscalation = useSwarmStore((s) => s.setEscalation);
  const setError = useSwarmStore((s) => s.setError);
  const setStatus = useSwarmStore((s) => s.setStatus);
  const generationStatus = useSwarmStore((s) => s.status);
  const drafts = useSwarmStore((s) => s.drafts);

  // Track current request ID
  const currentRequestIdRef = useRef<string | undefined>(requestId);
  currentRequestIdRef.current = requestId;

  // Track if this is the first draft
  const isFirstDraftRef = useRef(true);

  // Reset first draft flag when generation starts
  useEffect(() => {
    if (generationStatus === 'running') {
      isFirstDraftRef.current = drafts.length === 0;
    }
  }, [generationStatus, drafts.length]);

  // ============================================================================
  // Event Handlers
  // ============================================================================

  const handleRoundStart = useCallback(
    (payload: RoundStartPayload) => {
      setRound(payload.round, payload.totalRounds);
      setPhase(payload.phase);

      // Register agents with initial state
      payload.agents.forEach((agent) => {
        updateAgent(agent.id, {
          ...agent,
          state: 'idle',
          currentContent: null,
          target: null,
        } as AgentRuntimeState);
      });
    },
    [setRound, setPhase, updateAgent]
  );

  const handleRoundEnd = useCallback(
    (_payload: RoundEndPayload) => {
      // Reset all agents to waiting state at end of round
      const agents = useSwarmStore.getState().agents;
      Object.keys(agents).forEach((agentId) => {
        updateAgent(agentId, { state: 'waiting', currentContent: null });
      });
    },
    [updateAgent]
  );

  const handlePhaseChange = useCallback(
    (payload: PhaseChangePayload) => {
      setPhase(payload.phase);

      // Reset agent states for new phase
      const agents = useSwarmStore.getState().agents;
      Object.keys(agents).forEach((agentId) => {
        updateAgent(agentId, { state: 'idle', currentContent: null });
      });
    },
    [setPhase, updateAgent]
  );

  const handleAgentRegistered = useCallback(
    (payload: AgentRegisteredPayload) => {
      payload.agents.forEach((agent) => {
        updateAgent(agent.id, {
          ...agent,
          state: 'idle',
          currentContent: null,
          target: null,
        } as AgentRuntimeState);
      });
    },
    [updateAgent]
  );

  const handleAgentThinking = useCallback(
    (payload: AgentThinkingPayload) => {
      updateAgent(payload.agentId, {
        state: 'thinking',
        target: payload.target ?? null,
        currentContent: null,
      });
    },
    [updateAgent]
  );

  const handleAgentStreaming = useCallback(
    (payload: AgentStreamingPayload) => {
      const currentAgent = useSwarmStore.getState().agents[payload.agentId];
      const currentContent = currentAgent?.currentContent ?? '';

      updateAgent(payload.agentId, {
        state: 'typing',
        currentContent: currentContent + payload.chunk,
      });
    },
    [updateAgent]
  );

  const handleAgentComplete = useCallback(
    (payload: AgentCompletePayload) => {
      updateAgent(payload.agentId, {
        state: 'complete',
      });

      if (payload.critique) {
        addCritique(payload.critique);
      }

      if (payload.response) {
        addResponse(payload.response);
      }
    },
    [updateAgent, addCritique, addResponse]
  );

  const handleDraftUpdate = useCallback(
    (payload: DraftUpdatePayload) => {
      // The draft payload now contains a full DocumentDraft structure
      // with id, sections array, overallConfidence, and updatedAt
      const incomingDraft = payload.draft as DocumentDraft;

      // Convert updatedAt to Date if it's a string
      const normalizedDraft: DocumentDraft = {
        ...incomingDraft,
        updatedAt: typeof incomingDraft.updatedAt === 'string'
          ? new Date(incomingDraft.updatedAt)
          : incomingDraft.updatedAt,
      };

      const existingDraft = useSwarmStore
        .getState()
        .drafts.find((d) => d.id === normalizedDraft.id);

      if (existingDraft) {
        updateDraft(normalizedDraft);
      } else {
        // Always add as new draft to show progression over time
        addDraft(normalizedDraft);
      }
    },
    [addDraft, updateDraft]
  );

  const handleConfidenceUpdate = useCallback(
    (payload: ConfidenceUpdatePayload) => {
      // Update the latest draft with new confidence scores
      const draftsState = useSwarmStore.getState().drafts;
      const latestDraft = draftsState[draftsState.length - 1];

      if (latestDraft) {
        const updatedSections = latestDraft.sections.map((section) => ({
          ...section,
          confidence: payload.sections[section.id] ?? section.confidence,
        }));

        updateDraft({
          ...latestDraft,
          sections: updatedSections,
          overallConfidence: payload.overall,
        });
      }
    },
    [updateDraft]
  );

  const handleEscalationTriggered = useCallback(
    (payload: EscalationTriggeredPayload) => {
      setEscalation({
        reasons: payload.reasons,
        disputes: payload.disputes,
      });
      setStatus('review');
      onEscalation?.(payload);
    },
    [setEscalation, setStatus, onEscalation]
  );

  const handleGenerationComplete = useCallback(
    (payload: GenerationCompletePayload) => {
      setResult(payload.result);
      onComplete?.(payload.result);
    },
    [setResult, onComplete]
  );

  const handleGenerationError = useCallback(
    (payload: GenerationErrorPayload) => {
      setError(payload.error);
      onError?.(payload);
    },
    [setError, onError]
  );

  // ============================================================================
  // Subscribe to Events
  // ============================================================================

  useEffect(() => {
    const unsubscribers: (() => void)[] = [];

    // Helper to create typed subscription
    const sub = <K extends ServerEventType>(
      type: K,
      handler: (payload: ServerEvents[K]) => void
    ) => {
      unsubscribers.push(subscribe(type, handler as (payload: unknown) => void));
    };

    sub('round:start', handleRoundStart);
    sub('round:end', handleRoundEnd);
    sub('phase:change', handlePhaseChange);
    sub('agent:registered', handleAgentRegistered);
    sub('agent:thinking', handleAgentThinking);
    sub('agent:streaming', handleAgentStreaming);
    sub('agent:complete', handleAgentComplete);
    sub('draft:update', handleDraftUpdate);
    sub('confidence:update', handleConfidenceUpdate);
    sub('escalation:triggered', handleEscalationTriggered);
    sub('generation:complete', handleGenerationComplete);
    sub('generation:error', handleGenerationError);

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [
    subscribe,
    handleRoundStart,
    handleRoundEnd,
    handlePhaseChange,
    handleAgentRegistered,
    handleAgentThinking,
    handleAgentStreaming,
    handleAgentComplete,
    handleDraftUpdate,
    handleConfidenceUpdate,
    handleEscalationTriggered,
    handleGenerationComplete,
    handleGenerationError,
  ]);

  // ============================================================================
  // Client Actions
  // ============================================================================

  const sendEvent = useCallback(
    <K extends keyof ClientEvents>(type: K, payload: ClientEvents[K]) => {
      send(type, payload);
    },
    [send]
  );

  const startGeneration = useCallback(
    (reqId: string, request: DocumentRequest) => {
      currentRequestIdRef.current = reqId;
      isFirstDraftRef.current = true;

      // Build the full payload required by the backend
      const payload: GenerationStartPayload = {
        requestId: reqId,
        documentType: request.documentType,
        companyProfileId: request.companyProfileId,
        opportunityContext: request.opportunityContext,
        config: request.config,
      };

      sendEvent('generation:start', payload);
    },
    [sendEvent]
  );

  const pauseGeneration = useCallback(() => {
    if (currentRequestIdRef.current) {
      sendEvent('generation:pause', { requestId: currentRequestIdRef.current });
    }
  }, [sendEvent]);

  const resumeGeneration = useCallback(() => {
    if (currentRequestIdRef.current) {
      sendEvent('generation:resume', {
        requestId: currentRequestIdRef.current,
      });
    }
  }, [sendEvent]);

  const cancelGeneration = useCallback(() => {
    if (currentRequestIdRef.current) {
      sendEvent('generation:cancel', {
        requestId: currentRequestIdRef.current,
      });
      setStatus('idle');
    }
  }, [sendEvent, setStatus]);

  return {
    startGeneration,
    pauseGeneration,
    resumeGeneration,
    cancelGeneration,
    connectionStatus,
    connectionId,
    isGenerating: generationStatus === 'running',
  };
}

/**
 * Hook to subscribe to specific swarm events with typed handlers
 */
export function useSwarmEvent<K extends ServerEventType>(
  eventType: K,
  handler: (payload: ServerEvents[K]) => void
) {
  const { subscribe } = useWebSocket();

  useEffect(() => {
    return subscribe(eventType, handler as (payload: unknown) => void);
  }, [eventType, handler, subscribe]);
}
