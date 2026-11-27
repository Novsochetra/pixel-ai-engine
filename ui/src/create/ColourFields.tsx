import { Picker } from '@/components/picker/Picker';
import type { FormOptions } from './create-client';
import { colourChoices, type CreateValues } from './create-form';

interface ColourFieldsProps {
  options: FormOptions;
  values: CreateValues;
  onChange: (next: Partial<CreateValues>) => void;
}

export function ColourFields({ options, values, onChange }: ColourFieldsProps) {
  return (
    <fieldset className="form-group">
      <legend className="form-group__title">Colours</legend>
      <Picker
        label="Palette"
        value={values.palette}
        options={options.palettes}
        isStacked
        onChange={(palette) => onChange({ palette })}
      />
      <Picker
        label="Max colours"
        value={String(values.colours)}
        options={colourChoices(options.colours)}
        isStacked
        onChange={(colours) => onChange({ colours: Number(colours) })}
      />
      <p className="form-note">
        Every pixel snaps to the palette after the model draws. Max colours limits each sprite.
      </p>
    </fieldset>
  );
}
