import { Sheet } from '@/components/sheet/Sheet';
import { DeleteConfirm } from './DeleteConfirm';
import type { MadeTarget } from './made-client';
import { deleteQuestion } from './made-text';
import type { DeleteMade } from './use-delete-made';

interface DeleteSheetProps {
  target: MadeTarget | null;
  trash: DeleteMade;
  onClosed: () => void;
}

// The question a card's trash button asks, in a small sheet; it closes once the set is deleted.
export function DeleteSheet({ target, trash, onClosed }: DeleteSheetProps) {
  const { remove } = trash;

  const close = () => {
    remove.reset();
    onClosed();
  };

  return (
    <Sheet title="Delete?" size="compact" isOpen={target !== null} onClosed={close}>
      {target ? (
        <>
          {remove.error ? <p className="delete-made__error">{remove.error.message}</p> : null}
          <DeleteConfirm
            question={deleteQuestion(target)}
            isPending={remove.isPending}
            onKeep={close}
            onDelete={() => remove.mutate(target, { onSuccess: close })}
          />
        </>
      ) : null}
    </Sheet>
  );
}
