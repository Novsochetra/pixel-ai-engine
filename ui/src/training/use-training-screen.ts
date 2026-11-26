import { useMutation, useQueryClient } from '@tanstack/react-query';
import { usePrimaryShortcut } from '@/create/use-primary-shortcut';
import type { JobView } from '@/jobs/jobs-client';
import { CURRENT_JOB, useCurrentJob } from '@/jobs/use-current-job';
import { primaryPlan, type Plan, type PlanState } from './primary-plan';
import { modeOf, PRIMARY_LABELS, type Mode, type RunAction } from './training-actions';
import { useNewRunForm } from './use-new-run-form';
import { useRunChoice } from './use-run-choice';
import { RUNS, useRuns, useTrainingOptions } from './use-training';

// One mutation for the three POSTs: the toolbar has one button, so one error and one "Starting…".
function useSend() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: (post: () => Promise<JobView>) => post(),

    onSuccess: (view: JobView) => {
      client.setQueryData(CURRENT_JOB, view);
      client.invalidateQueries({ queryKey: RUNS });
    },
  });
}

// A run's screen whose run is not there (yet) must not offer to start a new one instead.
function screenPlan(
  name: string | null,
  action: RunAction,
  state: PlanState,
): { mode: Mode; plan: Plan } {
  if (name !== null && !state.run) {
    const problem = state.runs ? `No run called ${name}.` : 'The run is still loading.';

    return { mode: 'resume', plan: { problem, post: null } };
  }

  const mode = modeOf(state.run, action);

  return { mode, plan: primaryPlan(mode, state) };
}

// The runs' screen (no name) starts a new run; a run's own screen (its name) resumes or tries it.
export function useTrainingScreen(name: string | null) {
  const options = useTrainingOptions();
  const runs = useRuns();
  const newRun = useNewRunForm(options.data);
  const choice = useRunChoice(runs.data?.runs, options.data, name);
  const send = useSend();
  const isBusy = useCurrentJob().data?.job?.status === 'running';

  const state = { options: options.data, runs: runs.data?.runs, newRun: newRun.values, ...choice };
  const { mode, plan } = screenPlan(name, choice.action, state);

  const run = () => {
    if (plan.post && !isBusy && !send.isPending) {
      send.mutate(plan.post, { onSuccess: mode === 'new' ? newRun.clearName : undefined });
    }
  };

  usePrimaryShortcut(run);

  return {
    name,
    options,
    runs,
    newRun,
    choice,
    mode,
    problem: plan.problem,
    run,
    button: {
      label: PRIMARY_LABELS[mode],
      notReady: plan.problem,
      isBusy,
      isStarting: send.isPending,
    },
    error: send.error?.message ?? null,
    closeError: send.reset,
  };
}

export type TrainingScreenState = ReturnType<typeof useTrainingScreen>;
