import type { Job } from './jobs-client';

const STATUS_LABELS = {
  running: 'Running',
  done: 'Done',
  failed: 'Failed',
  stopped: 'Stopped',
} as const;

export function statusLabel(job: Job): string {
  return job.stopping ? 'Stopping…' : STATUS_LABELS[job.status];
}

export function percentText(progress: number | null): string {
  return progress === null ? '' : `${Math.round(progress * 100)}%`;
}

export function elapsedText(startedAt: string, endedAt: string | null, now: Date): string {
  const end = endedAt ? new Date(endedAt) : now;
  const seconds = Math.max(0, Math.round((end.getTime() - new Date(startedAt).getTime()) / 1000));

  if (seconds < 60) {
    return `${seconds} s`;
  }

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const rest = minutes % 60;

  return rest ? `${Math.floor(minutes / 60)} h ${rest} min` : `${minutes / 60} h`;
}
