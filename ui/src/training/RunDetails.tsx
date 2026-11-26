import { Segmented } from '@/components/segmented/Segmented';
import { CreateRunNote, ResumeFields, TryoutFields } from './RunActions';
import type { Mode, RunAction } from './training-actions';
import type { Run, TrainingOptions } from './training-client';
import type { RunChoice } from './use-run-choice';

const ACTIONS: { value: RunAction; label: string }[] = [
  { value: 'resume', label: 'Resume' },
  { value: 'tryout', label: 'Try out' },
];

interface RunDetailsProps {
  run: Run;
  choice: RunChoice;
  options: TrainingOptions;
  mode: Mode;
}

// What the toolbar's button does to the run: resume it, or try a checkpoint of a rotate run.
export function RunDetails({ run, choice, options, mode }: RunDetailsProps) {
  const isCreate = run.task === 'create';

  return (
    <div className="run-details">
      <form
        className="create-form"
        aria-label={`${run.name}: ${mode === 'tryout' ? 'try out' : 'resume'}`}
        onSubmit={(event) => event.preventDefault()}
      >
        {isCreate ? null : (
          <Segmented
            label="Action"
            options={ACTIONS}
            value={choice.action}
            onChange={choice.chooseAction}
          />
        )}
        {mode === 'tryout' ? (
          <TryoutFields run={run} choice={choice} options={options} />
        ) : (
          <ResumeFields run={run} choice={choice} options={options} />
        )}
        {isCreate ? <CreateRunNote /> : null}
      </form>
    </div>
  );
}
