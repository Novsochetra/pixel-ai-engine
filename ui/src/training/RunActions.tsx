import { Link } from 'react-router';
import { NumberField } from '@/components/number-field/NumberField';
import { Picker } from '@/components/picker/Picker';
import { Stepper } from '@/components/stepper/Stepper';
import { addedSteps } from './run-view';
import { addStepsTarget } from './training-actions';
import type { Run, TrainingOptions } from './training-client';
import type { RunChoice } from './use-run-choice';

interface ActionProps {
  run: Run;
  choice: RunChoice;
  options: TrainingOptions;
}

// The daily habit is a few hundred steps more: "Steps to add" sets the target from the last step.
export function ResumeFields({ run, choice, options }: ActionProps) {
  const added = addedSteps(run, choice.target);
  const checkpoint = run.checkpoints.at(-1);
  const range = { min: run.step + 1, max: options.mostSteps };

  return (
    <>
      <NumberField
        label="Steps to add"
        value={Number.isNaN(choice.target) ? NaN : added}
        range={{ min: 1, max: options.mostSteps - run.step }}
        onChange={(more) => choice.setTarget(addStepsTarget(run, more))}
      />
      <NumberField
        label="Train to step"
        value={choice.target}
        range={range}
        onChange={choice.setTarget}
      />
      <button
        className="pill-button pill-button--tinted"
        type="button"
        onClick={() => choice.setTarget(addStepsTarget(run, options.defaults.addSteps))}
      >
        Add {options.defaults.addSteps} steps
      </button>
      <p className="form-note">
        {checkpoint
          ? `Goes on from ${checkpoint} with the run's own settings.`
          : 'No checkpoint yet, so it starts from the first step again.'}
      </p>
    </>
  );
}

export function TryoutFields({ run, choice, options }: ActionProps) {
  const { tryout } = choice;

  if (!tryout || !run.tryouts.length) {
    return <p className="form-note">This run has no checkpoint to try yet.</p>;
  }

  return (
    <>
      <Picker
        label="Checkpoint"
        value={tryout.checkpoint}
        options={run.tryouts}
        onChange={(checkpoint) => choice.changeTryout({ checkpoint })}
      />
      <Picker
        label="Model"
        value={tryout.model}
        options={options.models}
        isStacked
        onChange={(model) => choice.changeTryout({ model })}
      />
      <Stepper
        label="Test characters"
        value={tryout.characters}
        range={options.characters}
        onChange={(characters) => choice.changeTryout({ characters })}
      />
      <p className="form-note">
        Turns test characters from the export with this checkpoint. See them in Library, under
        Try-outs.
      </p>
    </>
  );
}

export function CreateRunNote() {
  return (
    <p className="form-note">
      A create run draws characters from words, so it is tried on the{' '}
      <Link to="/create">Create</Link> screen: pick it under Draw with.
    </p>
  );
}
