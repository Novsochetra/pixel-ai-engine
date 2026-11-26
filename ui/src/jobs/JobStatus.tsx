import { useState } from 'react';
import { Progress } from '@/components/progress/Progress';
import { JobSheet } from './JobSheet';
import { percentText, statusLabel } from './job-text';
import { useCurrentJob } from './use-current-job';
import './jobs.css';

// The sidebar shows the latest job; a narrow screen floats only a running one above the tab bar.
export function JobStatus({ placement }: { placement: 'sidebar' | 'floating' }) {
  const { data: view } = useCurrentJob();
  const [isOpen, setOpen] = useState(false);
  const job = view?.job;

  if (!view || !job || (placement === 'floating' && job.status !== 'running')) {
    return null;
  }

  const isRunning = job.status === 'running';

  return (
    <>
      <button
        className={`job-status job-status--${placement}`}
        type="button"
        data-status={job.status}
        onClick={() => setOpen(true)}
      >
        <span className="job-status__title">{job.title}</span>
        <span className="job-status__state">
          {isRunning ? <Progress value={view.progress} label="Job progress" /> : null}
          <span className="job-status__label">
            {isRunning && view.progress !== null ? percentText(view.progress) : statusLabel(job)}
          </span>
        </span>
      </button>
      <JobSheet view={view} isOpen={isOpen} onClosed={() => setOpen(false)} />
    </>
  );
}
