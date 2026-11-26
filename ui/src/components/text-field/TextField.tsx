import './text-field.css';

interface TextFieldProps {
  label: string;
  value: string;
  maxLength: number;
  placeholder?: string;
  isMultiline?: boolean;
  isCounted?: boolean;
  onChange: (value: string) => void;
}

// A visible label over the field; a long text also shows how much room is left, unless its
// limit means nothing to the person (a list of lines counts its lines instead).
export function TextField(props: TextFieldProps) {
  const { label, value, maxLength, placeholder, isMultiline = false, onChange } = props;
  const { isCounted = isMultiline } = props;
  const Control = isMultiline ? 'textarea' : 'input';

  return (
    <label className="text-field">
      <span className="text-field__label">{label}</span>
      <Control
        className="text-field__input"
        value={value}
        maxLength={maxLength}
        placeholder={placeholder}
        rows={isMultiline ? 3 : undefined}
        onChange={(event) => onChange(event.target.value)}
      />
      {isCounted ? (
        <span className="text-field__count" aria-hidden="true">
          {value.length} / {maxLength}
        </span>
      ) : null}
    </label>
  );
}
