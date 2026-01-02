// Core types for the Adversarial Swarm application

// Document Types
export type DocumentType =
  | 'capability-statement'
  | 'swot-analysis'
  | 'competitive-analysis'
  | 'bd-pipeline-plan'
  | 'proposal-strategy'
  | 'go-to-market-strategy'
  | 'teaming-strategy';

export const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  'capability-statement': 'Capability Statement',
  'swot-analysis': 'SWOT Analysis',
  'competitive-analysis': 'Competitive Analysis',
  'bd-pipeline-plan': 'BD Pipeline Plan',
  'proposal-strategy': 'Proposal Strategy',
  'go-to-market-strategy': 'Go-to-Market Strategy',
  'teaming-strategy': 'Teaming Strategy',
};

// Agent Types
export type AgentCategory = 'blue' | 'red' | 'specialist' | 'orchestrator';
export type AgentState = 'idle' | 'thinking' | 'typing' | 'complete' | 'waiting';
export type Severity = 'critical' | 'major' | 'minor' | 'observation';

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  category: AgentCategory;
  required?: boolean;
}

export interface AgentRuntimeState extends AgentInfo {
  state: AgentState;
  currentContent: string | null;
  target: string | null;
}

// Swarm Configuration
export type Intensity = 'light' | 'medium' | 'aggressive';
export type ConsensusType = 'majority' | 'supermajority' | 'unanimous';
export type RiskTolerance = 'conservative' | 'balanced' | 'aggressive';

export interface AgentSelection {
  [agentId: string]: boolean;
}

export interface EscalationThresholds {
  confidenceMin: number;
  criticalUnresolved: boolean;
  complianceUncertainty: boolean;
}

export interface SwarmConfig {
  intensity: Intensity;
  rounds: number;
  consensus: ConsensusType;
  blueTeam: AgentSelection;
  redTeam: AgentSelection;
  specialists: AgentSelection;
  riskTolerance: RiskTolerance;
  escalationThresholds: EscalationThresholds;
}

// Company Profile Types

// Business operational status
export type BusinessStatus =
  | 'Active'
  | 'Startup'
  | 'Pre-Revenue'
  | 'Dormant'
  | 'Dissolved';

// Type of ownership stake
export type OwnershipType =
  | 'Member'       // LLC
  | 'Shareholder'  // Corporation
  | 'Partner'      // Partnership
  | 'Sole Proprietor';

// Federal small business certification types
export type CertificationType =
  | '8(a)'
  | 'HUBZone'
  | 'SDVOSB'
  | 'VOSB'
  | 'WOSB'
  | 'EDWOSB'
  | 'Small Business'
  | 'Large Business'
  | 'GSA MAS'
  | 'GSA STARS III'
  | 'GSA OASIS'
  | 'GSA Alliant'
  | 'Facility Clearance'
  | 'ISO 9001'
  | 'ISO 27001'
  | 'CMMI DEV'
  | 'CMMC'
  | 'FedRAMP';

// CPARS performance rating scale
export type PerformanceRating =
  | 'Exceptional'
  | 'Very Good'
  | 'Satisfactory'
  | 'Marginal'
  | 'Unsatisfactory'
  | 'Not Rated';

// NAICS code with primary/secondary designation
export interface NAICSCode {
  code: string;
  description: string;
  isPrimary?: boolean;
  smallBusinessSizeStandard?: string;
}

// Physical address for business locations
export interface Address {
  street1: string;
  street2?: string;
  city: string;
  state: string;
  zipCode: string;
  country?: string; // defaults to "USA"
}

// Ownership stake in the company
export interface OwnershipStake {
  name: string;
  ownershipType: OwnershipType;
  percentage: number; // 0-100
  title?: string; // e.g., "Managing Member", "CEO"
  isVeteran?: boolean;
  isServiceDisabledVeteran?: boolean;
  isWoman?: boolean;
  isDisadvantaged?: boolean; // For 8(a) purposes
}

// Management team member (officers, managers, key personnel)
export interface ManagementMember {
  name: string;
  title: string; // e.g., "CEO", "CFO", "Managing Member"
  roleDescription?: string;
  email?: string;
  phone?: string;
}

// Employee residence location for HUBZone calculations
export interface EmployeeResidenceInfo {
  zipCode: string;
  employeeCount: number;
  isHubzone?: boolean;
}

// HUBZone-specific information for certification compliance
export interface HUBZoneInfo {
  principalOfficeInHubzone?: boolean;
  principalOfficeAddress?: Address;
  employeeResidences?: EmployeeResidenceInfo[];
  hubzoneDesignation?: string; // e.g., "Qualified Census Tract"
}

// Summary of prior federal contracting experience
export interface FederalContractingHistory {
  hasFederalContracts?: boolean;
  totalContracts?: number;
  totalValue?: number;
  firstContractDate?: string; // ISO date string
  agenciesWorkedWith?: string[];
}

// Company certification with validity dates
export interface Certification {
  certType: CertificationType;
  issuingAuthority: string;
  issueDate: string; // ISO date string
  expirationDate?: string; // ISO date string
  certificationNumber?: string;
  level?: string; // e.g., CMMC Level 2, CMMI Level 3
}

// Past performance record for a completed or ongoing contract
export interface PastPerformance {
  id: string;
  contractNumber: string;
  contractName: string;
  agency: string;
  contractingOffice?: string;

  // Contract details
  contractValue: number;
  periodOfPerformanceStart?: string; // ISO date string
  periodOfPerformanceEnd?: string; // ISO date string
  contractType: string; // FFP, T&M, Cost-Plus, etc.

  // Performance metrics
  overallRating: PerformanceRating;
  qualityRating?: PerformanceRating;
  scheduleRating?: PerformanceRating;
  costControlRating?: PerformanceRating;
  managementRating?: PerformanceRating;

  // Relevance
  naicsCodes: string[];
  description: string;
  keyAccomplishments: string[];
  relevanceKeywords: string[];

  // Reference
  referenceName?: string;
  referenceTitle?: string;
  referencePhone?: string;
  referenceEmail?: string;
}

// Key personnel information
export interface TeamMember {
  name: string;
  title: string;
  role: string; // Role on potential contract
  yearsExperience: number;
  clearanceLevel?: string;
  certifications: string[];
  education: string[];
  relevantExperience: string;
}

// Core competency or service offering
export interface CoreCapability {
  name: string;
  description: string;
  differentiators: string[];
  relevantNaics: string[];
  proofPoints: string[]; // References to past performance
  maturityLevel: 'Emerging' | 'Established' | 'Market Leader';
}

// Complete company profile for GovCon strategy development
export interface CompanyProfile {
  id: string;

  // Basic Information
  name: string;
  description?: string;
  dunsNumber?: string;
  ueiNumber?: string; // Unique Entity Identifier (replaced DUNS)
  cageCode?: string;

  // === Company Fundamentals ===
  formationDate?: string; // ISO date string - Legal business formation date
  businessStatus?: BusinessStatus;
  fiscalYearEnd?: string; // e.g., "December 31" or "September 30"

  // Size and Structure
  employeeCount?: number; // Current FTE count
  employeeHeadcount?: number; // Total headcount including contractors
  annualRevenue?: number; // Last fiscal year revenue
  revenueIsYtd?: boolean; // True if revenue is YTD for pre-revenue companies
  yearsInBusiness?: number;
  headquartersLocation?: string; // Legacy field - use principalAddress for full address

  // === Principal Place of Business ===
  principalAddress?: Address;

  // === Ownership & Control ===
  ownershipStructure?: OwnershipStake[];
  managementTeam?: ManagementMember[];

  // Socioeconomic Status Flags (for certification eligibility)
  veteranOwned?: boolean; // For VOSB certification
  serviceDisabledVeteranOwned?: boolean; // For SDVOSB certification
  womanOwned?: boolean; // For WOSB/EDWOSB certification
  economicallyDisadvantagedWomanOwned?: boolean; // For EDWOSB
  disadvantagedBusiness?: boolean; // For 8(a) certification

  // === Certification & Compliance ===
  samRegistrationStatus?: string; // "Active", "Inactive", "Pending", "Not Registered"
  samRegistrationDate?: string; // ISO date string
  samExpirationDate?: string; // ISO date string

  // Federal Contracting History
  federalContractingHistory?: FederalContractingHistory;

  // === Geographic Information (HUBZone) ===
  hubzoneInfo?: HUBZoneInfo;

  // GovCon Specific
  naicsCodes?: NAICSCode[];
  certifications?: Certification[];
  pastPerformance?: PastPerformance[];

  // Capabilities
  coreCapabilities?: CoreCapability[];
  keyPersonnel?: TeamMember[];

  // Strategic Context
  targetAgencies?: string[];
  geographicCoverage?: string[];
  securityClearances?: string[]; // Facility clearance levels

  // Teaming
  existingPrimeRelationships?: string[];
  existingSubRelationships?: string[];
  teamingPreferences?: string;

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}

// Simplified profile for API requests (string arrays for basic fields)
export interface CompanyProfileSimple {
  id: string;
  name: string;
  description?: string;
  naicsCodes?: string[];
  certifications?: string[];
  pastPerformance?: string[];
  fullProfile?: CompanyProfile; // Full rich profile when available
  createdAt: Date;
  updatedAt: Date;
}

// Opportunity Context
export interface OpportunityContext {
  solicitationNumber?: string;
  targetAgency?: string;
  knownCompetitors?: string[];
  budgetMin?: number;
  budgetMax?: number;
  dueDate?: Date;
}

// Document Generation
export type GenerationStatus =
  | 'idle'
  | 'configuring'
  | 'running'
  | 'review'
  | 'complete'
  | 'error';

export type Phase = 'blue-build' | 'red-attack' | 'blue-defense' | 'synthesis';

export interface DocumentRequest {
  documentType: DocumentType;
  companyProfileId: string;
  opportunityContext?: OpportunityContext;
  config: SwarmConfig;
}

export interface Critique {
  id: string;
  agentId: string;
  target: string;
  severity: Severity;
  content: string;
  suggestedRemedy?: string;
  timestamp: Date;
  /** Round number when this critique was raised */
  round: number;
  /** Phase when this critique was raised */
  phase: Phase;
  /** Status of the critique resolution */
  status?: 'pending' | 'accepted' | 'rebutted' | 'acknowledged';
}

export interface Response {
  id: string;
  agentId: string;
  critiqueId: string;
  content: string;
  accepted: boolean;
  timestamp: Date;
  /** Round number when this response was made */
  round: number;
  /** Phase when this response was made */
  phase: Phase;
}

export interface DocumentSection {
  id: string;
  title: string;
  content: string;
  confidence: number;
  unresolvedCritiques: number;
}

export interface DocumentDraft {
  id: string;
  sections: DocumentSection[];
  overallConfidence: number;
  updatedAt: Date;
}

export interface ConfidenceReport {
  overall: number;
  sections: Record<string, number>;
}

export interface GenerationMetrics {
  roundsCompleted: number;
  totalCritiques: number;
  criticalCount: number;
  majorCount: number;
  minorCount: number;
  acceptedCount: number;
  rebuttedCount: number;
  acknowledgedCount: number;
  timeElapsedMs: number;
}

export interface DebateEntry {
  id: string;
  round: number;
  phase: Phase;
  agentId: string;
  type: 'critique' | 'response' | 'synthesis' | 'draft' | 'orchestrator' | 'round-marker';
  content: string;
  timestamp: Date;
  severity?: Severity;  // For critique entries
  status?: 'pending' | 'accepted' | 'rebutted' | 'acknowledged';  // For critique entries
  category?: 'blue' | 'red' | 'orchestrator';  // For color coding - orchestrator = yellow
  metadata?: Record<string, unknown>;  // For additional data like consensus info
}

export interface RedTeamReport {
  entries: DebateEntry[];
  summary: string;
  critiquesBySeverity?: Record<string, number>;
  responsesByDisposition?: Record<string, number>;
}

export interface EscalationInfo {
  reasons: string[];
  disputes: Dispute[];
}

export interface Dispute {
  id: string;
  title: string;
  redPosition: string;
  bluePosition: string;
  arbiterNote?: string;
}

export interface AgentInsightsSummary {
  agentsContributed: Array<{
    role: string;
    name: string;
    has_content: boolean;
    has_sections: boolean;
  }>;
  keyFindings: string[];
}

export interface AgentInsights {
  marketIntelligence: Record<string, unknown>;
  captureStrategy: Record<string, unknown>;
  complianceStatus: Record<string, unknown>;
  summary: AgentInsightsSummary;
}

export interface FinalOutput {
  documentId: string;
  content: DocumentDraft;
  confidence: ConfidenceReport;
  redTeamReport: RedTeamReport;
  debateLog: DebateEntry[];
  metrics: GenerationMetrics;
  requiresHumanReview: boolean;
  escalation?: EscalationInfo;
  agentInsights?: AgentInsights;
}

// User
export interface User {
  id: string;
  email: string;
  name: string;
}

// Generated Document (for history)
export interface GeneratedDocument {
  id: string;
  type: DocumentType;
  title: string;
  companyProfileId: string;
  status: 'draft' | 'approved' | 'rejected';
  confidence: number;
  createdAt: Date;
  updatedAt: Date;
}

// UI State
export type OutputTab = 'document' | 'redteam' | 'debate' | 'metrics' | 'insights';

export interface UIState {
  sidebarCollapsed: boolean;
  debateTheaterWidth: number;
  previewExpanded: boolean;
  activeTab: OutputTab;
}

// Export Formats
export type ExportFormat = 'word' | 'pdf' | 'markdown' | 'share';
