import { charactersText, REPEATS, setRepeat } from './run-data';
import type { ExportSource, StartBody } from './training-client';
import { toggleSource } from './training-form';

type Changes = Partial<Pick<StartBody, 'sources' | 'repeat'>>;

interface SourceChecksProps {
  sources: readonly ExportSource[];
  values: Pick<StartBody, 'sources' | 'repeat'>;
  nonCommercial: readonly string[];
  onChange: (changes: Changes) => void;
}

interface SourceRowProps {
  source: ExportSource;
  isChosen: boolean;
  times: number;
  onToggle: () => void;
  onRepeat: (times: number) => void;
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

function detailText(source: ExportSource) {
  const licence =
    source.use && source.use !== 'train' ? `${source.licence}, for ${source.use}` : source.licence;

  return source.count === null ? licence : `${charactersText([source])} · ${licence}`;
}

function SourceRow({ source, isChosen, times, onToggle, onRepeat }: SourceRowProps) {
  return (
    <div className="source-checks__row">
      <label className="source-checks__source">
        <input type="checkbox" checked={isChosen} onChange={onToggle} />
        <span className="source-checks__name">{source.name}</span>
        <span className="source-checks__licence">{detailText(source)}</span>
      </label>
      {isChosen ? (
        <select
          className="source-checks__repeat"
          aria-label={`Times to show ${source.name}`}
          title="Times each picture is shown"
          value={times}
          onChange={(event) => onRepeat(Number(event.target.value))}
        >
          {REPEATS.map((option) => (
            <option key={option} value={option}>
              ×{option}
            </option>
          ))}
        </select>
      ) : null}
    </div>
  );
}

// Each source with its characters and licence beside it, so what the model learns from, and may be
// used for, is clear before it trains.
export function SourceChecks({ sources, values, nonCommercial, onChange }: SourceChecksProps) {
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
        <SourceRow
          key={source.name}
          source={source}
          isChosen={values.sources.includes(source.name)}
          times={values.repeat[source.name] ?? 1}
          onToggle={() => onChange({ sources: toggleSource(values.sources, source.name, order) })}
          onRepeat={(times) => onChange({ repeat: setRepeat(values.repeat, source.name, times) })}
        />
      ))}
      <p className="form-note">
        ×5 shows each picture of a small source 5 times, so it is not lost.
      </p>
      <NonCommercialNote names={nonCommercial} />
    </fieldset>
  );
}
