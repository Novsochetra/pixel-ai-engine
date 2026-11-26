import type { TryoutList } from '@/library/library-client';
import type { LibraryNotice, LibraryView } from '@/library/library-view';
import { tryoutsView } from '@/library/tryout-view';

const NO_ROTATIONS: LibraryNotice = {
  title: 'No turned test characters in this run',
  text: 'Pick another run, or try a rotate LoRA on the test characters. In training/, run',
  command: 'uv run pixel-train tryout --no-create --lora rotate-v2',
};

// Only the rotations: a try-out's text-to-character pictures belong with Create.
export function rotateTryoutsView(list: TryoutList): LibraryView {
  const run = list.run && {
    ...list.run,
    groups: list.run.groups.filter((group) => group.character !== null),
  };
  const view = tryoutsView({ ...list, run });

  return run ? { ...view, empty: NO_ROTATIONS } : view;
}
