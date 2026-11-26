import '@/components/text-field/text-field.css';

interface NumberFieldProps {
  label: string;
  value: number;
  range: { min: number; max: number };
  onChange: (value: number) => void;
}

// A whole number too big for a stepper's taps, such as training steps. Left empty it is NaN, so
// the form says the number is missing instead of quietly sending a zero.
export function NumberField({ label, value, range, onChange }: NumberFieldProps) {
  return (
    <label className="text-field">
      <span className="text-field__label">{label}</span>
      <input
        className="text-field__input"
        type="number"
        inputMode="numeric"
        min={range.min}
        max={range.max}
        step={1}
        value={Number.isNaN(value) ? '' : value}
        onChange={(event) => onChange(event.target.value === '' ? NaN : Number(event.target.value))}
      />
    </label>
  );
}
