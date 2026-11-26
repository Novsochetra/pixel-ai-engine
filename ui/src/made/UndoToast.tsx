import { useEffect } from 'react';
import { Icon } from '@/components/icons';
import { readDuration } from '@/styles/motion-tokens.js';
import { deletedText } from './made-text';

// Without the tokens the wait would read as 0 and Undo would vanish before anyone saw it.
const UNDO_FALLBACK_MS = 8000;

interface UndoToastProps {
  title: string;
  isPending: boolean;
  error: string | null;
  onUndo: () => void;
  onDismiss: () => void;
}

// The deleted set waits in the trash; the toast offers it back for a while, then goes away.
export function UndoToast({ title, isPending, error, onUndo, onDismiss }: UndoToastProps) {
  useEffect(() => {
    if (error) {
      return;
    }

    const timer = window.setTimeout(
      onDismiss,
      readDuration(document, '--duration-undo') || UNDO_FALLBACK_MS,
    );

    return () => window.clearTimeout(timer);
  }, [error, onDismiss]);

  return (
    <div className="undo-toast" role="status">
      <span className="undo-toast__text">
        {error ? `Could not undo. ${error}` : deletedText(title)}
      </span>
      <button
        className="pill-button pill-button--glass"
        type="button"
        disabled={isPending}
        onClick={onUndo}
      >
        Undo
      </button>
      <button className="glass-button" type="button" aria-label="Close" onClick={onDismiss}>
        <Icon name="close" />
      </button>
    </div>
  );
}
