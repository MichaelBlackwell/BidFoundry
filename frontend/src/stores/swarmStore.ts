import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import type {
  GenerationStatus,
  Phase,
  SwarmConfig,
  DocumentRequest,
  AgentRuntimeState,
  DocumentDraft,
  Critique,
  Response,
  FinalOutput,
  EscalationInfo,
} from '../types';

interface ConfidenceState {
  overall: number;
  sections: Record<string, number>;
}

interface SwarmState {
  // Generation lifecycle
  status: GenerationStatus;
  config: SwarmConfig | null;
  request: DocumentRequest | null;

  // Real-time state
  currentRound: number;
  totalRounds: number;
  currentPhase: Phase;
  agents: Record<string, AgentRuntimeState>;

  // Confidence tracking
  confidence: ConfidenceState | null;

  // Accumulated outputs
  drafts: DocumentDraft[];
  critiques: Critique[];
  responses: Response[];

  // Final result
  result: FinalOutput | null;
  escalation: EscalationInfo | null;
  error: string | null;

  // Actions
  setConfig: (config: SwarmConfig) => void;
  startGeneration: (request: DocumentRequest) => void;
  setStatus: (status: GenerationStatus) => void;
  setRound: (round: number, totalRounds: number) => void;
  setPhase: (phase: Phase) => void;
  updateAgent: (agentId: string, updates: Partial<AgentRuntimeState>) => void;
  setConfidence: (confidence: ConfidenceState) => void;
  addDraft: (draft: DocumentDraft) => void;
  updateDraft: (draft: DocumentDraft) => void;
  addCritique: (critique: Critique) => void;
  addResponse: (response: Response) => void;
  setResult: (result: FinalOutput) => void;
  setEscalation: (escalation: EscalationInfo) => void;
  setError: (error: string) => void;
  pauseGeneration: () => void;
  resumeGeneration: () => void;
  cancelGeneration: () => void;
  reset: () => void;
}

const initialState = {
  status: 'idle' as GenerationStatus,
  config: null,
  request: null,
  currentRound: 0,
  totalRounds: 3,
  currentPhase: 'blue-build' as Phase,
  agents: {},
  confidence: null,
  drafts: [],
  critiques: [],
  responses: [],
  result: null,
  escalation: null,
  error: null,
};

export const useSwarmStore = create<SwarmState>()(
  devtools(
    subscribeWithSelector((set) => ({
      ...initialState,

      setConfig: (config) => set({ config }),

      startGeneration: (request) =>
        set({
          ...initialState,
          status: 'running',
          config: request.config,
          request,
          totalRounds: request.config.rounds,
        }),

      setStatus: (status) => set({ status }),

      setRound: (round, totalRounds) => set({ currentRound: round, totalRounds }),

      setPhase: (phase) => set({ currentPhase: phase }),

      updateAgent: (agentId, updates) =>
        set((state) => {
          const existingAgent = state.agents[agentId];

          // If agent doesn't exist and updates don't include required fields, skip the update
          // This prevents creating incomplete agent records from streaming events
          if (!existingAgent && (!updates.name || !updates.role || !updates.category)) {
            console.warn(`[swarmStore] Skipping update for unregistered agent: ${agentId}`);
            return state;
          }

          return {
            agents: {
              ...state.agents,
              [agentId]: {
                ...existingAgent,
                ...updates,
              },
            },
          };
        }),

      setConfidence: (confidence) => set({ confidence }),

      addDraft: (draft) =>
        set((state) => ({
          drafts: [...state.drafts, draft],
        })),

      updateDraft: (draft) =>
        set((state) => ({
          drafts: state.drafts.map((d) => (d.id === draft.id ? draft : d)),
        })),

      addCritique: (critique) =>
        set((state) => ({
          critiques: [...state.critiques, critique],
        })),

      addResponse: (response) =>
        set((state) => ({
          responses: [...state.responses, response],
        })),

      setResult: (result) =>
        set({
          result,
          status: result.requiresHumanReview ? 'review' : 'complete',
        }),

      setEscalation: (escalation) =>
        set({
          escalation,
          status: 'review',
        }),

      setError: (error) =>
        set({
          error,
          status: 'error',
        }),

      pauseGeneration: () =>
        set((state) => ({
          status: state.status === 'running' ? 'review' : state.status,
        })),

      resumeGeneration: () =>
        set((state) => ({
          status: state.status === 'review' ? 'running' : state.status,
        })),

      cancelGeneration: () =>
        set({
          status: 'idle',
        }),

      reset: () => set(initialState),
    })),
    { name: 'swarm-store' }
  )
);

// Selectors for common access patterns
export const selectStatus = (state: SwarmState) => state.status;
export const selectIsRunning = (state: SwarmState) => state.status === 'running';
export const selectCurrentRound = (state: SwarmState) => state.currentRound;
export const selectCurrentPhase = (state: SwarmState) => state.currentPhase;
export const selectAgents = (state: SwarmState) => Object.values(state.agents);
export const selectLatestDraft = (state: SwarmState) =>
  state.drafts[state.drafts.length - 1] ?? null;

// Critique and Response selectors
export const selectCritiquesForRound = (round: number) => (state: SwarmState) =>
  state.critiques.filter((c) => c.round === round);

export const selectCritiquesForPhase = (phase: Phase) => (state: SwarmState) =>
  state.critiques.filter((c) => c.phase === phase);

export const selectCritiquesBySeverity = (severity: Critique['severity']) => (state: SwarmState) =>
  state.critiques.filter((c) => c.severity === severity);

export const selectUnresolvedCritiques = (state: SwarmState) =>
  state.critiques.filter((c) => c.status === 'pending' || !c.status);

export const selectResponsesForRound = (round: number) => (state: SwarmState) =>
  state.responses.filter((r) => r.round === round);

export const selectResponseForCritique = (critiqueId: string) => (state: SwarmState) =>
  state.responses.find((r) => r.critiqueId === critiqueId);

// Agent selectors
export const selectAgentById = (agentId: string) => (state: SwarmState) =>
  state.agents[agentId];

export const selectAgentsByCategory = (category: AgentRuntimeState['category']) => (state: SwarmState) =>
  Object.values(state.agents).filter((a) => a.category === category);

export const selectActiveAgents = (state: SwarmState) =>
  Object.values(state.agents).filter((a) => a.state === 'thinking' || a.state === 'typing');

// Summary selectors
export const selectCritiqueSummary = (state: SwarmState) => {
  const critiques = state.critiques;
  return {
    total: critiques.length,
    critical: critiques.filter((c) => c.severity === 'critical').length,
    major: critiques.filter((c) => c.severity === 'major').length,
    minor: critiques.filter((c) => c.severity === 'minor').length,
    accepted: critiques.filter((c) => c.status === 'accepted').length,
    rebutted: critiques.filter((c) => c.status === 'rebutted').length,
    pending: critiques.filter((c) => c.status === 'pending' || !c.status).length,
  };
};

export const selectRoundProgress = (state: SwarmState) => ({
  current: state.currentRound,
  total: state.totalRounds,
  phase: state.currentPhase,
  percentComplete: state.totalRounds > 0
    ? Math.round((state.currentRound / state.totalRounds) * 100)
    : 0,
});
