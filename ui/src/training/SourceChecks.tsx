import type { ExportSource } from './training-client';
import { toggleSource } from './training-form';

interface SourceChecksProps {
  sources: readonly ExportSource[];
  chosen: readonly string[];
  nonCommercial: readonly string[];
  onChange: (sources: string[]) => void;
}

function NonCommercialNote({ names }: { names: readonly string[] }) {
  if (!names.length) {
    return null;
  }

  const which = names.length === 1 ? `${names[0]} has` : `${names.join(', ')} have`;

  return (
    <p className="form-note" role="status">
      {which} a non-commercial licence, so this run is for non-commercial use only.
    </p>
  );
}

// Each source with its licence beside it, so what the model may be used for is clear before it trains.
export function SourceChecks({ sources, chosen, nonCommercial, onChange }: SourceChecksProps) {
  const order = sources.map((source) => source.name);

  if (!sources.length) {
    return (
      <p className="form-note">
        This export lists no sources. Export again with uv run pixel export.
      </p>
    );
  }

  return (
    <fieldset className="source-checks">
      <legend className="form-field__label">Sources</legend>
      {sources.map((source) => (
        <label className="source-checks__source" key={source.name}>
          <input
            type="checkbox"
            checked={chosen.includes(source.name)}
            onChange={() => onChange(toggleSource(chosen, source.name, order))}
          />
          <span className="source-checks__name">{source.name}</span>
          <span className="source-checks__licence">
            {source.use && source.use !== 'train'
              ? `${source.licence}, for ${source.use}`
              : source.licence}
          </span>
        </label>
      ))}
      <NonCommercialNote names={nonCommercial} />
    </fieldset>
  );
}
