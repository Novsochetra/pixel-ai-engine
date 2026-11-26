import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchCurrentJob, stopJob, type JobView } from './jobs-client';

const CURRENT_JOB = ['jobs', 'current'];
const RUNNING_POLL_MS = 2000;
const IDLE_POLL_MS = 10000;

// A running job is asked about often, so its progress moves; an idle server rarely, to see a job
// started from the terminal.
export function useCurrentJob() {
  return useQuery({
    queryKey: CURRENT_JOB,
    queryFn: fetchCurrentJob,

    refetchInterval: (query) =>
      query.state.data?.job?.status === 'running' ? RUNNING_POLL_MS : IDLE_POLL_MS,
  });
}

export function useStopJob() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: stopJob,
    onSuccess: (view: JobView) => client.setQueryData(CURRENT_JOB, view),
  });
}
