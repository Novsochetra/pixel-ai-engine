import { useState } from 'react';
import { resumeTarget } from './run-view';
import { tryoutDefaults, type RunAction, type TryoutValues } from './training-actions';
import type { Run, TrainingOptions } from './training-client';

interface Choice {
  name: string | null;
  action: RunAction;
  target: number | null;
  tryout: Partial<TryoutValues>;
}

const NOTHING: Choice = { name: null, action: 'resume', target: null, tryout: {} };

// The selected run and what to do with it. Another run starts from its own defaults; the action
// (Resume or Try out) stays, as the person is likely to do the same to the next run.
export function useRunChoice(
  runs: readonly Run[] | undefined,
  options: TrainingOptions | undefined,
) {
  const [choice, setChoice] = useState<Choice>(NOTHING);
  const run = runs?.find((each) => each.name === choice.name) ?? null;
  const isReady = run !== null && options !== undefined;

  return {
    run,
    action: choice.action,
    target: isReady ? (choice.target ?? resumeTarget(run, options.defaults.addSteps)) : NaN,
    tryout: isReady ? { ...tryoutDefaults(run, options), ...choice.tryout } : null,

    select: (name: string) =>
      setChoice((current) =>
        current.name === name
          ? { ...NOTHING, action: current.action }
          : { ...NOTHING, action: current.action, name },
      ),

    clear: () => setChoice((current) => ({ ...NOTHING, action: current.action })),
    chooseAction: (action: RunAction) => setChoice((current) => ({ ...current, action })),
    setTarget: (target: number) => setChoice((current) => ({ ...current, target })),

    changeTryout: (next: Partial<TryoutValues>) =>
      setChoice((current) => ({ ...current, tryout: { ...current.tryout, ...next } })),
  };
}

export type RunChoice = ReturnType<typeof useRunChoice>;
