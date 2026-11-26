import { Icon } from '@/components/icons';
import './picker.css';

interface PickerProps {
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}

// A pop-up button: its label, then the chosen value, opening the system's own menu.
export function Picker({ label, value, options, onChange }: PickerProps) {
  return (
    <label className="picker">
      <span className="picker__label">{label}</span>
      <select
        className="picker__select"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <span className="picker__chevron" aria-hidden="true">
        <Icon name="chevron" />
      </span>
    </label>
  );
}
