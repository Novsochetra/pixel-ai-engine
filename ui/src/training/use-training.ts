import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { useCurrentJob } from '@/jobs/use-current-job';
import { fetchRuns, fetchTrainingOptions } from './training-client';

export const RUNS = ['training', 'runs'];
const TRAINING_POLL_MS = 30000;

// Each finished job may have trained a step, saved a checkpoint, or made a new run.
function useFinishedJob() {
  const job = useCurrentJob().data?.job;

  return job && job.status !== 'running' ? job.id : null;
}

export function useTrainingOptions() {
  const finished = useFinishedJob();

  return useQuery({
    queryKey: ['training', 'options', finished],
    queryFn: fetchTrainingOptions,
    placeholderData: keepPreviousData,
  });
}

// A run being trained logs a step about every half minute, so its chart is asked for that often.
export function useRuns() {
  const finished = useFinishedJob();

  return useQuery({
    queryKey: [...RUNS, finished],
    queryFn: fetchRuns,
    placeholderData: keepPreviousData,

    refetchInterval: (query) =>
      query.state.data?.runs.some((run) => run.isTraining) ? TRAINING_POLL_MS : false,
  });
}
