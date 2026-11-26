import { FactList } from '@/components/fact-list/FactList';
import { Segmented } from '@/components/segmented/Segmented';
import { CreateRunNote, ResumeFields, TryoutFields } from './RunActions';
import { runFacts, runSubtitle } from './run-view';
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

// The selected run: what it is, then the action the toolbar's button runs, then its numbers.
export function RunDetails({ run, choice, options, mode }: RunDetailsProps) {
  const isCreate = run.task === 'create';

  return (
    <div className="run-details">
      <div className="run-details__head">
        <h2 className="run-details__title">{run.name}</h2>
        <p className="run-details__subtitle">{runSubtitle(run, options.models)}</p>
        <button className="pill-button pill-button--plain" type="button" onClick={choice.clear}>
          New run
        </button>
      </div>
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
      <FactList title="Run" facts={runFacts(run, options.models)} />
    </div>
  );
}
