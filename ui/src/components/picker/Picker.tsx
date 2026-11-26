import { Icon } from '@/components/icons';
import './picker.css';

interface PickerProps {
  label: string;
  value: string;
  options: readonly { value: string; label: string }[];
  isStacked?: boolean;
  isDisabled?: boolean;
  onChange: (value: string) => void;
}

// A pop-up button: its label, then the chosen value, opening the system's own menu. Stacked, the
// value gets the whole width, for long choices in a narrow inspector.
export function Picker(props: PickerProps) {
  const { label, value, options, isStacked = false, isDisabled = false, onChange } = props;

  return (
    <label className={isStacked ? 'picker picker--stacked' : 'picker'}>
      <span className="picker__label">{label}</span>
      <select
        className="picker__select"
        value={value}
        disabled={isDisabled}
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
