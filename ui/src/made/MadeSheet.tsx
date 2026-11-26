import { PictureSheet } from '@/library/PictureSheet';
import type { LibraryItem } from '@/library/library-view';
import { DeleteMade } from './DeleteMade';
import { deleteQuestion } from './made-text';
import type { DeleteMade as Trash } from './use-delete-made';

interface MadeSheetProps {
  item: LibraryItem | null;
  trash: Trash;
  onClosed: () => void;
}

// The picture sheet for what Create and Rotate made, with Delete at its bottom.
export function MadeSheet({ item, trash, onClosed }: MadeSheetProps) {
  const { remove } = trash;
  const target = item?.made;

  const close = () => {
    remove.reset();
    onClosed();
  };

  const actions = target ? (
    <DeleteMade
      question={deleteQuestion(target)}
      isPending={remove.isPending}
      error={remove.error?.message ?? null}
      onDelete={() => remove.mutate(target, { onSuccess: close })}
    />
  ) : null;

  return <PictureSheet key={item?.key ?? ''} item={item} actions={actions} onClosed={close} />;
}
