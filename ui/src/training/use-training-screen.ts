import { useMutation, useQueryClient } from '@tanstack/react-query';
import { usePrimaryShortcut } from '@/create/use-primary-shortcut';
import type { JobView } from '@/jobs/jobs-client';
import { CURRENT_JOB, useCurrentJob } from '@/jobs/use-current-job';
import { primaryPlan } from './primary-plan';
import { modeOf, PRIMARY_LABELS } from './training-actions';
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

export function useTrainingScreen() {
  const options = useTrainingOptions();
  const runs = useRuns();
  const newRun = useNewRunForm(options.data);
  const choice = useRunChoice(runs.data?.runs, options.data);
  const send = useSend();
  const isBusy = useCurrentJob().data?.job?.status === 'running';

  const mode = modeOf(choice.run, choice.action);
  const plan = primaryPlan(mode, {
    options: options.data,
    runs: runs.data?.runs,
    newRun: newRun.values,
    ...choice,
  });

  const run = () => {
    if (plan.post && !isBusy && !send.isPending) {
      send.mutate(plan.post, { onSuccess: mode === 'new' ? newRun.clearName : undefined });
    }
  };

  usePrimaryShortcut(run);

  return {
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
