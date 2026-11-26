import { stepsProblem } from './training-form';
import type { ResumeBody, Run, TrainingOptions, TryoutBody } from './training-client';

export type Mode = 'new' | 'resume' | 'tryout';

export type RunAction = Exclude<Mode, 'new'>;

export const PRIMARY_LABELS: Record<Mode, string> = {
  new: 'Start training',
  resume: 'Resume',
  tryout: 'Try out',
};

export type TryoutValues = Omit<TryoutBody, 'run'>;

// A create run draws from text, which a try-out of turning views cannot show: only Resume is left.
export function modeOf(run: Run | null, action: RunAction): Mode {
  if (!run) {
    return 'new';
  }

  return run.task === 'create' ? 'resume' : action;
}

export const addStepsTarget = (run: Run, addSteps: number) => run.step + addSteps;

export const resumeProblem = (run: Run, target: number, options: TrainingOptions) =>
  stepsProblem(target, run.step + 1, options.mostSteps);

export const resumeBody = (run: Run, target: number): ResumeBody => ({
  run: run.name,
  steps: target,
});

export function tryoutDefaults(run: Run, options: TrainingOptions): TryoutValues {
  return {
    checkpoint: run.tryouts[0]?.value ?? '',
    model: options.defaults.tryoutModel,
    characters: options.characters.default,
  };
}

export function tryoutProblem(run: Run, values: TryoutValues): string | null {
  if (run.task === 'create') {
    return 'Try a create run on the Create screen.';
  }

  return values.checkpoint ? null : 'This run has no checkpoint to try yet.';
}

export const tryoutBody = (run: Run, values: TryoutValues): TryoutBody => ({
  run: run.name,
  ...values,
});
