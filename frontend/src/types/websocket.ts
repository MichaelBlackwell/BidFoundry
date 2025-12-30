/**
 * WebSocket Event Types
 *
 * Defines all WebSocket events for real-time communication between
 * the frontend and backend during document generation.
 *
 * Based on Section 7.2 of the Frontend Design Document.
 */

import type {
  AgentInfo,
  Critique,
  Response,
  DocumentDraft,
  Phase,
  FinalOutput,
  EscalationInfo,
  SwarmConfig,
} from './index';

// ============================================================================
// Client → Server Events
// ============================================================================

export interface GenerationStartPayload {
  requestId: string;
  documentType: string;
  companyProfileId: string;
  opportunityContext?: {
    solicitationNumber?: string;
    targetAgency?: string;
    knownCompetitors?: string[];
    budgetMin?: number;
    budgetMax?: number;
    dueDate?: string;
  };
  config: SwarmConfig;
}

export interface GenerationPausePayload {
  requestId: string;
}

export interface GenerationResumePayload {
  requestId: string;
}

export interface GenerationCancelPayload {
  requestId: string;
}

export type ClientEventType =
  | 'generation:start'
  | 'generation:pause'
  | 'generation:resume'
  | 'generation:cancel';

export interface ClientEvents {
  'generation:start': GenerationStartPayload;
  'generation:pause': GenerationPausePayload;
  'generation:resume': GenerationResumePayload;
  'generation:cancel': GenerationCancelPayload;
}

// ============================================================================
// Server → Client Events
// ============================================================================

export interface RoundStartPayload {
  round: number;
  totalRounds: number;
  phase: Phase;
  agents: AgentInfo[];
}

export interface RoundEndPayload {
  round: number;
  summary: {
    critiquesCount: number;
    responsesCount: number;
    acceptedCount: number;
    rebuttedCount: number;
  };
}

export interface AgentThinkingPayload {
  agentId: string;
  target?: string;
}

export interface AgentStreamingPayload {
  agentId: string;
  chunk: string;
}

export interface AgentCompletePayload {
  agentId: string;
  critique?: Critique;
  response?: Response;
}

export interface DraftUpdatePayload {
  draft: DocumentDraft;
  changedSections: string[];
}

export interface ConfidenceUpdatePayload {
  overall: number;
  sections: Record<string, number>;
}

export interface EscalationTriggeredPayload {
  reasons: string[];
  disputes: EscalationInfo['disputes'];
}

export interface GenerationCompletePayload {
  result: FinalOutput;
}

export interface GenerationErrorPayload {
  error: string;
  code?: string;
  recoverable?: boolean;
}

export interface PhaseChangePayload {
  phase: Phase;
  round: number;
}

export interface AgentRegisteredPayload {
  agents: AgentInfo[];
}

export interface ConnectedPayload {
  connectionId: string;
  serverTime: number;
}

export type ServerEventType =
  | 'connected'
  | 'round:start'
  | 'round:end'
  | 'phase:change'
  | 'agent:registered'
  | 'agent:thinking'
  | 'agent:streaming'
  | 'agent:complete'
  | 'draft:update'
  | 'confidence:update'
  | 'escalation:triggered'
  | 'generation:complete'
  | 'generation:error';

export interface ServerEvents {
  'connected': ConnectedPayload;
  'round:start': RoundStartPayload;
  'round:end': RoundEndPayload;
  'phase:change': PhaseChangePayload;
  'agent:registered': AgentRegisteredPayload;
  'agent:thinking': AgentThinkingPayload;
  'agent:streaming': AgentStreamingPayload;
  'agent:complete': AgentCompletePayload;
  'draft:update': DraftUpdatePayload;
  'confidence:update': ConfidenceUpdatePayload;
  'escalation:triggered': EscalationTriggeredPayload;
  'generation:complete': GenerationCompletePayload;
  'generation:error': GenerationErrorPayload;
}

// ============================================================================
// WebSocket Message Types
// ============================================================================

export interface WebSocketMessage<T = unknown> {
  type: string;
  payload: T;
  timestamp?: number;
  requestId?: string;
}

export interface TypedWebSocketMessage<
  K extends keyof ServerEvents | keyof ClientEvents
> {
  type: K;
  payload: K extends keyof ServerEvents
    ? ServerEvents[K]
    : K extends keyof ClientEvents
    ? ClientEvents[K]
    : never;
  timestamp?: number;
  requestId?: string;
}

// ============================================================================
// Connection State
// ============================================================================

export type ConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'reconnecting';

export interface ConnectionState {
  status: ConnectionStatus;
  reconnectAttempts: number;
  lastConnectedAt: Date | null;
  lastDisconnectedAt: Date | null;
  error: string | null;
}

// ============================================================================
// Message Queue (for offline/reconnection handling)
// ============================================================================

export interface QueuedMessage {
  id: string;
  type: keyof ClientEvents;
  payload: ClientEvents[keyof ClientEvents];
  timestamp: number;
  retries: number;
}

// ============================================================================
// Type Guards
// ============================================================================

export function isServerEvent(type: string): type is ServerEventType {
  return [
    'connected',
    'round:start',
    'round:end',
    'phase:change',
    'agent:registered',
    'agent:thinking',
    'agent:streaming',
    'agent:complete',
    'draft:update',
    'confidence:update',
    'escalation:triggered',
    'generation:complete',
    'generation:error',
  ].includes(type);
}

export function isClientEvent(type: string): type is ClientEventType {
  return [
    'generation:start',
    'generation:pause',
    'generation:resume',
    'generation:cancel',
  ].includes(type);
}

// ============================================================================
// Event Handler Types
// ============================================================================

export type ServerEventHandler<K extends ServerEventType> = (
  payload: ServerEvents[K]
) => void;

export type MessageHandler = (payload: unknown) => void;

export interface EventHandlers {
  onRoundStart?: ServerEventHandler<'round:start'>;
  onRoundEnd?: ServerEventHandler<'round:end'>;
  onPhaseChange?: ServerEventHandler<'phase:change'>;
  onAgentRegistered?: ServerEventHandler<'agent:registered'>;
  onAgentThinking?: ServerEventHandler<'agent:thinking'>;
  onAgentStreaming?: ServerEventHandler<'agent:streaming'>;
  onAgentComplete?: ServerEventHandler<'agent:complete'>;
  onDraftUpdate?: ServerEventHandler<'draft:update'>;
  onConfidenceUpdate?: ServerEventHandler<'confidence:update'>;
  onEscalationTriggered?: ServerEventHandler<'escalation:triggered'>;
  onGenerationComplete?: ServerEventHandler<'generation:complete'>;
  onGenerationError?: ServerEventHandler<'generation:error'>;
}
