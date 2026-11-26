interface DeleteConfirmProps {
  question: string;
  isPending: boolean;
  onKeep: () => void;
  onDelete: () => void;
}

// The question before a delete: what goes, then Keep beside the red Delete.
export function DeleteConfirm({ question, isPending, onKeep, onDelete }: DeleteConfirmProps) {
  return (
    <div className="delete-made" role="group" aria-label="Delete?">
      <p className="delete-made__question">{question}</p>
      <div className="delete-made__actions">
        <button className="pill-button pill-button--glass" type="button" onClick={onKeep}>
          Keep
        </button>
        <button
          className="pill-button pill-button--destructive"
          type="button"
          disabled={isPending}
          onClick={onDelete}
        >
          {isPending ? 'Deleting…' : 'Delete'}
        </button>
      </div>
    </div>
  );
}
