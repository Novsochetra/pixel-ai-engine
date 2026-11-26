import { CornerDelete } from '@/made/CornerDelete';
import type { MadeTarget } from '@/made/made-client';
import type { AnimatedRun, Clip } from './animate-client';
import { clipText, runSubtitle, runTarget, type ClipChoice } from './clip-view';
import { SheetFrame } from './SheetFrame';

interface RunCardProps {
  run: AnimatedRun;
  chosen: ClipChoice | null;
  onChoose: (run: AnimatedRun, clip: Clip) => void;
  onDelete: (target: MadeTarget) => void;
}

// A clip shows its first frame still: only the player moves, so the gallery stays quiet.
function ClipTile({
  run,
  clip,
  isChosen,
  onChoose,
}: Omit<RunCardProps, 'chosen' | 'onDelete'> & { clip: Clip; isChosen: boolean }) {
  return (
    <li>
      <button
        className="clip-tile"
        type="button"
        aria-pressed={isChosen}
        aria-label={`${run.source}, ${clipText(clip)}`}
        onClick={() => onChoose(run, clip)}
      >
        <span className="clip-tile__art pixel-art">
          <SheetFrame src={clip.sheet} alt="" kept={clip.kept} frame={0} />
        </span>
        <span className="clip-tile__label">{clipText(clip)}</span>
      </button>
    </li>
  );
}

export function RunCard({ run, chosen, onChoose, onDelete }: RunCardProps) {
  const isThisRun = chosen?.folder === run.folder;

  return (
    <li className="run-card made-item">
      <CornerDelete target={runTarget(run)} onDelete={onDelete} />
      <h3 className="run-card__title">{run.source}</h3>
      <p className="run-card__subtitle">{runSubtitle(run)}</p>
      {run.subject ? <p className="run-card__subject">{run.subject}</p> : null}
      {run.clips.length ? (
        <ul className="run-card__clips" aria-label={`Clips of ${run.source}`}>
          {run.clips.map((clip) => (
            <ClipTile
              key={clip.id}
              run={run}
              clip={clip}
              isChosen={isThisRun && chosen?.clipId === clip.id}
              onChoose={onChoose}
            />
          ))}
        </ul>
      ) : (
        <p className="run-card__subject">
          No clips yet. A running job adds each clip when it is done.
        </p>
      )}
    </li>
  );
}
