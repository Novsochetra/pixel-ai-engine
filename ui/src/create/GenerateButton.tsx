interface GenerateButtonProps {
  isReady: boolean;
  isBusy: boolean;
  isStarting: boolean;
  onGenerate: () => void;
}

function buttonText({ isBusy, isStarting }: Pick<GenerateButtonProps, 'isBusy' | 'isStarting'>) {
  if (isStarting) {
    return 'Starting…';
  }

  return isBusy ? 'Job running' : 'Generate';
}

// The screen's one primary action; while a job runs it waits, and says so.
export function GenerateButton({ isReady, isBusy, isStarting, onGenerate }: GenerateButtonProps) {
  const tip = isBusy ? 'Wait for the running job, or stop it first.' : 'Generate (⌘↩)';

  return (
    <button
      className="pill-button pill-button--primary"
      type="button"
      title={isReady ? tip : 'Write what to draw first.'}
      aria-keyshortcuts="Meta+Enter"
      disabled={!isReady || isBusy || isStarting}
      onClick={onGenerate}
    >
      {buttonText({ isBusy, isStarting })}
    </button>
  );
}
