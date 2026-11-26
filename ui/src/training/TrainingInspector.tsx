import type { ReactNode } from 'react';
import { Progress } from '@/components/progress/Progress';
import { NewRunForm } from './NewRunForm';
import { RunDetails } from './RunDetails';
import type { TrainingScreenState } from './use-training-screen';

interface InspectorProps {
  screen: TrainingScreenState;
  error: ReactNode;
}

// A run's actions on its own screen, or the New run form on the runs' screen. The server's last
// refusal sits above, so it is read before the fields.
export function TrainingInspector({ screen, error }: InspectorProps) {
  const { options, newRun, choice } = screen;

  if (options.isError) {
    return (
      <div className="create-inspector-state">
        <p className="inspector-note">The form did not load. {options.error.message}</p>
        <button
          className="pill-button pill-button--glass"
          type="button"
          onClick={() => options.refetch()}
        >
          Try again
        </button>
      </div>
    );
  }

  if (!options.data || !newRun.values) {
    return (
      <div className="create-inspector-state">
        <Progress value={null} label="Loading the form" />
      </div>
    );
  }

  return (
    <>
      {error}
      {screen.name === null ? (
        <NewRunForm
          form={newRun}
          options={options.data}
          values={newRun.values}
          problem={screen.problem}
        />
      ) : null}
      {choice.run ? (
        <RunDetails run={choice.run} choice={choice} options={options.data} mode={screen.mode} />
      ) : null}
    </>
  );
}
