export type JobStatus = 'running' | 'done' | 'failed' | 'stopped';

export interface Job {
  id: string;
  kind: string;
  title: string;
  status: JobStatus;
  stopping: boolean;
  startedAt: string;
  endedAt: string | null;
}

export interface JobView {
  job: Job | null;
  progress: number | null;
  step: string;
  log: string;
}

async function readJson<Reply>(reply: Response): Promise<Reply> {
  if (!reply.ok) {
    throw new Error(`The server answered ${reply.status}.`);
  }

  return reply.json();
}

export const fetchCurrentJob = () =>
  fetch('/api/jobs/current', { cache: 'no-store' }).then(readJson<JobView>);

export const stopJob = () => fetch('/api/jobs/stop', { method: 'POST' }).then(readJson<JobView>);
