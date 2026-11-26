import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { JobView } from '@/jobs/jobs-client';
import { CURRENT_JOB, useCurrentJob } from '@/jobs/use-current-job';
import {
  fetchAnimated,
  fetchAnimateOptions,
  fetchAnimateSources,
  postAnimate,
  postUpload,
  type AnimateSources,
  type UploadSource,
} from './animate-client';

const SOURCES = ['animate', 'sources'];

// Each finished job may have made something: a clip here, or a character to animate.
function useFinishedJob() {
  const job = useCurrentJob().data?.job;

  return job && job.status !== 'running' ? job.id : null;
}

export const useAnimateOptions = () =>
  useQuery({ queryKey: ['animate', 'options'], queryFn: fetchAnimateOptions, staleTime: Infinity });

export function useAnimateSources() {
  const finished = useFinishedJob();

  return useQuery({
    queryKey: [...SOURCES, finished],
    queryFn: fetchAnimateSources,
    placeholderData: keepPreviousData,
  });
}

export function useAnimated() {
  const finished = useFinishedJob();

  return useQuery({
    queryKey: ['animate', 'runs', finished],
    queryFn: fetchAnimated,
    placeholderData: keepPreviousData,
  });
}

// The job status shows the new job at once, without waiting for its next poll.
export function useAnimate() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: postAnimate,
    onSuccess: (view: JobView) => client.setQueryData(CURRENT_JOB, view),
  });
}

const withUpload = (upload: UploadSource) => (sources?: AnimateSources) =>
  sources && { ...sources, uploads: [upload, ...sources.uploads] };

// The new PNG is in the list before the server is asked again, so the picker can show it at once.
export function useUpload(onUploaded: (upload: UploadSource) => void) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: postUpload,

    onSuccess: (upload: UploadSource) => {
      client.setQueriesData({ queryKey: SOURCES }, withUpload(upload));
      onUploaded(upload);
      client.invalidateQueries({ queryKey: SOURCES });
    },
  });
}
