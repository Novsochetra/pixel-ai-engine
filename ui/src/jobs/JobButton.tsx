interface JobButtonProps {
  label: string;
  notReady: string | null;
  isBusy: boolean;
  isStarting: boolean;
  onRun: () => void;
}

function buttonText({ label, isBusy, isStarting }: Omit<JobButtonProps, 'notReady' | 'onRun'>) {
  if (isStarting) {
    return 'Starting…';
  }

  return isBusy ? 'Job running' : label;
}

// A screen's one primary action, which starts a job; while a job runs it waits, and says so.
export function JobButton({ label, notReady, isBusy, isStarting, onRun }: JobButtonProps) {
  const tip = isBusy ? 'Wait for the running job, or stop it first.' : `${label} (⌘↩)`;

  return (
    <button
      className="pill-button pill-button--primary"
      type="button"
      title={notReady ?? tip}
      aria-keyshortcuts="Meta+Enter"
      disabled={notReady !== null || isBusy || isStarting}
      onClick={onRun}
    >
      {buttonText({ label, isBusy, isStarting })}
    </button>
  );
}
