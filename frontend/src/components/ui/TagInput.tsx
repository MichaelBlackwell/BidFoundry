import { useState, useCallback, type KeyboardEvent, type ChangeEvent } from 'react';
import './TagInput.css';

interface TagInputProps {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  disabled?: boolean;
  id?: string;
}

export function TagInput({
  value,
  onChange,
  placeholder = 'Type and press Enter',
  disabled = false,
  id,
}: TagInputProps) {
  const [inputValue, setInputValue] = useState('');

  const addTag = useCallback(
    (tag: string) => {
      const trimmed = tag.trim();
      if (trimmed && !value.includes(trimmed)) {
        onChange([...value, trimmed]);
      }
      setInputValue('');
    },
    [value, onChange]
  );

  const removeTag = useCallback(
    (tagToRemove: string) => {
      onChange(value.filter((tag) => tag !== tagToRemove));
    },
    [value, onChange]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addTag(inputValue);
      } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
        removeTag(value[value.length - 1]);
      }
    },
    [inputValue, value, addTag, removeTag]
  );

  const handleChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
  }, []);

  return (
    <div className={`tag-input ${disabled ? 'tag-input--disabled' : ''}`}>
      <div className="tag-input__tags">
        {value.map((tag) => (
          <span key={tag} className="tag-input__tag">
            {tag}
            {!disabled && (
              <button
                type="button"
                className="tag-input__remove"
                onClick={() => removeTag(tag)}
                aria-label={`Remove ${tag}`}
              >
                x
              </button>
            )}
          </span>
        ))}
        <input
          id={id}
          type="text"
          className="tag-input__input"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={value.length === 0 ? placeholder : ''}
          disabled={disabled}
        />
      </div>
    </div>
  );
}
