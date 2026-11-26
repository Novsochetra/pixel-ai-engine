import { charactersText, otherExports } from './run-data';
import type { StartBody, TrainingOptions } from './training-client';

interface MoreExportsProps {
  options: TrainingOptions;
  values: StartBody;
  onToggle: (name: string) => void;
}

export function MoreExports({ options, values, onToggle }: MoreExportsProps) {
  const others = otherExports(options, values);

  if (values.task !== 'create' || !others.length) {
    return null;
  }

  return (
    <fieldset className="source-checks">
      <legend className="form-field__label">More exports</legend>
      {others.map((entry) => (
        <label className="source-checks__source" key={entry.name}>
          <input
            type="checkbox"
            checked={values.moreExports.includes(entry.name)}
            onChange={() => onToggle(entry.name)}
          />
          <span className="source-checks__name">{entry.name}</span>
          <span className="source-checks__licence">{charactersText(entry.sources)}</span>
        </label>
      ))}
      <p className="form-note">Adds the characters of another export to this run.</p>
    </fieldset>
  );
}
