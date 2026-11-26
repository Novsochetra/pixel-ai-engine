import type { CSSProperties } from 'react';
import './segmented.css';

export interface SegmentedOption<Value extends string> {
  value: Value;
  label: string;
}

interface SegmentedProps<Value extends string> {
  label: string;
  options: readonly SegmentedOption<Value>[];
  value: Value;
  onChange: (value: Value) => void;
}

// a hairline sits between two options; it hides beside the thumb, as on iOS
const isBesideThumb = (separator: number, chosen: number) =>
  separator === chosen || separator === chosen + 1;

export function Segmented<Value extends string>(props: SegmentedProps<Value>) {
  const { label, options, value, onChange } = props;
  const chosen = Math.max(
    0,
    options.findIndex((option) => option.value === value),
  );
  const style = { '--segment': chosen, '--segments': options.length } as CSSProperties;

  return (
    <div className="segmented" role="group" aria-label={label} style={style}>
      <span className="segmented__thumb" aria-hidden="true" />
      {options.slice(1).map((option, i) => (
        <span
          className="segmented__separator"
          key={option.value}
          aria-hidden="true"
          data-hidden={isBesideThumb(i + 1, chosen)}
          style={{ '--separator': i + 1 } as CSSProperties}
        />
      ))}
      {options.map((option) => (
        <button
          className="segmented__option"
          type="button"
          key={option.value}
          aria-pressed={option.value === value}
          onClick={() => option.value !== value && onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
