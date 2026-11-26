import { useState } from 'react';
import { Icon } from '@/components/icons';
import { DeleteConfirm } from './DeleteConfirm';

interface DeleteMadeProps {
  question: string;
  isPending: boolean;
  error: string | null;
  onDelete: () => void;
}

// Delete at the bottom of a picture sheet: it asks in place first, as the HIG asks of a
// destructive action.
export function DeleteMade({ question, isPending, error, onDelete }: DeleteMadeProps) {
  const [isAsking, setAsking] = useState(false);

  if (isAsking) {
    const confirm = () => {
      setAsking(false);
      onDelete();
    };

    return (
      <DeleteConfirm
        question={question}
        isPending={isPending}
        onKeep={() => setAsking(false)}
        onDelete={confirm}
      />
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
