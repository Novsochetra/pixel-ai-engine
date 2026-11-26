import { useEffect, useRef } from 'react';
import { Progress } from '@/components/progress/Progress';
import { Sheet } from '@/components/sheet/Sheet';
import { StopJob } from './StopJob';
import { elapsedText, statusLabel } from './job-text';
import type { JobView } from './jobs-client';

interface JobSheetProps {
  view: JobView;
  isOpen: boolean;
  onClosed: () => void;
}

function JobLog({ log }: { log: string }) {
  const logRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const element = logRef.current;

    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }, [log]);

  return (
    <pre className="job-log" ref={logRef} tabIndex={0} aria-label="Job log">
      {log || 'Nothing written yet.'}
    </pre>
  );
}

export function JobSheet({ view, isOpen, onClosed }: JobSheetProps) {
  const job = view.job!;
  const isRunning = job.status === 'running';

  return (
    <Sheet title={job.title} isOpen={isOpen} onClosed={onClosed}>
      <p className="job-sheet__meta" data-status={job.status}>
        {statusLabel(job)} · {elapsedText(job.startedAt, job.endedAt, new Date())}
      </p>
      {isRunning ? <Progress value={view.progress} label="Job progress" /> : null}
      {view.step ? <p className="job-sheet__step">{view.step}</p> : null}
      <JobLog log={view.log} />
      {isRunning ? <StopJob /> : null}
    </Sheet>
  );
}
