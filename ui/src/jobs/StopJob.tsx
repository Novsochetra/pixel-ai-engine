import { useState } from 'react';
import { useStopJob } from './use-current-job';

function StopConfirm({ onKeep, onStop }: { onKeep: () => void; onStop: () => void }) {
  return (
    <div className="job-sheet__confirm" role="group" aria-label="Stop the job?">
      <p>Stop this job? Work since its last saved step is lost.</p>
      <div className="job-sheet__actions">
        <button className="pill-button pill-button--plain" type="button" onClick={onKeep}>
          Keep running
        </button>
        <button className="pill-button pill-button--destructive" type="button" onClick={onStop}>
          Stop
        </button>
      </div>
    </div>
  );
}

// Stopping throws work away, so it asks first and says what is lost.
export function StopJob() {
  const stop = useStopJob();
  const [isAsking, setAsking] = useState(false);

  if (isAsking) {
    const confirm = () => {
      stop.mutate();
      setAsking(false);
    };

    return <StopConfirm onKeep={() => setAsking(false)} onStop={confirm} />;
  }

  return (
    <div className="job-sheet__actions">
      {stop.isError ? <p className="job-sheet__error">Could not stop the job. Try again.</p> : null}
      <button
        className="pill-button pill-button--destructive"
        type="button"
        disabled={stop.isPending}
        onClick={() => setAsking(true)}
      >
        {stop.isPending ? 'Stopping…' : 'Stop job'}
      </button>
    </div>
  );
}
