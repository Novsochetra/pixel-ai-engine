import { Icon } from '@/components/icons';
import './search-field.css';

interface SearchFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

// iOS's search field: a magnifying glass, the label as its placeholder, and a clear button.
export function SearchField({ label, value, onChange }: SearchFieldProps) {
  return (
    <label className="search-field">
      <Icon name="search" />
      <input
        className="search-field__input"
        type="search"
        placeholder={label}
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => event.key === 'Escape' && value && onChange('')}
      />
    </label>
  );
}
