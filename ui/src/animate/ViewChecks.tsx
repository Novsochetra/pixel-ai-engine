import { toggleView } from './animate-form';
import { viewText } from './clip-view';

interface ViewChecksProps {
  views: readonly string[];
  has: readonly string[];
  chosen: readonly string[];
  onChange: (views: string[]) => void;
}

// One clip per view and action; a view the character has no sprite for cannot be picked.
export function ViewChecks({ views, has, chosen, onChange }: ViewChecksProps) {
  return (
    <fieldset className="view-checks">
      <legend className="form-field__label">Views</legend>
      {views.map((view) => (
        <label className="view-checks__view" key={view}>
          <input
            type="checkbox"
            checked={chosen.includes(view)}
            disabled={!has.includes(view)}
            onChange={() => onChange(toggleView(chosen, view, views))}
          />
          {viewText(view)}
        </label>
      ))}
    </fieldset>
  );
}
