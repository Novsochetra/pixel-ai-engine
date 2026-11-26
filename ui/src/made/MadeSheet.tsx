import { PictureSheet } from '@/library/PictureSheet';
import type { LibraryItem } from '@/library/library-view';
import { DeleteMade } from './DeleteMade';
import { UndoToast } from './UndoToast';
import { deleteQuestion } from './made-text';
import { useDeleteMade } from './use-delete-made';
import './made.css';

type Made = ReturnType<typeof useDeleteMade>;

function DeleteAction({
  item,
  made,
  onDone,
}: {
  item: LibraryItem;
  made: Made;
  onDone: () => void;
}) {
  const { folder, characters } = item.made!;
  const { remove } = made;

  return (
    <DeleteMade
      question={deleteQuestion(item.title, characters)}
      isPending={remove.isPending}
      error={remove.error?.message ?? null}
      onDelete={() => remove.mutate({ folder, title: item.title }, { onSuccess: onDone })}
    />
  );
}

function Undo({ made }: { made: Made }) {
  const { deleted, restore, dismiss } = made;

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

// The picture sheet for what Create and Rotate made, with Delete; the toast outlives the sheet.
export function MadeSheet({ item, onClosed }: { item: LibraryItem | null; onClosed: () => void }) {
  const made = useDeleteMade();

  const close = () => {
    made.remove.reset();
    onClosed();
  };

  const actions = item?.made ? <DeleteAction item={item} made={made} onDone={close} /> : null;

  return (
    <>
      <PictureSheet key={item?.key ?? ''} item={item} actions={actions} onClosed={close} />
      <Undo made={made} />
    </>
  );
}
