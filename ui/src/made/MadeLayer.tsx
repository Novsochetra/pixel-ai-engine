import { DeleteSheet } from './DeleteSheet';
import { MadeSheet } from './MadeSheet';
import { UndoToast } from './UndoToast';
import type { DeleteMade } from './use-delete-made';
import type { MadeView } from './use-made-view';
import './made.css';

function Undo({ trash }: { trash: DeleteMade }) {
  const { deleted, restore, dismiss } = trash;

  if (!deleted) {
    return null;
  }

  return (
    <UndoToast
      title={deleted.title}
      isPending={restore.isPending}
      error={restore.error?.message ?? null}
      onUndo={() => restore.mutate(deleted)}
      onDismiss={dismiss}
    />
  );
}

// What floats over a gallery of made things: its picture sheet, the delete question and Undo,
// which stays after both sheets close.
export function MadeLayer({ view }: { view: MadeView }) {
  return (
    <>
      <MadeSheet item={view.viewing} trash={view.trash} onClosed={view.closeView} />
      <DeleteSheet target={view.asking} trash={view.trash} onClosed={view.closeAsk} />
      <Undo trash={view.trash} />
    </>
  );
}
