import { NumberField } from '@/components/number-field/NumberField';
import { Picker } from '@/components/picker/Picker';
import { Segmented } from '@/components/segmented/Segmented';
import { TextField } from '@/components/text-field/TextField';
import { SourceChecks } from './SourceChecks';
import type { Task, TrainingOptions } from './training-client';
import { findExport, nonCommercialSources, type NewRunValues } from './training-form';
import type { NewRunForm as Form } from './use-new-run-form';

const NAME_LENGTH = 40;

interface NewRunProps {
  form: Form;
  options: TrainingOptions;
  values: NewRunValues;
  problem: string | null;
}

const taskName = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);

function TaskField({ form, options, values }: Omit<NewRunProps, 'problem'>) {
  const choices = options.tasks.map((task) => ({
    value: task.value as Task,
    label: taskName(task.value),
  }));
  const meaning = options.tasks.find((task) => task.value === values.task)?.label.split(': ')[1];

  return (
    <div className="form-field">
      <span className="form-field__label" aria-hidden="true">
        Task
      </span>
      <Segmented
        label="Task"
        options={choices}
        value={values.task}
        onChange={(task) => form.change({ task })}
      />
      {meaning ? <p className="form-note">Learns to {meaning}.</p> : null}
    </div>
  );
}

function ModelFields({ form, options, values }: Omit<NewRunProps, 'problem'>) {
  return (
    <>
      <Picker
        label="Model"
        value={values.model}
        options={options.models}
        isStacked
        onChange={(model) => form.change({ model })}
      />
      <Picker
        label="Size"
        value={values.size}
        options={options.sizes}
        onChange={(size) => form.change({ size })}
      />
      <NumberField
        label="Steps"
        value={values.steps}
        range={{ min: 1, max: options.mostSteps }}
        onChange={(steps) => form.change({ steps })}
      />
      <p className="form-note">About 28 s a step at 256 px and 77 s at 512 px on an M1 Max.</p>
    </>
  );
}

// The inspector with no run selected: a new run, named first, then its data, then the model.
export function NewRunForm({ form, options, values, problem }: NewRunProps) {
  const exportChoices = options.exports.map((entry) => ({ value: entry.name, label: entry.name }));

  return (
    <form className="create-form" aria-label="New run" onSubmit={(event) => event.preventDefault()}>
      <TextField
        label="Name"
        value={values.name}
        maxLength={NAME_LENGTH}
        placeholder="rotate-v3"
        onChange={(name) => form.change({ name })}
      />
      <TaskField form={form} options={options} values={values} />
      {exportChoices.length ? (
        <Picker
          label="Export"
          value={values.export}
          options={exportChoices}
          isStacked
          onChange={form.chooseExport}
        />
      ) : (
        <p className="form-note">No export yet. Run uv run pixel export in dataset/ first.</p>
      )}
      <SourceChecks
        sources={findExport(options, values.export)?.sources ?? []}
        chosen={values.sources}
        nonCommercial={nonCommercialSources(options, values)}
        onChange={(sources) => form.change({ sources })}
      />
      <ModelFields form={form} options={options} values={values} />
      <p className="form-note" aria-live="polite">
        {problem ?? 'Ready to start. Training fills the Mac for hours; Stop ends it at any time.'}
      </p>
    </form>
  );
}
