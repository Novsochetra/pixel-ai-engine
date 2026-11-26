import { Picker } from '@/components/picker/Picker';
import { TextField } from '@/components/text-field/TextField';
import { estimateText } from './animate-checks';
import type { AnimateOptions, AnimateSources } from './animate-client';
import { actionLines, findMade, type AnimateValues } from './animate-form';
import { SourceField } from './SourceField';
import { ViewChecks } from './ViewChecks';
import type { AnimateForm as Form } from './use-animate-form';

interface FieldsProps {
  form: Form;
  options: AnimateOptions;
  sources: AnimateSources;
  values: AnimateValues;
}

function ActionFields({ form, options, values }: Omit<FieldsProps, 'sources'>) {
  const count = actionLines(values.actions).length;

  return (
    <>
      <TextField
        label="Actions, one a line"
        value={values.actions}
        maxLength={options.mostActions * (options.longestAction + 1)}
        placeholder={'idle\nwalk\nflaps its wings and hovers'}
        isMultiline
        isCounted={false}
        onChange={(actions) => form.change({ actions })}
      />
      <p className="form-note">
        {count} of at most {options.mostActions}. Each line is one clip. idle, walk and attack have
        ready words; any other line is used as you write it.
      </p>
    </>
  );
}

function VideoFields({ form, options, values }: Omit<FieldsProps, 'sources'>) {
  return (
    <>
      <Picker
        label="Video size"
        value={values.size}
        options={options.sizes}
        isStacked
        onChange={(size) => form.change({ size })}
      />
      <Picker
        label="Length"
        value={values.frames}
        options={options.frames}
        isStacked
        onChange={(frames) => form.change({ frames })}
      />
    </>
  );
}

// The inspector's form: the character, what it shows, its views and actions, then the video. Its
// last line says what is missing before Animate, or how long the clips will take.
export function AnimateForm(props: FieldsProps & { problem: string | null }) {
  const { form, options, sources, values, problem } = props;
  const made = findMade(sources, values.source);

  return (
    <form
      className="create-form"
      aria-label="New animation"
      onSubmit={(event) => event.preventDefault()}
    >
      <SourceField form={form} options={options} sources={sources} values={values} />
      <TextField
        label="What it shows"
        value={values.subject}
        maxLength={options.subjectLength}
        placeholder="a knight in grey armour with a blue cape, empty hands"
        isMultiline
        onChange={(subject) => form.change({ subject })}
      />
      <p className="form-note">
        Name only what the picture shows: a sword in the words gives the character a sword.
      </p>
      {made ? (
        <ViewChecks
          views={options.views}
          has={made.views}
          chosen={values.views}
          onChange={(views) => form.change({ views })}
        />
      ) : null}
      <ActionFields form={form} options={options} values={values} />
      <VideoFields form={form} options={options} values={values} />
      <p className="form-note" aria-live="polite">
        {problem ?? estimateText(values, options)}
      </p>
    </form>
  );
}
