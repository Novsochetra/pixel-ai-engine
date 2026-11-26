import { useState } from 'react';
import { Icon } from '@/components/icons';

interface DeleteMadeProps {
  question: string;
  isPending: boolean;
  error: string | null;
  onDelete: () => void;
}

// Deleting asks first and says what goes with it, as the HIG asks of a destructive action.
export function DeleteMade({ question, isPending, error, onDelete }: DeleteMadeProps) {
  const [isAsking, setAsking] = useState(false);

  if (isAsking) {
    const confirm = () => {
      setAsking(false);
      onDelete();
    };

    return (
      <div className="delete-made" role="group" aria-label="Delete?">
        <p className="delete-made__question">{question}</p>
        <div className="delete-made__actions">
          <button
            className="pill-button pill-button--glass"
            type="button"
            onClick={() => setAsking(false)}
          >
            Keep
          </button>
          <button className="pill-button pill-button--destructive" type="button" onClick={confirm}>
            Delete
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="delete-made__actions">
      {error ? <p className="delete-made__error">{error}</p> : null}
      <button
        className="pill-button pill-button--destructive"
        type="button"
        disabled={isPending}
        onClick={() => setAsking(true)}
      >
        <Icon name="trash" />
        {isPending ? 'Deleting…' : 'Delete'}
      </button>
    </div>
  );
}
