import { type DocumentType, DOCUMENT_TYPE_LABELS } from '../../types';
import './DocumentTypeSelector.css';

interface DocumentTypeSelectorProps {
  value: DocumentType | null;
  onChange: (type: DocumentType) => void;
}

const DOCUMENT_TYPES: DocumentType[] = [
  'capability-statement',
  'swot-analysis',
  'competitive-analysis',
  'bd-pipeline-plan',
  'proposal-strategy',
  'go-to-market-strategy',
  'teaming-strategy',
];

export function DocumentTypeSelector({ value, onChange }: DocumentTypeSelectorProps) {
  return (
    <div className="document-type-selector">
      <h3 className="document-type-selector__label">Document Type</h3>
      <div className="document-type-selector__options">
        {DOCUMENT_TYPES.map((type) => (
          <label key={type} className="document-type-selector__option">
            <input
              type="radio"
              name="documentType"
              value={type}
              checked={value === type}
              onChange={() => onChange(type)}
              className="document-type-selector__radio"
            />
            <span className="document-type-selector__text">
              {DOCUMENT_TYPE_LABELS[type]}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
