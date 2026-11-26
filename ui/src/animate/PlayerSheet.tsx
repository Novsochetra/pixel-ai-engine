import { Sheet } from '@/components/sheet/Sheet';
import { DeleteMade } from '@/made/DeleteMade';
import { deleteQuestion } from '@/made/made-text';
import type { DeleteMade as Trash } from '@/made/use-delete-made';
import type { AnimatedRun, Clip } from './animate-client';
import { runSubtitle, runTarget } from './clip-view';
import { SpritePlayer } from './SpritePlayer';

type Chosen = { run: AnimatedRun; clip: Clip };

interface PlayerSheetProps {
  chosen: Chosen | null;
  trash: Trash;
  onChoose: (run: AnimatedRun, clip: Clip) => void;
  onClosed: () => void;
}

function PlayerBody({
  chosen,
  trash,
  onChoose,
  onDeleted,
}: Omit<PlayerSheetProps, 'chosen' | 'onClosed'> & { chosen: Chosen; onDeleted: () => void }) {
  const { run, clip } = chosen;
  const target = runTarget(run);

  return (
    <>
      <p className="player-sheet__about">
        {[run.subject, runSubtitle(run)].filter(Boolean).join(' · ')}
      </p>
      <SpritePlayer
        key={run.folder}
        run={run}
        clip={clip}
        onChoose={(next) => onChoose(run, next)}
      />
      <DeleteMade
        question={deleteQuestion(target)}
        isPending={trash.remove.isPending}
        error={trash.remove.error?.message ?? null}
        onDelete={() => trash.remove.mutate(target, { onSuccess: onDeleted })}
      />
    </>
  );
}

// A run plays in a sheet over the gallery, so a run far down plays where it was opened.
export function PlayerSheet({ chosen, trash, onChoose, onClosed }: PlayerSheetProps) {
  const close = () => {
    trash.remove.reset();
    onClosed();
  };

  return (
    <Sheet title={chosen?.run.source ?? ''} isOpen={chosen !== null} onClosed={close}>
      {chosen ? (
        <PlayerBody chosen={chosen} trash={trash} onChoose={onChoose} onDeleted={close} />
      ) : null}
    </Sheet>
  );
}
