import type { InputHTMLAttributes } from 'react';
import './Checkbox.css';

interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  hint?: string;
}

export function Checkbox({ label, hint, id, className = '', ...props }: CheckboxProps) {
  const checkboxId = id || label.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className={`checkbox-group ${className}`}>
      <label htmlFor={checkboxId} className="checkbox-group__label">
        <input
          id={checkboxId}
          type="checkbox"
          className="checkbox-group__input"
          {...props}
        />
        <span className="checkbox-group__checkmark" />
        <span className="checkbox-group__text">{label}</span>
      </label>
      {hint && <span className="checkbox-group__hint">{hint}</span>}
    </div>
  );
}
