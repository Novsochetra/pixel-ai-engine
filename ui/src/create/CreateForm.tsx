import { Picker } from '@/components/picker/Picker';
import { Segmented } from '@/components/segmented/Segmented';
import { Stepper } from '@/components/stepper/Stepper';
import { TextField } from '@/components/text-field/TextField';
import type { Facing, FormOptions } from './create-client';
import { STANDING, type CreateValues } from './create-form';
import { ModelFields } from './ModelFields';
import type { CreateForm as Form } from './use-create-form';

interface FieldsProps {
  options: FormOptions;
  values: CreateValues;
  onChange: (next: Partial<CreateValues>) => void;
}

const facingLabel = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

function FacingField({ options, values, onChange }: FieldsProps) {
  const choices = options.facing.map((facing) => ({
    value: facing.value as Facing,
    label: facingLabel(facing.value),
  }));
  const meaning = options.facing.find((facing) => facing.value === values.facing)?.label;

  return (
    <div className="form-field">
      <span className="form-field__label" aria-hidden="true">
        Facing
      </span>
      <Segmented
        label="Facing"
        options={choices}
        value={values.facing}
        onChange={(facing) => onChange({ facing })}
      />
      <p className="form-note">Drawn {meaning}.</p>
    </div>
  );
}

function DrawingFields({ options, values, onChange }: FieldsProps) {
  return (
    <>
      <TextField
        label="What to draw"
        value={values.prompt}
        maxLength={options.promptLength}
        placeholder="a frog wizard with a staff"
        isMultiline
        onChange={(prompt) => onChange({ prompt })}
      />
      <TextField
        label="Pose"
        value={values.pose}
        maxLength={options.poseLength}
        placeholder={STANDING}
        onChange={(pose) => onChange({ pose })}
      />
      <FacingField options={options} values={values} onChange={onChange} />
      <Stepper
        label="Characters"
        value={values.characters}
        range={options.characters}
        onChange={(characters) => onChange({ characters })}
      />
      <Picker
        label="Sprite size"
        value={values.sprite}
        options={options.sprites}
        isStacked
        onChange={(sprite) => onChange({ sprite })}
      />
    </>
  );
}

// The inspector's form: what to draw first, then the models that draw and turn it.
export function CreateForm({ form }: { form: Form }) {
  const { options, values, change } = form;

  if (!options || !values) {
    return null;
  }

  return (
    <form
      className="create-form"
      aria-label="New character"
      onSubmit={(event) => event.preventDefault()}
    >
      <DrawingFields options={options} values={values} onChange={change} />
      <ModelFields form={form} values={values} options={options} />
    </form>
  );
}
