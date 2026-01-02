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

/**
 * Structured insights from blue team agents.
 * Organized by agent category for display in the Agent Insights panel.
 */
export interface AgentInsights {
  marketIntelligence: {
    tam?: string | number;
    sam?: string | number;
    competitiveDensity?: string;
    opportunityCount?: number;
    rankedOpportunities?: unknown[];
    timingRecommendations?: string[];
    marketTrends?: string[];
    analysisContent?: string;
  };
  captureStrategy: {
    winThemeCount?: number;
    discriminatorCount?: number;
    competitorCount?: number;
    winProbability?: string;
    pricePositioning?: string;
    analysisContent?: string;
  };
  complianceStatus: {
    eligibleSetasides?: string[];
    overallStatus?: string;
    criticalIssuesCount?: number;
    complianceGapsCount?: number;
    ociRiskLevel?: string;
    analysisContent?: string;
  };
  summary: {
    agentsContributed: Array<{
      role: string;
      name: string;
      hasContent: boolean;
      hasSections: boolean;
    }>;
    keyFindings: string[];
  };
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

  // Agent insights from blue team agents
  agentInsights: AgentInsights;

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
  updateAgentInsights: (payload: { agentRole: string; agentName: string; content: string | null; metadata: Record<string, unknown> }) => void;
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

const initialAgentInsights: AgentInsights = {
  marketIntelligence: {},
  captureStrategy: {},
  complianceStatus: {},
  summary: {
    agentsContributed: [],
    keyFindings: [],
  },
};

const initialState = {
  status: 'idle' as GenerationStatus,
  config: null,
  request: null,
  currentRound: 0,
  totalRounds: 3,
  currentPhase: 'blue-build' as Phase,
  agents: {},
  confidence: null,
  agentInsights: initialAgentInsights,
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

      updateAgentInsights: (payload) =>
        set((state) => {
          const { agentRole, agentName, content, metadata } = payload;
          const roleLower = agentRole.toLowerCase();

          // Create updated insights based on agent role
          const updatedInsights = { ...state.agentInsights };

          // Track agent contribution in summary
          const alreadyContributed = updatedInsights.summary.agentsContributed.some(
            (a) => a.role === agentRole
          );
          if (!alreadyContributed) {
            updatedInsights.summary = {
              ...updatedInsights.summary,
              agentsContributed: [
                ...updatedInsights.summary.agentsContributed,
                {
                  role: agentRole,
                  name: agentName,
                  hasContent: !!content,
                  hasSections: false,
                },
              ],
            };
          }

          // Route to appropriate insight category based on role
          if (roleLower.includes('market_analyst') || roleLower.includes('market analyst')) {
            updatedInsights.marketIntelligence = {
              tam: metadata.tam as string | number | undefined,
              sam: metadata.sam as string | number | undefined,
              competitiveDensity: metadata.competitive_density as string | undefined,
              opportunityCount: metadata.opportunity_count as number | undefined,
              rankedOpportunities: metadata.ranked_opportunities as unknown[] | undefined,
              timingRecommendations: metadata.timing_recommendations as string[] | undefined,
              marketTrends: metadata.market_trends as string[] | undefined,
              analysisContent: content || undefined,
            };
            if (metadata.competitive_density) {
              updatedInsights.summary.keyFindings = [
                ...updatedInsights.summary.keyFindings,
                `Market competitive density: ${metadata.competitive_density}`,
              ];
            }
          } else if (roleLower.includes('capture_strategist') || roleLower.includes('capture strategist')) {
            updatedInsights.captureStrategy = {
              winThemeCount: metadata.win_theme_count as number | undefined,
              discriminatorCount: metadata.discriminator_count as number | undefined,
              competitorCount: metadata.competitor_count as number | undefined,
              winProbability: metadata.win_probability as string | undefined,
              pricePositioning: metadata.price_positioning as string | undefined,
              analysisContent: content || undefined,
            };
            if (metadata.win_probability) {
              updatedInsights.summary.keyFindings = [
                ...updatedInsights.summary.keyFindings,
                `Win probability: ${metadata.win_probability}`,
              ];
            }
          } else if (roleLower.includes('compliance_navigator') || roleLower.includes('compliance navigator')) {
            updatedInsights.complianceStatus = {
              eligibleSetasides: metadata.eligible_setasides as string[] | undefined,
              overallStatus: metadata.overall_status as string | undefined,
              criticalIssuesCount: metadata.critical_issues_count as number | undefined,
              complianceGapsCount: metadata.compliance_gaps_count as number | undefined,
              ociRiskLevel: metadata.oci_risk_level as string | undefined,
              analysisContent: content || undefined,
            };
            if (metadata.overall_status) {
              updatedInsights.summary.keyFindings = [
                ...updatedInsights.summary.keyFindings,
                `Compliance status: ${metadata.overall_status}`,
              ];
            }
          }

          return { agentInsights: updatedInsights };
        }),

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
          critiques: [
            ...state.critiques,
            {
              ...critique,
              severity: critique.severity || 'minor',
              status: critique.status || 'pending',
            },
          ],
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
export const selectAgentInsights = (state: SwarmState) => state.agentInsights;

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
