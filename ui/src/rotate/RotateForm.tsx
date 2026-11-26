import type { AnimateSources } from '@/animate/animate-client';
import { SourceField } from '@/animate/SourceField';
import { ViewChecks } from '@/animate/ViewChecks';
import { Picker } from '@/components/picker/Picker';
import type { RotateOptions } from './rotate-client';
import { turnText, type RotateValues } from './rotate-form';
import type { RotateForm as Form } from './use-rotate-form';

const NO_LORA = [{ value: '', label: 'None yet: train one in Training' }];

interface FieldsProps {
  form: Form;
  options: RotateOptions;
  values: RotateValues;
}

function TurningFields({ form, options, values }: FieldsProps) {
  return (
    <fieldset className="form-group">
      <legend className="form-group__title">Turning</legend>
      <Picker
        label="Turn with"
        value={values.lora}
        options={form.loras.length ? form.loras : NO_LORA}
        isStacked
        isDisabled={!form.loras.length}
        onChange={(lora) => form.change({ lora })}
      />
      <Picker
        label="Turning model"
        value={values.turningModel}
        options={options.models}
        isStacked
        onChange={(turningModel) => form.change({ turningModel })}
      />
      <Picker
        label="Sprite size"
        value={values.sprite}
        options={options.sprites}
        isStacked
        onChange={(sprite) => form.change({ sprite })}
      />
    </fieldset>
  );
}

// The inspector's form: the front view to turn, the LoRA and model that turn it, and the views.
// Its last line says what is missing before Rotate, or what Rotate will make.
export function RotateForm(
  props: FieldsProps & { sources: AnimateSources; problem: string | null },
) {
  const { form, options, sources, values, problem } = props;

  return (
    <form
      className="create-form"
      aria-label="New rotation"
      onSubmit={(event) => event.preventDefault()}
    >
      <SourceField
        picker={form}
        limits={options}
        sources={sources}
        source={values.source}
        view="front"
      />
      {form.kind === 'upload' ? (
        <p className="form-note">The PNG should show the character from the front.</p>
      ) : null}
      <TurningFields form={form} options={options} values={values} />
      <ViewChecks
        views={options.views}
        has={options.views}
        chosen={values.views}
        onChange={(views) => form.change({ views })}
      />
      <p className="form-note" aria-live="polite">
        {problem ?? turnText(values)}
      </p>
    </form>
  );
}
