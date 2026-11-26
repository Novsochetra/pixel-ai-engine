import { Icon } from '@/components/icons';
import './stepper.css';

interface StepperProps {
  label: string;
  value: number;
  range: { min: number; max: number };
  onChange: (value: number) => void;
}

// iOS's stepper: the value with its label, and a minus and plus pair beside it.
export function Stepper({ label, value, range, onChange }: StepperProps) {
  return (
    <div className="stepper" role="group" aria-label={label}>
      <span className="stepper__label" aria-hidden="true">
        {label}
      </span>
      <output className="stepper__value" aria-live="polite">
        {value}
      </output>
      <span className="stepper__buttons">
        <button
          className="stepper__button"
          type="button"
          aria-label={`${label}: one less`}
          disabled={value <= range.min}
          onClick={() => onChange(value - 1)}
        >
          <Icon name="minus" />
        </button>
        <button
          className="stepper__button"
          type="button"
          aria-label={`${label}: one more`}
          disabled={value >= range.max}
          onClick={() => onChange(value + 1)}
        >
          <Icon name="plus" />
        </button>
      </span>
    </div>
  );
}
