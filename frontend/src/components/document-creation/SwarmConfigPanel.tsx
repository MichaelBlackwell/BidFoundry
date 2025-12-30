import { useState } from 'react';
import type { SwarmConfig, ConsensusType, RiskTolerance, AgentInfo, DocumentType } from '../../types';
import { IntensitySlider } from './IntensitySlider';
import { AgentChecklist } from './AgentChecklist';
import './SwarmConfigPanel.css';

interface SwarmConfigPanelProps {
  value: SwarmConfig;
  onChange: (config: SwarmConfig) => void;
  documentType: DocumentType | null;
}

// Agent definitions
const BLUE_TEAM_AGENTS: AgentInfo[] = [
  { id: 'strategy-architect', name: 'Strategy Architect', role: 'Lead strategist', category: 'blue', required: true },
  { id: 'market-analyst', name: 'Market Analyst', role: 'Market research', category: 'blue' },
  { id: 'compliance-navigator', name: 'Compliance Navigator', role: 'Regulatory compliance', category: 'blue' },
  { id: 'capture-strategist', name: 'Capture Strategist', role: 'Capture planning', category: 'blue' },
];

const RED_TEAM_AGENTS: AgentInfo[] = [
  { id: 'devils-advocate', name: "Devil's Advocate", role: 'Challenge assumptions', category: 'red' },
  { id: 'competitor-simulator', name: 'Competitor Simulator', role: 'Competitor perspective', category: 'red' },
  { id: 'evaluator-simulator', name: 'Evaluator Simulator', role: 'Government evaluator view', category: 'red' },
  { id: 'risk-assessor', name: 'Risk Assessor', role: 'Risk identification', category: 'red' },
];

const SPECIALIST_AGENTS: AgentInfo[] = [
  { id: 'gsa-specialist', name: 'GSA Specialist', role: 'GSA schedules expertise', category: 'specialist' },
  { id: 'sbir-sttr-advisor', name: 'SBIR/STTR Advisor', role: 'Small business programs', category: 'specialist' },
  { id: 'pricing-strategist', name: 'Pricing Strategist', role: 'Pricing strategy', category: 'specialist' },
  { id: 'clearance-consultant', name: 'Clearance Consultant', role: 'Security clearances', category: 'specialist' },
  { id: 'past-performance-curator', name: 'Past Performance Curator', role: 'Past performance', category: 'specialist' },
];

// Suggest specialists based on document type
function getSuggestedSpecialists(docType: DocumentType | null): string[] {
  switch (docType) {
    case 'capability-statement':
      return ['gsa-specialist', 'past-performance-curator'];
    case 'proposal-strategy':
      return ['pricing-strategist', 'past-performance-curator', 'compliance-navigator'];
    case 'competitive-analysis':
      return ['past-performance-curator'];
    case 'teaming-strategy':
      return ['gsa-specialist', 'clearance-consultant'];
    default:
      return ['past-performance-curator'];
  }
}

export function SwarmConfigPanel({ value, onChange, documentType }: SwarmConfigPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const updateConfig = <K extends keyof SwarmConfig>(field: K, fieldValue: SwarmConfig[K]) => {
    onChange({ ...value, [field]: fieldValue });
  };

  const updateEscalation = (
    field: keyof SwarmConfig['escalationThresholds'],
    fieldValue: number | boolean
  ) => {
    onChange({
      ...value,
      escalationThresholds: { ...value.escalationThresholds, [field]: fieldValue },
    });
  };

  const suggestedSpecialists = getSuggestedSpecialists(documentType);

  return (
    <div className="swarm-config">
      <button
        type="button"
        className="swarm-config__toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="swarm-config__toggle-icon">{isExpanded ? '▼' : '▶'}</span>
        <span className="swarm-config__toggle-label">Advanced: Swarm Configuration</span>
      </button>

      {isExpanded && (
        <div className="swarm-config__content">
          {/* Intensity & Rounds */}
          <div className="swarm-config__section">
            <IntensitySlider
              value={value.intensity}
              onChange={(intensity) => updateConfig('intensity', intensity)}
            />

            <div className="swarm-config__row">
              <div className="swarm-config__field">
                <label className="swarm-config__label">Adversarial Rounds</label>
                <select
                  className="swarm-config__select"
                  value={value.rounds}
                  onChange={(e) => updateConfig('rounds', parseInt(e.target.value, 10))}
                >
                  {[1, 2, 3, 4, 5].map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
                <span className="swarm-config__hint">(1-5)</span>
              </div>

              <div className="swarm-config__field">
                <label className="swarm-config__label">Consensus Requirement</label>
                <div className="swarm-config__radio-group">
                  {(['majority', 'supermajority', 'unanimous'] as ConsensusType[]).map((type) => (
                    <label key={type} className="swarm-config__radio">
                      <input
                        type="radio"
                        name="consensus"
                        value={type}
                        checked={value.consensus === type}
                        onChange={() => updateConfig('consensus', type)}
                      />
                      <span>{type === 'majority' ? 'Simple majority' : type === 'supermajority' ? 'Supermajority' : 'Full agreement'}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <hr className="swarm-config__divider" />

          {/* Agent Selection */}
          <div className="swarm-config__section">
            <div className="swarm-config__agents">
              <AgentChecklist
                title="Blue Team Agents"
                category="blue"
                agents={BLUE_TEAM_AGENTS}
                selection={value.blueTeam}
                onChange={(selection) => updateConfig('blueTeam', selection)}
              />
              <AgentChecklist
                title="Red Team Agents"
                category="red"
                agents={RED_TEAM_AGENTS}
                selection={value.redTeam}
                onChange={(selection) => updateConfig('redTeam', selection)}
              />
            </div>

            <div className="swarm-config__specialists">
              <div className="swarm-config__specialists-header">
                <span>Specialist Agents</span>
                {suggestedSpecialists.length > 0 && (
                  <span className="swarm-config__suggested-hint">
                    (auto-suggested based on document type)
                  </span>
                )}
              </div>
              <AgentChecklist
                title="Specialists"
                category="specialist"
                agents={SPECIALIST_AGENTS.map((agent) => ({
                  ...agent,
                  name: suggestedSpecialists.includes(agent.id)
                    ? `${agent.name} *`
                    : agent.name,
                }))}
                selection={value.specialists}
                onChange={(selection) => updateConfig('specialists', selection)}
              />
            </div>
          </div>

          <hr className="swarm-config__divider" />

          {/* Risk & Escalation */}
          <div className="swarm-config__section">
            <div className="swarm-config__field">
              <label className="swarm-config__label">Risk Tolerance</label>
              <div className="swarm-config__radio-group swarm-config__radio-group--vertical">
                {([
                  { value: 'conservative' as RiskTolerance, label: 'Conservative (flag all risks)' },
                  { value: 'balanced' as RiskTolerance, label: 'Balanced (flag medium+ risks)' },
                  { value: 'aggressive' as RiskTolerance, label: 'Aggressive (flag only critical risks)' },
                ]).map(({ value: riskValue, label }) => (
                  <label key={riskValue} className="swarm-config__radio">
                    <input
                      type="radio"
                      name="riskTolerance"
                      value={riskValue}
                      checked={value.riskTolerance === riskValue}
                      onChange={() => updateConfig('riskTolerance', riskValue)}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="swarm-config__field">
              <label className="swarm-config__label">Auto-Escalate to Human Review When:</label>
              <div className="swarm-config__checkbox-group">
                <label className="swarm-config__checkbox">
                  <input
                    type="checkbox"
                    checked={value.escalationThresholds.confidenceMin > 0}
                    onChange={(e) => updateEscalation('confidenceMin', e.target.checked ? 70 : 0)}
                  />
                  <span>
                    Confidence {'<'}{' '}
                    <input
                      type="number"
                      className="swarm-config__inline-input"
                      value={value.escalationThresholds.confidenceMin || 70}
                      onChange={(e) =>
                        updateEscalation('confidenceMin', parseInt(e.target.value, 10) || 0)
                      }
                      min={0}
                      max={100}
                      disabled={value.escalationThresholds.confidenceMin === 0}
                    />
                    %
                  </span>
                </label>
                <label className="swarm-config__checkbox">
                  <input
                    type="checkbox"
                    checked={value.escalationThresholds.criticalUnresolved}
                    onChange={(e) => updateEscalation('criticalUnresolved', e.target.checked)}
                  />
                  <span>Critical unresolved critiques</span>
                </label>
                <label className="swarm-config__checkbox">
                  <input
                    type="checkbox"
                    checked={value.escalationThresholds.complianceUncertainty}
                    onChange={(e) => updateEscalation('complianceUncertainty', e.target.checked)}
                  />
                  <span>Compliance uncertainty flagged</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
