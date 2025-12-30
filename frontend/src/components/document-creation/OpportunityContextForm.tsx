import type { OpportunityContext } from '../../types';
import { Input, TagInput } from '../ui';
import './OpportunityContextForm.css';

interface OpportunityContextFormProps {
  value: OpportunityContext;
  onChange: (context: OpportunityContext) => void;
}

export function OpportunityContextForm({ value, onChange }: OpportunityContextFormProps) {
  const updateField = <K extends keyof OpportunityContext>(
    field: K,
    fieldValue: OpportunityContext[K]
  ) => {
    onChange({ ...value, [field]: fieldValue });
  };

  return (
    <div className="opportunity-form">
      <h3 className="opportunity-form__label">Opportunity Context (optional)</h3>
      <div className="opportunity-form__fields">
        <div className="opportunity-form__row">
          <Input
            label="Solicitation #"
            placeholder="e.g., 75D30123R00001"
            value={value.solicitationNumber || ''}
            onChange={(e) => updateField('solicitationNumber', e.target.value || undefined)}
          />
          <Input
            label="Target Agency"
            placeholder="e.g., DHS, DoD, HHS"
            value={value.targetAgency || ''}
            onChange={(e) => updateField('targetAgency', e.target.value || undefined)}
          />
        </div>
        <div className="opportunity-form__field">
          <label className="opportunity-form__field-label">Known Competitors</label>
          <TagInput
            value={value.knownCompetitors || []}
            onChange={(tags) => updateField('knownCompetitors', tags.length > 0 ? tags : undefined)}
            placeholder="Type competitor name and press Enter"
          />
        </div>
        <div className="opportunity-form__row">
          <div className="opportunity-form__budget">
            <label className="opportunity-form__field-label">Budget Range</label>
            <div className="opportunity-form__budget-inputs">
              <Input
                type="number"
                placeholder="Min"
                value={value.budgetMin ?? ''}
                onChange={(e) =>
                  updateField(
                    'budgetMin',
                    e.target.value ? parseInt(e.target.value, 10) : undefined
                  )
                }
              />
              <span className="opportunity-form__budget-separator">-</span>
              <Input
                type="number"
                placeholder="Max"
                value={value.budgetMax ?? ''}
                onChange={(e) =>
                  updateField(
                    'budgetMax',
                    e.target.value ? parseInt(e.target.value, 10) : undefined
                  )
                }
              />
            </div>
          </div>
          <Input
            label="Due Date"
            type="date"
            value={
              value.dueDate
                ? new Date(value.dueDate).toISOString().split('T')[0]
                : ''
            }
            onChange={(e) =>
              updateField('dueDate', e.target.value ? new Date(e.target.value) : undefined)
            }
          />
        </div>
      </div>
    </div>
  );
}
