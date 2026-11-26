import { useState } from 'react';
import { resumeTarget } from './run-view';
import { tryoutDefaults, type RunAction, type TryoutValues } from './training-actions';
import type { Run, TrainingOptions } from './training-client';

interface Choice {
  action: RunAction;
  target: number | null;
  tryout: Partial<TryoutValues>;
}

const NOTHING: Choice = { action: 'resume', target: null, tryout: {} };

// The run of this screen and what to do with it. Each run's screen starts from its own defaults.
export function useRunChoice(
  runs: readonly Run[] | undefined,
  options: TrainingOptions | undefined,
  name: string | null,
) {
  const [choice, setChoice] = useState<Choice>(NOTHING);
  const run = runs?.find((each) => each.name === name) ?? null;
  const isReady = run !== null && options !== undefined;

  return {
    run,
    action: choice.action,
    target: isReady ? (choice.target ?? resumeTarget(run, options.defaults.addSteps)) : NaN,
    tryout: isReady ? { ...tryoutDefaults(run, options), ...choice.tryout } : null,

    chooseAction: (action: RunAction) => setChoice((current) => ({ ...current, action })),
    setTarget: (target: number) => setChoice((current) => ({ ...current, target })),

    changeTryout: (next: Partial<TryoutValues>) =>
      setChoice((current) => ({ ...current, tryout: { ...current.tryout, ...next } })),
  };
}

export type RunChoice = ReturnType<typeof useRunChoice>;
