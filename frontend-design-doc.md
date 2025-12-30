# Adversarial Swarm Frontend Design Document

## React Application for GovCon Strategy Generation

### Version 1.1

> **Implementation Status:** ✅ Frontend fully implemented with all core views, real-time WebSocket streaming, accessibility features, and responsive design.

---

## 1. Executive Summary

This document describes the frontend architecture for the Adversarial Swarm application—a React-based interface that allows power users to generate government contracting strategy documents while observing the real-time red team/blue team debate process. The UI emphasizes transparency into agent reasoning, granular control over swarm behavior, and efficient document workflow.

---

## 2. Design Principles

| Principle | Description |
|-----------|-------------|
| **Transparency** | Users see exactly how agents argue, critique, and resolve disputes |
| **Control** | Power users can tune agent behavior, select participants, adjust intensity |
| **Progressive Disclosure** | Complexity is available but not overwhelming; sensible defaults throughout |
| **Real-time Feedback** | Streaming updates as agents work; no black-box waiting |
| **Keyboard-first** | Power users expect shortcuts and efficient navigation |

---

## 3. Information Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP SHELL                                │
│  ┌───────────┐  ┌─────────────────────────────────────────────┐ │
│  │           │  │                                             │ │
│  │  SIDEBAR  │  │              MAIN WORKSPACE                 │ │
│  │           │  │                                             │ │
│  │ • New Doc │  │  ┌─────────────────────────────────────┐   │ │
│  │ • History │  │  │         DOCUMENT HEADER             │   │ │
│  │ • Company │  │  │    (type, status, confidence)       │   │ │
│  │   Profile │  │  └─────────────────────────────────────┘   │ │
│  │ • Settings│  │                                             │ │
│  │           │  │  ┌─────────────┬───────────────────────┐   │ │
│  │           │  │  │             │                       │   │ │
│  │           │  │  │   DEBATE    │      DOCUMENT         │   │ │
│  │           │  │  │   THEATER   │      PREVIEW          │   │ │
│  │           │  │  │             │                       │   │ │
│  │           │  │  │  (agent     │   (live-updating      │   │ │
│  │           │  │  │   activity) │    draft)             │   │ │
│  │           │  │  │             │                       │   │ │
│  │           │  │  └─────────────┴───────────────────────┘   │ │
│  │           │  │                                             │ │
│  │           │  │  ┌─────────────────────────────────────┐   │ │
│  │           │  │  │         CONTROL PANEL               │   │ │
│  │           │  │  │   (agent config, actions)           │   │ │
│  │           │  │  └─────────────────────────────────────┘   │ │
│  └───────────┘  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Views

### 4.1 Document Creation View

Entry point for generating a new strategy document.

**Sections:**

```
┌─────────────────────────────────────────────────────────────────┐
│  CREATE NEW DOCUMENT                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  DOCUMENT TYPE                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ○ Capability Statement    ○ SWOT Analysis               │   │
│  │ ○ Competitive Analysis    ○ BD Pipeline Plan            │   │
│  │ ○ Proposal Strategy       ○ Go-to-Market Strategy       │   │
│  │ ○ Teaming Strategy                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  COMPANY PROFILE                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [Select saved profile ▼]  or  [+ Create new]            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  OPPORTUNITY CONTEXT (optional)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Solicitation #: [_______________]                       │   │
│  │ Target Agency:  [_______________]                       │   │
│  │ Known Competitors: [tag input________________________]  │   │
│  │ Budget Range:   [$______] - [$______]                   │   │
│  │ Due Date:       [_______________]                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ▶ ADVANCED: SWARM CONFIGURATION  [collapsed by default]       │
│                                                                 │
│            [Cancel]                    [Generate Document →]    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Swarm Configuration Panel (Advanced)

Power user controls for tuning agent behavior.

```
┌─────────────────────────────────────────────────────────────────┐
│  SWARM CONFIGURATION                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ADVERSARIAL INTENSITY                                          │
│  ├────────●─────────────┤  Medium                               │
│  Light    Med    Aggressive                                     │
│                                                                 │
│  ADVERSARIAL ROUNDS        [3 ▼]  (1-5)                        │
│                                                                 │
│  CONSENSUS REQUIREMENT                                          │
│  ○ Simple majority   ● Supermajority   ○ Full agreement        │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  BLUE TEAM AGENTS                      RED TEAM AGENTS          │
│  ☑ Strategy Architect (required)       ☑ Devil's Advocate      │
│  ☑ Market Analyst                      ☑ Competitor Simulator  │
│  ☑ Compliance Navigator                ☑ Evaluator Simulator   │
│  ☑ Capture Strategist                  ☑ Risk Assessor         │
│                                                                 │
│  SPECIALIST AGENTS (auto-suggested based on document type)      │
│  ☑ GSA Specialist          ☐ SBIR/STTR Advisor                 │
│  ☐ Pricing Strategist      ☐ Clearance Consultant              │
│  ☑ Past Performance Curator                                     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  RISK TOLERANCE                                                 │
│  ○ Conservative (flag all risks)                                │
│  ● Balanced (flag medium+ risks)                                │
│  ○ Aggressive (flag only critical risks)                        │
│                                                                 │
│  AUTO-ESCALATE TO HUMAN REVIEW WHEN:                           │
│  ☑ Confidence < [70]%                                          │
│  ☑ Critical unresolved critiques                               │
│  ☑ Compliance uncertainty flagged                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Debate Theater View

The centerpiece: real-time visualization of agent debate.

```
┌─────────────────────────────────────────────────────────────────┐
│  DEBATE THEATER                                    Round 2 of 3 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PHASE: RED TEAM ATTACK                          ◉ Live         │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔴 DEVIL'S ADVOCATE                           Critical   │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ TARGET: Section 3.2 - Market Sizing                     │   │
│  │                                                         │   │
│  │ "The $2.4B TAM estimate assumes 15% YoY growth, but     │   │
│  │ Agency X's budget justification shows flat funding      │   │
│  │ through FY26. This undermines the entire growth         │   │
│  │ thesis."                                                │   │
│  │                                                         │   │
│  │ SUGGESTED REMEDY: Revise to 3-5% growth with            │   │
│  │ sensitivity analysis for flat scenario.                 │   │
│  │                                                    2:34 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔴 EVALUATOR SIMULATOR                           Major   │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ TARGET: Section 4.1 - Past Performance                  │   │
│  │                                                         │   │
│  │ "Past performance narrative lacks quantified outcomes.  │   │
│  │ An SSEB would score this as a weakness. Government      │   │
│  │ evaluators expect metrics: cost savings %, on-time      │   │
│  │ delivery %, customer satisfaction scores."              │   │
│  │                                                         │   │
│  │ SUGGESTED REMEDY: Add 2-3 quantified achievements       │   │
│  │ per cited contract.                                     │   │
│  │                                                    2:31 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔴 COMPETITOR SIMULATOR (as: BoozAllen)          Major   │   │
│  │ ─────────────────────────────────────────────────────── │   │
│  │ Typing...  █                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ──────────────────────────────────────────────────────────    │
│  ROUND SUMMARY                                                  │
│  Critiques: 5 total (2 Critical, 2 Major, 1 Minor)             │
│  Agents reporting: 3/4                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Agent Cards

Individual agent representation during debate.

**States:**

| State | Visual Treatment |
|-------|------------------|
| Idle | Grayed out, subtle |
| Thinking | Pulsing border, "Analyzing..." |
| Typing | Active border, streaming text |
| Complete | Solid border, full content |
| Waiting | Dimmed, "Waiting for round..." |

**Agent Card Anatomy:**

```
┌─────────────────────────────────────────────────────────────┐
│ [Icon] AGENT NAME                      [Severity Badge]     │
│ ─────────────────────────────────────────────────────────── │
│ TARGET: [Section reference]                                 │
│                                                             │
│ [Critique/Response body text - streams in real-time]       │
│                                                             │
│ SUGGESTED REMEDY: [Recommendation]                          │
│                                                             │
│ [Evidence/Data citations if applicable]                     │
│                                                        time │
└─────────────────────────────────────────────────────────────┘
```

**Color Coding:**

| Agent Category | Color | Icon |
|----------------|-------|------|
| Blue Team | Blue (#3B82F6) | 🔵 |
| Red Team | Red (#EF4444) | 🔴 |
| Specialist | Purple (#8B5CF6) | 🟣 |
| Arbiter | Gold (#F59E0B) | ⚖️ |

### 4.5 Document Preview Pane

Live-updating document as agents work.

```
┌─────────────────────────────────────────────────────────────────┐
│  DOCUMENT PREVIEW                          [Expand] [Export ▼] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  COMPETITIVE ANALYSIS: DHS EAGLE II RECOMPETE                  │
│  ═══════════════════════════════════════════════════════════   │
│  Confidence: ████████░░ 78%                                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. EXECUTIVE SUMMARY                              [92%] │   │
│  │                                                         │   │
│  │ Acme Federal is well-positioned to capture Task Order   │   │
│  │ opportunities under the EAGLE II recompete, with        │   │
│  │ particular strength in cybersecurity and cloud          │   │
│  │ migration services aligned to DHS priorities...         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2. MARKET LANDSCAPE                               [71%] │   │
│  │ ⚠️ 2 unresolved critiques                               │   │
│  │                                                         │   │
│  │ The DHS IT services market represents approximately     │   │
│  │ $2.4B in annual spend, with projected growth of         │   │
│  │ ~~15%~~ 3-5% annually through FY27...                   │   │
│  │                                                         │   │
│  │ [Revision in progress - accepting critique #C-2024]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 3. COMPETITOR PROFILES                            [85%] │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Preview Features:**
- Section-level confidence scores
- Visual diff for revisions (strikethrough old, highlight new)
- Warning badges for sections with unresolved critiques
- Click section to jump to relevant debate thread
- Real-time updates as blue team revises

### 4.6 Human Review Modal

Triggered when escalation thresholds are breached.

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  HUMAN REVIEW REQUIRED                                [X]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  The swarm was unable to reach consensus on this document.     │
│  Overall confidence: 64%                                        │
│                                                                 │
│  ESCALATION TRIGGERS:                                          │
│  • Confidence below 70% threshold                              │
│  • 2 critical unresolved critiques                             │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  UNRESOLVED DISPUTES:                                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DISPUTE #1: Market Growth Assumptions                   │   │
│  │                                                         │   │
│  │ 🔴 Red Team Position:                                   │   │
│  │ "15% growth assumption contradicts budget data"         │   │
│  │                                                         │   │
│  │ 🔵 Blue Team Position:                                  │   │
│  │ "Growth reflects new administration priorities not      │   │
│  │ yet reflected in budget documents"                      │   │
│  │                                                         │   │
│  │ ⚖️ Arbiter Note:                                        │   │
│  │ "Insufficient evidence on either side. Recommend        │   │
│  │ human judgment on market outlook."                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ DISPUTE #2: Teaming Partner Viability                   │   │
│  │ ...                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ACTIONS:                                                       │
│                                                                 │
│  [Approve as-is]  [Reject & Regenerate]  [View Full Document]  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Regeneration options:                                         │
│  ○ Retry with same configuration                               │
│  ○ Retry with higher adversarial rounds                        │
│  ○ Retry with modified agent selection                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.7 Final Output View

Post-generation document view with full artifacts.

```
┌─────────────────────────────────────────────────────────────────┐
│  ✓ DOCUMENT COMPLETE                                            │
│  Competitive Analysis: DHS EAGLE II Recompete                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TABS: [Document] [Red Team Report] [Debate Log] [Metrics]     │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  CONFIDENCE BREAKDOWN                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Overall:        ████████░░ 82%                          │   │
│  │ Executive:      █████████░ 92%                          │   │
│  │ Market:         ███████░░░ 71%  ⚠️                      │   │
│  │ Competitors:    ████████░░ 85%                          │   │
│  │ Positioning:    █████████░ 88%                          │   │
│  │ Recommendations:████████░░ 79%                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  GENERATION STATS                                               │
│  • Rounds completed: 3                                          │
│  • Total critiques: 14 (3 Critical, 6 Major, 5 Minor)          │
│  • Accepted: 9 | Rebutted: 3 | Acknowledged: 2                 │
│  • Time elapsed: 4m 32s                                        │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [DOCUMENT CONTENT - SCROLLABLE]                               │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  EXPORT OPTIONS:                                                │
│  [📄 Word]  [📊 PDF]  [📋 Markdown]  [🔗 Share Link]           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Component Architecture

> ✅ **All components implemented** with full TypeScript support and React 18 features.

### 5.1 Component Hierarchy ✅

```
App ✅
├── AppShell ✅
│   ├── Sidebar ✅
│   │   ├── NavItem (New Document) ✅
│   │   ├── NavItem (History) ✅
│   │   ├── NavItem (Company Profile) ✅
│   │   └── NavItem (Settings) ✅
│   │
│   └── MainWorkspace ✅
│       ├── DocumentCreationView ✅
│       │   ├── DocumentTypeSelector ✅
│       │   ├── CompanyProfileSelector ✅
│       │   ├── OpportunityContextForm ✅
│       │   └── SwarmConfigPanel (collapsible) ✅
│       │       ├── IntensitySlider ✅
│       │       ├── RoundsSelector ✅
│       │       ├── ConsensusSelector ✅
│       │       ├── AgentChecklist (Blue) ✅
│       │       ├── AgentChecklist (Red) ✅
│       │       ├── AgentChecklist (Specialist) ✅
│       │       └── EscalationConfig ✅
│       │
│       ├── GenerationView ✅
│       │   ├── DocumentHeader ✅
│       │   │   ├── StatusBadge ✅
│       │   │   ├── RoundIndicator ✅
│       │   │   └── ConfidenceMeter ✅
│       │   │
│       │   ├── DebateTheater ✅
│       │   │   ├── PhaseHeader ✅
│       │   │   ├── AgentCardList ✅
│       │   │   │   └── AgentCard (multiple) ✅
│       │   │   │       ├── AgentAvatar ✅
│       │   │   │       ├── SeverityBadge ✅
│       │   │   │       ├── StreamingContent ✅
│       │   │   │       └── Timestamp ✅
│       │   │   └── RoundSummary ✅
│       │   │
│       │   ├── DocumentPreview ✅
│       │   │   ├── SectionList ✅
│       │   │   │   └── SectionCard (multiple) ✅
│       │   │   │       ├── SectionConfidence ✅
│       │   │   │       ├── ContentDiff ✅
│       │   │   │       └── CritiqueWarnings ✅
│       │   │   └── PreviewControls ✅
│       │   │
│       │   └── ControlPanel ✅
│       │       ├── PauseResumeButton ✅
│       │       ├── SkipRoundButton ✅
│       │       └── CancelButton ✅
│       │
│       ├── HumanReviewModal ✅
│       │   ├── EscalationSummary ✅
│       │   ├── DisputeList ✅
│       │   │   └── DisputeCard (multiple) ✅
│       │   └── ActionButtons ✅
│       │
│       └── FinalOutputView ✅
│           ├── TabBar ✅
│           ├── ConfidenceBreakdown ✅
│           ├── GenerationStats ✅
│           ├── DocumentContent ✅
│           ├── DebateLogView ✅
│           ├── MetricsView ✅
│           ├── RedTeamReportView ✅
│           └── ExportOptions ✅
│
└── Providers ✅
    ├── AuthProvider ✅
    ├── WebSocketProvider (Enhanced) ✅
    ├── AccessibilityProvider ✅
    └── ThemeProvider ✅
```

### 5.2 Key Component Specifications

#### AgentCard

```typescript
interface AgentCardProps {
  agent: AgentInfo;
  content: string | null;
  state: 'idle' | 'thinking' | 'typing' | 'complete' | 'waiting';
  severity?: 'critical' | 'major' | 'minor';
  target?: string;
  timestamp?: Date;
  onExpand?: () => void;
}
```

#### DebateTheater

```typescript
interface DebateTheaterProps {
  round: number;
  totalRounds: number;
  phase: 'blue-build' | 'red-attack' | 'blue-defense' | 'synthesis';
  agents: AgentState[];
  critiques: Critique[];
  responses: Response[];
  isLive: boolean;
}
```

#### SwarmConfigPanel

```typescript
interface SwarmConfig {
  intensity: 'light' | 'medium' | 'aggressive';
  rounds: number;
  consensus: 'majority' | 'supermajority' | 'unanimous';
  blueTeam: AgentSelection;
  redTeam: AgentSelection;
  specialists: AgentSelection;
  riskTolerance: 'conservative' | 'balanced' | 'aggressive';
  escalationThresholds: {
    confidenceMin: number;
    criticalUnresolved: boolean;
    complianceUncertainty: boolean;
  };
}
```

---

## 6. State Management

### 6.1 Global State Structure

```typescript
interface AppState {
  // Auth
  user: User | null;
  
  // Company data
  companyProfiles: CompanyProfile[];
  activeProfile: CompanyProfile | null;
  
  // Document generation
  generation: {
    status: 'idle' | 'configuring' | 'running' | 'review' | 'complete' | 'error';
    config: SwarmConfig | null;
    request: DocumentRequest | null;
    
    // Real-time state
    currentRound: number;
    currentPhase: Phase;
    agents: Record<AgentId, AgentRuntimeState>;
    
    // Accumulated outputs
    drafts: DocumentDraft[];
    critiques: Critique[];
    responses: Response[];
    
    // Final
    result: FinalOutput | null;
    escalation: EscalationInfo | null;
  };
  
  // History
  documents: GeneratedDocument[];
  
  // UI state
  ui: {
    sidebarCollapsed: boolean;
    debateTheaterWidth: number;
    previewExpanded: boolean;
    activeTab: 'document' | 'redteam' | 'debate' | 'metrics';
  };
}
```

### 6.2 State Management Approach

**Recommended: Zustand + React Query**

| Concern | Solution |
|---------|----------|
| Server state (documents, profiles) | React Query |
| Real-time streaming state | Zustand |
| UI state | Zustand |
| Form state | React Hook Form |

**Rationale:**
- Zustand is lightweight and handles real-time updates well
- React Query manages caching, refetching, optimistic updates
- Avoids Redux boilerplate while maintaining predictability

### 6.3 Real-time State Updates

WebSocket events map to state mutations:

```typescript
// WebSocket event handlers
const wsHandlers = {
  'round:start': (payload) => {
    setCurrentRound(payload.round);
    setCurrentPhase(payload.phase);
  },
  
  'agent:thinking': (payload) => {
    updateAgent(payload.agentId, { state: 'thinking' });
  },
  
  'agent:streaming': (payload) => {
    updateAgent(payload.agentId, { 
      state: 'typing',
      content: (prev) => prev + payload.chunk 
    });
  },
  
  'agent:complete': (payload) => {
    updateAgent(payload.agentId, { state: 'complete' });
    if (payload.critique) addCritique(payload.critique);
    if (payload.response) addResponse(payload.response);
  },
  
  'draft:update': (payload) => {
    updateDraft(payload.draft);
  },
  
  'escalation:triggered': (payload) => {
    setEscalation(payload);
    setStatus('review');
  },
  
  'generation:complete': (payload) => {
    setResult(payload.result);
    setStatus('complete');
  }
};
```

---

## 7. API Contract

### 7.1 REST Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/documents/generate` | Start document generation |
| GET | `/api/documents/:id` | Get document by ID |
| GET | `/api/documents` | List user's documents |
| POST | `/api/documents/:id/regenerate` | Regenerate with new config |
| POST | `/api/documents/:id/approve` | Approve after human review |
| POST | `/api/documents/:id/reject` | Reject after human review |
| GET | `/api/profiles` | List company profiles |
| POST | `/api/profiles` | Create company profile |
| PUT | `/api/profiles/:id` | Update company profile |

### 7.2 WebSocket Events

**Client → Server:**

| Event | Payload | Purpose |
|-------|---------|---------|
| `generation:start` | `{ requestId, config }` | Initiate generation |
| `generation:pause` | `{ requestId }` | Pause generation |
| `generation:resume` | `{ requestId }` | Resume generation |
| `generation:cancel` | `{ requestId }` | Cancel generation |

**Server → Client:**

| Event | Payload | Purpose |
|-------|---------|---------|
| `round:start` | `{ round, phase, agents }` | New round beginning |
| `round:end` | `{ round, summary }` | Round complete |
| `agent:thinking` | `{ agentId, target }` | Agent started processing |
| `agent:streaming` | `{ agentId, chunk }` | Streaming content chunk |
| `agent:complete` | `{ agentId, critique?, response? }` | Agent finished |
| `draft:update` | `{ draft, changedSections }` | Document updated |
| `confidence:update` | `{ overall, sections }` | Confidence recalculated |
| `escalation:triggered` | `{ reasons, disputes }` | Human review needed |
| `generation:complete` | `{ result }` | Generation finished |
| `generation:error` | `{ error }` | Generation failed |

### 7.3 Data Types

```typescript
// Request to generate a document
interface DocumentRequest {
  documentType: DocumentType;
  companyProfileId: string;
  opportunityContext?: OpportunityContext;
  config: SwarmConfig;
}

// Real-time agent state
interface AgentRuntimeState {
  agentId: string;
  role: AgentRole;
  category: 'blue' | 'red' | 'specialist' | 'orchestrator';
  state: 'idle' | 'thinking' | 'typing' | 'complete' | 'waiting';
  currentContent: string | null;
  target: string | null;
}

// Final generation result
interface FinalOutput {
  documentId: string;
  content: DocumentContent;
  confidence: ConfidenceReport;
  redTeamReport: RedTeamReport;
  debateLog: DebateEntry[];
  metrics: GenerationMetrics;
  requiresHumanReview: boolean;
  escalation?: EscalationInfo;
}
```

---

## 8. User Flows

### 8.1 Happy Path: Generate Document

```
1. User clicks "New Document" in sidebar
2. User selects document type (e.g., Competitive Analysis)
3. User selects or creates company profile
4. User optionally fills opportunity context
5. User optionally expands advanced config, adjusts settings
6. User clicks "Generate Document"

7. View transitions to Generation View
8. Debate Theater shows Round 1: Blue Build
   - Strategy Architect card appears, shows "Thinking..."
   - Content streams in as agent writes
   - Other blue team agents activate in parallel
9. Phase indicator updates to "Red Team Attack"
   - Red team agent cards appear
   - Critiques stream in with severity badges
10. Phase updates to "Blue Team Defense"
    - Blue team response cards appear
    - Document preview shows diffs as revisions applied
11. Rounds 2-3 repeat attack/defense cycle
12. Phase updates to "Synthesis"
    - Arbiter card appears
    - Confidence scores finalize

13. View transitions to Final Output
14. User reviews document, red team report, debate log
15. User exports as Word/PDF
```

### 8.2 Escalation Path: Human Review Required

```
1-11. Same as happy path through synthesis

12. Confidence score is 64% (below 70% threshold)
13. Escalation modal appears
    - Shows 2 unresolved critical disputes
    - Displays red vs. blue positions
    - Shows arbiter notes

14. User reviews disputes
15. User selects "Reject & Regenerate"
16. User chooses "Retry with higher adversarial rounds"
17. Generation restarts with 5 rounds instead of 3

18. After regeneration, confidence is 78%
19. User approves document
20. View transitions to Final Output
```

### 8.3 Power User Path: Custom Configuration

```
1. User clicks "New Document"
2. User selects Proposal Strategy Outline
3. User expands Advanced: Swarm Configuration
4. User adjusts:
   - Intensity: Aggressive
   - Rounds: 5
   - Consensus: Full agreement
   - Enables Pricing Strategist specialist
   - Disables Competitor Simulator (known sole-source)
   - Risk tolerance: Conservative
5. User clicks "Generate Document"

6. Generation runs with custom config
7. More critiques generated due to aggressive intensity
8. More rounds before consensus due to stricter requirement
9. All risks flagged due to conservative tolerance

10. Document completes with 91% confidence
11. User exports with full red team report
```

---

## 9. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + N` | New document |
| `Cmd/Ctrl + Enter` | Start generation (from config view) |
| `Space` | Pause/resume generation |
| `Escape` | Cancel generation / close modal |
| `Tab` | Switch between Debate Theater and Preview |
| `1-4` | Switch output tabs (Document/RedTeam/Debate/Metrics) |
| `Cmd/Ctrl + E` | Export document |
| `Cmd/Ctrl + Shift + C` | Copy document as markdown |
| `[` / `]` | Previous/next round in debate log |

---

## 10. Responsive Considerations

### 10.1 Breakpoints

| Breakpoint | Layout |
|------------|--------|
| Desktop (>1280px) | Full layout: sidebar + debate theater + preview side-by-side |
| Tablet (768-1279px) | Collapsible sidebar, stacked theater/preview with tabs |
| Mobile (<768px) | Not supported for generation; view-only for completed docs |

### 10.2 Layout Adaptations

**Tablet Mode:**
- Debate Theater and Document Preview become tabs, not side-by-side
- Swarm Config is a full-screen modal instead of collapsible panel
- Agent cards stack vertically

**Mobile Mode:**
- Generation disabled with message: "Document generation requires desktop"
- Can view completed documents in read-only mode
- Can export/share documents

---

## 11. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Screen reader support | ARIA live regions for streaming content |
| Keyboard navigation | Full keyboard support, visible focus states |
| Color contrast | WCAG AA compliant; severity not color-only |
| Motion sensitivity | Respect `prefers-reduced-motion` for streaming animations |
| Status announcements | Announce phase changes, round completions |

---

## 12. Performance Considerations

### 12.1 Rendering Optimization

| Challenge | Solution |
|-----------|----------|
| Streaming text causes re-renders | Virtualized list for agent cards; memoized components |
| Large debate logs | Windowed rendering for history |
| Real-time confidence recalc | Debounced updates; optimistic UI |
| Multiple concurrent WebSocket events | Batch state updates |

### 12.2 Network Optimization

| Concern | Approach |
|---------|----------|
| WebSocket reconnection | Exponential backoff; automatic reconnect |
| Large document payloads | Gzip compression; incremental updates |
| Offline handling | Queue actions; sync on reconnect |

---

## 13. Error Handling

### 13.1 Error States

| Error Type | User Experience |
|------------|-----------------|
| WebSocket disconnect | Banner: "Connection lost. Reconnecting..." with retry countdown |
| Generation failure | Modal with error details; option to retry or contact support |
| Agent timeout | Agent card shows warning; generation continues with remaining agents |
| Invalid config | Inline validation errors on form fields |
| Rate limit | Modal explaining limit; countdown to retry |

### 13.2 Recovery Flows

```
Generation Interrupted:
1. User loses connection mid-generation
2. On reconnect, server sends current state
3. UI reconstructs debate theater from state
4. Generation resumes (or shows completion if finished)

Agent Failure:
1. Single agent times out or errors
2. Arbiter notes agent unavailable
3. Generation continues with remaining agents
4. Final output notes missing agent perspective
```

---

## 14. Future Enhancements

| Enhancement | Description |
|-------------|-------------|
| Collaborative review | Multiple users review escalated documents together |
| Agent personality tuning | Adjust individual agent aggressiveness/focus |
| Custom agent prompts | Power users can modify agent system prompts |
| Debate replay | Playback completed debates at variable speed |
| Comparison view | Side-by-side multiple generations of same doc type |
| Template library | Save and reuse swarm configurations |
| Notification system | Email/Slack alerts when generation completes |

---

## 15. Implementation Status

All implementation chunks have been completed:

| Chunk | Components | Status |
|-------|------------|--------|
| F1 | App shell, routing, providers | ✅ Complete |
| F2 | Company profile CRUD | ✅ Complete |
| F3 | Document creation form + swarm config | ✅ Complete |
| F4 | WebSocket infrastructure | ✅ Complete |
| F5 | Agent card component | ✅ Complete |
| F6 | Debate theater view | ✅ Complete |
| F7 | Document preview pane | ✅ Complete |
| F8 | Generation view (combined) | ✅ Complete |
| F9 | Human review modal | ✅ Complete |
| F10 | Final output view + export | ✅ Complete |
| F11 | History and document list | ✅ Complete |
| F12 | Polish: shortcuts, accessibility, responsive | ✅ Complete |

---

## 16. Additional Implemented Features

### 16.1 Routes ✅

| Route | Page | Description |
|-------|------|-------------|
| `/` | Redirect | Redirects to `/new` |
| `/new` | NewDocumentPage | Document creation form |
| `/history` | HistoryPage | Document history with filters |
| `/profiles` | CompanyProfilesPage | Company profile management |
| `/settings` | SettingsPage | LLM provider settings |
| `/generate/:requestId` | GenerationPage | Real-time generation view |
| `/documents/:id` | DocumentViewPage | View completed document |

### 16.2 Custom Hooks ✅

| Hook | Purpose |
|------|---------|
| `useProfiles` | Company profile CRUD operations |
| `useDocuments` | Document listing and management |
| `useGeneration` | Generation workflow control |
| `useSwarmWebSocket` | WebSocket connection management |
| `useDocumentPreview` | Live document preview state |
| `useAgentCard` | Agent card state and animations |
| `useDebateTheater` | Debate theater coordination |
| `useGenerationView` | Generation view orchestration |
| `useHumanReview` | Human review modal state |
| `useFinalOutput` | Final output view data |
| `useKeyboardShortcuts` | Keyboard navigation |
| `useStatusAnnouncements` | Accessibility announcements |
| `useResponsive` | Responsive breakpoint detection |

### 16.3 State Management ✅

- **React Query** for server state (documents, profiles)
- **Zustand** for UI state (`uiStore.ts`) and swarm state (`swarmStore.ts`)
- **React Hook Form** for form management

### 16.4 UI Components ✅

| Component | Location |
|-----------|----------|
| Button | `components/ui/Button.tsx` |
| Input | `components/ui/Input.tsx` |
| Select | `components/ui/Select.tsx` |
| Checkbox | `components/ui/Checkbox.tsx` |
| Modal | `components/ui/Modal.tsx` |
| TagInput | `components/ui/TagInput.tsx` |
| ConnectionStatusIndicator | `components/ui/ConnectionStatusIndicator.tsx` |
| KeyboardShortcutsModal | `components/ui/KeyboardShortcutsModal.tsx` |
| SkipLink | `components/ui/SkipLink.tsx` |
| VisuallyHidden | `components/ui/VisuallyHidden.tsx` |
| ResponsiveContainer | `components/ui/ResponsiveContainer.tsx` |

### 16.5 API Layer ✅

| Module | Purpose |
|--------|---------|
| `api/profiles.ts` | Company profile API calls |
| `api/documents.ts` | Document management API |
| `api/generation.ts` | Generation control API |
| `api/settings.ts` | LLM settings API |

---

*Document Version: 1.1*
*Status: Implementation Complete*
*Last Updated: 2025-01-15*
