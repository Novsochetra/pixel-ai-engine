import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { postUpload, type UploadSource } from '@/animate/animate-client';
import { SOURCES } from '@/animate/use-animate';
import type { JobView } from '@/jobs/jobs-client';
import { CURRENT_JOB, useCurrentJob } from '@/jobs/use-current-job';
import {
  fetchFormOptions,
  fetchGenerated,
  fetchLoras,
  fetchUploads,
  postGenerate,
  type LoraTask,
} from './create-client';

export const useFormOptions = () =>
  useQuery({ queryKey: ['create', 'options'], queryFn: fetchFormOptions, staleTime: Infinity });

export const useLoras = (task: LoraTask) =>
  useQuery({ queryKey: ['create', 'loras', task], queryFn: () => fetchLoras(task) });

const UPLOADS = ['create', 'uploads'];

export const useUploads = () => useQuery({ queryKey: UPLOADS, queryFn: fetchUploads });

// Animate lists the same uploads, so its list is asked for again too.
export function useReferenceUpload(onUploaded: (upload: UploadSource) => void) {
  const client = useQueryClient();

  return useMutation({
    mutationFn: postUpload,

    onSuccess: (upload: UploadSource) => {
      client.setQueryData(UPLOADS, (uploads: UploadSource[] = []) => [upload, ...uploads]);
      onUploaded(upload);
      client.invalidateQueries({ queryKey: UPLOADS });
      client.invalidateQueries({ queryKey: SOURCES });
    },
  });
}

// Each finished job may have drawn something, so its id is part of what the gallery asks for.
export function useGenerated() {
  const job = useCurrentJob().data?.job;
  const finished = job && job.status !== 'running' ? job.id : null;

  return useQuery({
    queryKey: ['create', 'generated', finished],
    queryFn: fetchGenerated,
    placeholderData: keepPreviousData,
  });
}

// The job status shows the new job at once, without waiting for its next poll.
export function useGenerate() {
  const client = useQueryClient();

  return useMutation({
    mutationFn: postGenerate,
    onSuccess: (view: JobView) => client.setQueryData(CURRENT_JOB, view),
  });
}
