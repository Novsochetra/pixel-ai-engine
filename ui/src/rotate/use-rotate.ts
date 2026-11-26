import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useFinishedJob } from '@/animate/use-animate';
import type { JobView } from '@/jobs/jobs-client';
import { CURRENT_JOB } from '@/jobs/use-current-job';
import { fetchTryouts } from '@/library/library-client';
import { fetchRotated, fetchRotateOptions, postRotate } from './rotate-client';
import { rotateTryoutsView } from './rotate-tryouts';

export const useRotateOptions = () =>
  useQuery({ queryKey: ['rotate', 'options'], queryFn: fetchRotateOptions, staleTime: Infinity });

export function useRotated() {
  const finished = useFinishedJob();

  return useQuery({
    queryKey: ['rotate', 'turned', finished],
    queryFn: fetchRotated,
    placeholderData: keepPreviousData,
  });
}

export function useRotateTryouts(run: string) {
  return useQuery({
    queryKey: ['rotate', 'tryouts', run],
    queryFn: () => fetchTryouts(run).then(rotateTryoutsView),
    placeholderData: keepPreviousData,
  });
}

// The job status shows the new job at once, without waiting for its next poll.
export function useRotate() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: postRotate,
    onSuccess: (view: JobView) => client.setQueryData(CURRENT_JOB, view),
  });
}
