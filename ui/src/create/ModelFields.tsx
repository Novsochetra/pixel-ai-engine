import { Picker } from '@/components/picker/Picker';
import type { Choice, FormOptions } from './create-client';
import { createBody, drawWithNote, modelFor, type CreateValues } from './create-form';
import type { CreateForm } from './use-create-form';

const NO_CREATE_LORA = { value: '', label: 'None: the model as it is' };

interface GroupProps {
  title: string;
  note: string | null;
  lora: { label: string; value: string; choices: Choice[]; onChange: (value: string) => void };
  model: { label: string; value: string; onChange: (value: string) => void };
  models: Choice[];
}

function ModelGroup({ title, note, lora, model, models }: GroupProps) {
  return (
    <fieldset className="form-group">
      <legend className="form-group__title">{title}</legend>
      <Picker
        label={lora.label}
        value={lora.value}
        options={lora.choices}
        isStacked
        isDisabled={note !== null}
        onChange={lora.onChange}
      />
      {note ? <p className="form-note">{note}</p> : null}
      <Picker {...model} options={models} isStacked />
    </fieldset>
  );
}

interface ModelFieldsProps {
  form: CreateForm;
  values: CreateValues;
  options: FormOptions;
}

function drawingGroup({ form, values, options }: ModelFieldsProps): GroupProps {
  return {
    title: 'Drawing',
    note: drawWithNote(values),
    lora: {
      label: 'Draw with',
      value: createBody(values).drawWith,
      choices: [NO_CREATE_LORA, ...form.createLoras],

      onChange: (drawWith) =>
        form.change({
          drawWith,
          drawingModel: modelFor(form.createLoras, drawWith, options.defaults.model),
        }),
    },
    model: {
      label: 'Drawing model',
      value: values.drawingModel,
      onChange: (drawingModel) => form.change({ drawingModel }),
    },
    models: options.models,
  };
}

// A LoRA the server would refuse shows as none, with the reason under it.
export function ModelFields(props: ModelFieldsProps) {
  return <ModelGroup {...drawingGroup(props)} />;
}
