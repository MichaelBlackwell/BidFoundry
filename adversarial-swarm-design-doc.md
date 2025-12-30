# Adversarial Agentic Swarm for Small Business GovCon Strategy

## Design Document v1.1

> **Implementation Status:** ✅ Core system implemented with Blue Team, Red Team, and Orchestrator agents fully operational. Multi-provider LLM support (Anthropic Claude, Groq) with streaming enabled.

---

## 1. Executive Summary

This document outlines the architecture for an adversarial agentic swarm designed to produce high-quality business strategy documents for small businesses pursuing government contracts. The system employs a red team/blue team dynamic where competing and critiquing agents iteratively improve outputs through structured debate, challenge, and synthesis.

---

## 2. System Overview

### 2.1 Core Philosophy

The swarm operates on the principle that **better strategies emerge from rigorous challenge**. Rather than a single agent producing output, multiple agents with distinct adversarial roles collaborate through structured conflict to surface weaknesses, blind spots, and opportunities that a single perspective would miss.

### 2.2 Target Users

- Small businesses (typically < 500 employees)
- Companies new to government contracting
- Established contractors expanding into new agencies or contract vehicles
- BD/Capture teams with limited resources

### 2.3 Output Documents

The swarm produces the following strategy documents:

| Document Type | Purpose |
|---------------|---------|
| Capability Statement | Marketing collateral for agency outreach |
| Competitive Analysis | Assessment of competitive landscape for specific opportunities |
| SWOT Analysis | Internal strategic positioning assessment |
| BD Pipeline Plan | Opportunity prioritization and pursuit strategy |
| Proposal Strategy Outline | Win themes, discriminators, and approach for specific RFPs |
| Go-to-Market Strategy | Entry strategy for specific contract vehicles (GSA, GWACs, IDIQs) |
| Teaming Strategy | Partner identification and teaming arrangement recommendations |

---

## 3. Agent Architecture

### 3.1 Agent Taxonomy

The swarm consists of three agent categories:

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR LAYER                      │
│                    [Arbiter Agent]                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   BLUE TEAM   │     │   RED TEAM    │     │  SPECIALIST   │
│   (Builders)  │◄───►│  (Challengers)│◄───►│    POOL       │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

### 3.2 Blue Team Agents (Builders)

Blue team agents are responsible for **constructive output generation**.

> ✅ **All Blue Team agents implemented** in `agents/blue/` with document-specific templates and prompts.

#### 3.2.1 Strategy Architect ✅
- **Role**: Primary document drafter
- **Behavior**: Synthesizes inputs into coherent strategic narratives
- **Outputs**: Initial document drafts, revised versions after red team feedback
- **Perspective**: Optimistic, opportunity-focused
- **Implementation**: `agents/blue/strategy_architect.py` with specialized prompts

#### 3.2.2 Market Analyst ✅
- **Role**: Government market intelligence
- **Behavior**: Analyzes agency budgets, procurement trends, incumbent performance
- **Outputs**: Market sizing, opportunity identification, timing recommendations
- **Perspective**: Data-driven, trend-focused
- **Implementation**: `agents/blue/market_analyst.py` with market data models

#### 3.2.3 Compliance Navigator ✅
- **Role**: Regulatory and eligibility expert
- **Behavior**: Ensures strategies align with FAR/DFAR, small business regulations, and set-aside requirements
- **Outputs**: Compliance checklists, eligibility assessments, risk flags
- **Perspective**: Risk-aware, rule-adherent
- **Implementation**: `agents/blue/compliance_navigator.py` with FAR rules, small business rules, and set-aside rules

#### 3.2.4 Capture Strategist ✅
- **Role**: Win strategy development
- **Behavior**: Develops win themes, discriminators, and competitive positioning
- **Outputs**: Proposal themes, ghost team analysis, price-to-win guidance
- **Perspective**: Competition-focused, win-oriented
- **Implementation**: `agents/blue/capture_strategist.py` with specialized prompts

---

### 3.3 Red Team Agents (Challengers)

Red team agents are responsible for **critical evaluation and stress-testing**.

> ✅ **All Red Team agents implemented** in `agents/red/` with evaluation criteria and specialized prompts.

#### 3.3.1 Devil's Advocate ✅
- **Role**: Contrarian challenger
- **Behavior**: Systematically argues against proposed strategies; identifies logical flaws
- **Outputs**: Counterarguments, alternative interpretations, assumption challenges
- **Perspective**: Skeptical, adversarial
- **Implementation**: `agents/red/devils_advocate.py` with structured critique prompts

#### 3.3.2 Competitor Simulator ✅
- **Role**: Competitive threat modeling
- **Behavior**: Role-plays as likely competitors; predicts their strategies and responses
- **Outputs**: Competitor response scenarios, vulnerability assessments
- **Perspective**: Hostile, competitive
- **Implementation**: `agents/red/competitor_simulator.py` with role-play prompts

#### 3.3.3 Evaluator Simulator ✅
- **Role**: Government evaluator perspective
- **Behavior**: Scores and critiques strategies as a Source Selection Evaluation Board would
- **Outputs**: Mock evaluation scores, weakness identification, compliance gaps
- **Perspective**: Bureaucratic, criteria-focused
- **Implementation**: `agents/red/evaluator_simulator.py` with LPTA and Best Value evaluation criteria

#### 3.3.4 Risk Assessor ✅
- **Role**: Downside scenario planning
- **Behavior**: Identifies what could go wrong; stress-tests assumptions
- **Outputs**: Risk registers, mitigation requirements, worst-case scenarios
- **Perspective**: Pessimistic, failure-focused
- **Implementation**: `agents/red/risk_assessor.py` with risk taxonomy model

---

### 3.4 Specialist Agents (Domain Experts)

Specialist agents are **invoked on-demand** based on document type or industry.

> ⏳ **Planned for future implementation.** Agent registry supports specialist agents but none are currently implemented.

| Agent | Specialty | Invoked For | Status |
|-------|-----------|-------------|--------|
| GSA Specialist | GSA Schedule mechanics, pricing, compliance | GSA go-to-market strategies | Planned |
| SBIR/STTR Advisor | R&D contracting, tech transition | Technology companies, R&D strategies | Planned |
| Pricing Strategist | Cost modeling, price-to-win | Proposal strategies, competitive analysis | Planned |
| Past Performance Curator | Experience narrative development | Capability statements, proposals | Planned |
| Subcontracting Advisor | Teaming, mentor-protégé, JVs | Teaming strategies, large contract pursuits | Planned |
| Clearance Consultant | Security requirements, FCL processes | Classified opportunity strategies | Planned |

---

### 3.5 Arbiter Agent (Orchestrator) ✅

The Arbiter is the **meta-agent** that controls swarm behavior.

> ✅ **Fully implemented** in `agents/orchestrator/arbiter.py` with workflow, consensus detection, and synthesis.

**Responsibilities:**
- Assigns document requests to appropriate agent configurations ✅
- Manages debate rounds between red and blue teams ✅
- Determines when consensus is reached or forces resolution ✅
- Synthesizes final outputs from competing perspectives ✅
- Escalates unresolved conflicts to human review ✅
- Generates Red Team Reports for transparency ✅
- Real-time streaming of agent activity via MessageBus ✅

**Decision Authority:**
- Number of adversarial rounds (default: 3, configurable per request)
- Which specialist agents to invoke (based on document type configuration)
- When to terminate debate (consensus threshold or max rounds)
- Quality threshold for output acceptance (confidence scoring)

**Implementation Details:**
- `DocumentWorkflow` manages phase transitions (BlueBuild → RedAttack → BlueDefense → Synthesis)
- `ConsensusDetector` evaluates agreement between critique resolutions
- `DocumentSynthesizer` compiles final document with blue team contributions
- `RoundManager` tracks round progression and emits control messages

---

## 4. Interaction Patterns

> ✅ **Workflow fully implemented** with real-time streaming, message bus communication, and structured debate protocol.

### 4.1 Standard Document Generation Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│    (Company profile, opportunity details, strategic goals)       │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ROUND 1: BLUE TEAM BUILD                      │
│  Strategy Architect + relevant specialists produce initial draft │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ROUND 2: RED TEAM ATTACK                      │
│  All red team agents independently critique the draft            │
│  - Devil's Advocate: Logical challenges                          │
│  - Competitor Simulator: Competitive vulnerabilities             │
│  - Evaluator Simulator: Compliance/scoring gaps                  │
│  - Risk Assessor: Failure modes                                  │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ROUND 3: BLUE TEAM DEFENSE                    │
│  Blue team responds to critiques:                                │
│  - Accept and revise                                             │
│  - Rebut with evidence                                           │
│  - Acknowledge as known risk                                     │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ARBITER SYNTHESIS                             │
│  - Evaluates unresolved disputes                                 │
│  - Forces decisions on contested points                          │
│  - Compiles final document with confidence ratings               │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                        FINAL OUTPUT                              │
│  Strategy document + Red Team Report + Confidence Assessment     │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Adversarial Debate Protocol

Each critique/response cycle follows a structured format:

**Red Team Critique Structure:**
```
CRITIQUE ID: [unique identifier]
AGENT: [red team agent name]
TARGET: [specific section/claim being challenged]
CHALLENGE TYPE: [Logic | Evidence | Completeness | Risk | Compliance]
SEVERITY: [Critical | Major | Minor]
ARGUMENT: [detailed challenge]
EVIDENCE: [supporting data or reasoning]
SUGGESTED REMEDY: [how blue team might address]
```

**Blue Team Response Structure:**
```
RESPONSE TO: [critique ID]
DISPOSITION: [Accept | Rebut | Acknowledge]
ACTION: [revision made or rebuttal argument]
EVIDENCE: [supporting data if rebutting]
RESIDUAL RISK: [if acknowledging, explain accepted risk]
```

---

## 5. Document-Specific Configurations

### 5.1 Capability Statement

| Parameter | Configuration |
|-----------|---------------|
| Lead Agent | Past Performance Curator |
| Required Specialists | Industry-specific specialist |
| Red Team Focus | Evaluator Simulator (agency perspective) |
| Adversarial Rounds | 2 |
| Key Challenge Areas | Differentiation clarity, relevance to target agency |

### 5.2 Competitive Analysis

| Parameter | Configuration |
|-----------|---------------|
| Lead Agent | Market Analyst |
| Required Specialists | Pricing Strategist |
| Red Team Focus | Competitor Simulator |
| Adversarial Rounds | 3 |
| Key Challenge Areas | Competitor capability assumptions, market share estimates |

### 5.3 Proposal Strategy Outline

| Parameter | Configuration |
|-----------|---------------|
| Lead Agent | Capture Strategist |
| Required Specialists | Pricing Strategist, Compliance Navigator |
| Red Team Focus | Full red team engagement |
| Adversarial Rounds | 4 |
| Key Challenge Areas | Win theme credibility, price competitiveness, compliance gaps |

### 5.4 Go-to-Market Strategy

| Parameter | Configuration |
|-----------|---------------|
| Lead Agent | Strategy Architect |
| Required Specialists | Vehicle-specific specialist (GSA, GWAC, etc.) |
| Red Team Focus | Risk Assessor, Devil's Advocate |
| Adversarial Rounds | 3 |
| Key Challenge Areas | Timeline realism, resource requirements, ROI assumptions |

---

## 6. Quality Assurance Mechanisms

> ✅ **Confidence scoring and Red Team reports fully implemented** with section-level tracking and adjustable thresholds.

### 6.1 Confidence Scoring

Each output section receives a confidence score based on adversarial resolution:

| Score | Meaning | Criteria |
|-------|---------|----------|
| High (90-100%) | Strong consensus | No unresolved critical/major critiques |
| Medium (70-89%) | Qualified confidence | Minor unresolved critiques or acknowledged risks |
| Low (50-69%) | Significant uncertainty | Major unresolved disputes; human review recommended |
| Insufficient (<50%) | Requires rework | Critical unresolved issues; document not released |

### 6.2 Red Team Report

Every document is accompanied by a transparency report containing:

- Summary of all red team challenges raised
- Disposition of each challenge (accepted, rebutted, acknowledged)
- Unresolved disputes and arbiter decisions
- Residual risks explicitly accepted
- Minority opinions from dissenting agents

### 6.3 Human-in-the-Loop Triggers

The system escalates to human review when:

- Confidence score falls below 70%
- Red and blue teams reach impasse after maximum rounds
- Compliance Navigator flags regulatory uncertainty
- Risk Assessor identifies catastrophic risk scenarios
- Document involves novel situations outside training distribution

---

## 7. Data Inputs and Integrations

### 7.1 Required User Inputs

**Company Profile:**
- NAICS codes and size standards
- Past performance summaries
- Key personnel and certifications
- Current contract vehicles
- Small business certifications (8(a), HUBZone, SDVOSB, WOSB)

**Opportunity Context (if applicable):**
- Solicitation number or forecast opportunity
- Target agency and contracting office
- Known competitors
- Budget constraints
- Timeline requirements

### 7.2 External Data Sources

| Source | Data Provided | Used By |
|--------|---------------|---------|
| SAM.gov | Entity registration, exclusions, opportunities | Compliance Navigator, Market Analyst |
| FPDS | Historical contract data, incumbent analysis | Market Analyst, Competitor Simulator |
| USASpending | Agency spending patterns, contractor performance | Market Analyst |
| GovWin/Deltek | Opportunity intelligence, forecasts | Capture Strategist |
| Agency strategic plans | Mission priorities, budget justifications | Strategy Architect |

---

## 8. Extensibility and Customization

### 8.1 Adding New Document Types

New document types can be added by defining:

1. **Template schema**: Required sections and content structure
2. **Agent configuration**: Lead agent, specialists, red team focus
3. **Challenge rubric**: Document-specific evaluation criteria
4. **Adversarial depth**: Number of rounds, severity thresholds

### 8.2 Industry Customization

The specialist pool can be extended with industry-specific agents:

- Defense/Intel Specialist
- Healthcare/HHS Specialist
- IT/Cybersecurity Specialist
- Construction/Facilities Specialist
- Professional Services Specialist

### 8.3 Behavioral Tuning

Arbiter parameters allow tuning of adversarial intensity:

| Parameter | Low Setting | High Setting |
|-----------|-------------|--------------|
| `critique_threshold` | Only major issues | All observations |
| `consensus_requirement` | Simple majority | Full agreement |
| `devil_advocate_intensity` | Constructive pushback | Aggressive challenge |
| `risk_tolerance` | Accept moderate risks | Flag all risks |

---

## 9. Limitations and Guardrails

### 9.1 Known Limitations

- Cannot access non-public procurement intelligence
- Competitive analysis limited to publicly available information
- Cannot guarantee win outcomes or compliance determinations
- Pricing recommendations are directional, not definitive
- Does not replace legal review for teaming agreements

### 9.2 Ethical Guardrails

- No generation of misleading past performance claims
- No fabrication of capabilities or certifications
- Flags potential organizational conflicts of interest
- Refuses to generate content for apparent bid-rigging scenarios
- Maintains confidentiality boundaries between competing clients

---

## 10. Success Metrics

### 10.1 System Performance

| Metric | Target |
|--------|--------|
| Average confidence score | > 80% |
| Human escalation rate | < 15% |
| Red team challenge acceptance rate | 40-60% (healthy tension) |
| Average rounds to consensus | ≤ 3 |

### 10.2 User Outcomes (Longitudinal)

| Metric | Measurement |
|--------|-------------|
| Proposal win rate improvement | Pre/post comparison |
| Time to capability statement | Hours reduced |
| Pipeline qualification accuracy | Predicted vs. actual outcomes |
| User satisfaction | NPS and feedback scores |

---

## 11. Future Enhancements

### Phase 2 Considerations

- **Learning from outcomes**: Incorporate win/loss data to refine agent behaviors
- **Multi-company teaming simulation**: Model teaming negotiations between multiple parties
- **Real-time opportunity monitoring**: Proactive alerts when market conditions change
- **Proposal draft generation**: Extend from strategy to actual proposal content
- **Voice of customer integration**: Incorporate agency feedback and debrief data

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| BD | Business Development |
| FAR | Federal Acquisition Regulation |
| GWAC | Government-Wide Acquisition Contract |
| IDIQ | Indefinite Delivery/Indefinite Quantity |
| NAICS | North American Industry Classification System |
| SSEB | Source Selection Evaluation Board |
| PTW | Price to Win |

---

## Appendix B: Agent Interaction Matrix

| Agent | Collaborates With | Challenges | Challenged By |
|-------|-------------------|------------|---------------|
| Strategy Architect | All blue team | — | All red team |
| Market Analyst | Capture Strategist | — | Devil's Advocate, Competitor Sim |
| Compliance Navigator | All agents | — | Evaluator Simulator |
| Capture Strategist | Market Analyst, Pricing | — | Competitor Sim, Evaluator Sim |
| Devil's Advocate | — | All blue team | Strategy Architect (rebuttals) |
| Competitor Simulator | — | Capture Strategist, Market Analyst | — |
| Evaluator Simulator | — | All blue team | Compliance Navigator |
| Risk Assessor | — | Strategy Architect | — |
| Arbiter | All agents | Resolves disputes | — |

---

---

## 12. Implementation Architecture

### 12.1 Multi-Provider LLM Support ✅

The system supports multiple LLM providers with seamless switching:

| Provider | Models | Status |
|----------|--------|--------|
| Anthropic | Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus | ✅ Implemented |
| Groq | Llama 3.1 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma2 9B | ✅ Implemented |

**Features:**
- Streaming support for both providers
- Automatic retry with exponential backoff
- Per-agent model configuration
- Session-level provider/model switching via API

### 12.2 Communication Infrastructure ✅

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| MessageBus | Async pub/sub for agent communication | `comms/bus.py` |
| ConversationHistory | Tracks all agent interactions | `comms/history.py` |
| RoundManager | Manages debate round lifecycle | `comms/round.py` |
| Message Types | DRAFT, CRITIQUE, RESPONSE, CONTROL, STATUS | `comms/message.py` |

### 12.3 Document Templates ✅

All seven document types have structured templates:

| Template | File |
|----------|------|
| Capability Statement | `agents/blue/templates/capability_statement.py` |
| Competitive Analysis | `agents/blue/templates/competitive_analysis.py` |
| SWOT Analysis | `agents/blue/templates/swot.py` |
| BD Pipeline Plan | `agents/blue/templates/bd_pipeline.py` |
| Proposal Strategy | `agents/blue/templates/proposal_strategy.py` |
| Go-to-Market Strategy | `agents/blue/templates/go_to_market.py` |
| Teaming Strategy | `agents/blue/templates/teaming_strategy.py` |

### 12.4 Data Models ✅

| Model | Purpose | File |
|-------|---------|------|
| CompanyProfile | Company information for document context | `models/company_profile.py` |
| DocumentType | Enumeration of supported document types | `models/document_types.py` |
| Opportunity | Opportunity/solicitation context | `models/opportunity.py` |
| Critique | Structured red team critique format | `models/critique.py` |
| Response | Blue team response structure | `models/response.py` |
| Confidence | Section and overall confidence scoring | `models/confidence.py` |
| MarketData | Market analysis data structures | `models/market_data.py` |

---

*Document Version: 1.1*
*Status: Implementation Complete - Core Features*
*Last Updated: 2025-01-15*
