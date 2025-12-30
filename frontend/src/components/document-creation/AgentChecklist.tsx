import type { AgentInfo, AgentCategory, AgentSelection } from '../../types';
import './AgentChecklist.css';

interface AgentChecklistProps {
  title: string;
  category: AgentCategory;
  agents: AgentInfo[];
  selection: AgentSelection;
  onChange: (selection: AgentSelection) => void;
}

const CATEGORY_COLORS: Record<AgentCategory, string> = {
  blue: 'var(--color-blue-team)',
  red: 'var(--color-red-team)',
  specialist: 'var(--color-specialist)',
  orchestrator: 'var(--color-arbiter)',
};

export function AgentChecklist({
  title,
  category,
  agents,
  selection,
  onChange,
}: AgentChecklistProps) {
  const handleToggle = (agentId: string, required?: boolean) => {
    if (required) return; // Can't toggle required agents
    onChange({
      ...selection,
      [agentId]: !selection[agentId],
    });
  };

  const handleToggleAll = (checked: boolean) => {
    const newSelection: AgentSelection = {};
    agents.forEach((agent) => {
      newSelection[agent.id] = agent.required ? true : checked;
    });
    onChange(newSelection);
  };

  const allSelected = agents.every((agent) => selection[agent.id]);
  const someSelected = agents.some((agent) => selection[agent.id]) && !allSelected;

  return (
    <div className="agent-checklist">
      <div
        className="agent-checklist__header"
        style={{ borderColor: CATEGORY_COLORS[category] }}
      >
        <label className="agent-checklist__select-all">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => {
              if (el) el.indeterminate = someSelected;
            }}
            onChange={(e) => handleToggleAll(e.target.checked)}
            className="agent-checklist__checkbox"
          />
          <span className="agent-checklist__title">{title}</span>
        </label>
        <span className="agent-checklist__count">
          {agents.filter((a) => selection[a.id]).length}/{agents.length}
        </span>
      </div>
      <ul className="agent-checklist__list">
        {agents.map((agent) => (
          <li key={agent.id} className="agent-checklist__item">
            <label
              className={`agent-checklist__agent ${
                agent.required ? 'agent-checklist__agent--required' : ''
              }`}
            >
              <input
                type="checkbox"
                checked={selection[agent.id] ?? false}
                onChange={() => handleToggle(agent.id, agent.required)}
                disabled={agent.required}
                className="agent-checklist__checkbox"
              />
              <span className="agent-checklist__name">
                {agent.name}
                {agent.required && (
                  <span className="agent-checklist__required-badge">required</span>
                )}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
