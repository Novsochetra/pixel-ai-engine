import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import type { MadeTarget } from '@/made/made-client';
import { MadeGrid, MadeTile } from '@/made/MadeTile';
import { StripArt } from '@/made/TileArt';
import type { AnimatedRun } from './animate-client';
import { clipText, runTarget, tileText } from './clip-view';
import { clipFps } from './sprite-frames';

type RunsQuery = UseQueryResult<{ runs: AnimatedRun[] }>;

interface TileProps {
  run: AnimatedRun;
  onOpen: (run: AnimatedRun) => void;
  onDelete: (target: MadeTarget) => void;
}

function GalleryError({ query }: { query: RunsQuery }) {
  const retry = (
    <button
      className="pill-button pill-button--glass"
      type="button"
      onClick={() => query.refetch()}
    >
      Try again
    </button>
  );

  return (
    <EmptyState icon="warning" title="The clips did not load" action={retry}>
      {query.error?.message} Check that the server runs, then try again.
    </EmptyState>
  );
}

// The run's first clip stands for it, still until the pointer is over it, then at its own speed.
function RunTile({ run, onOpen, onDelete }: TileProps) {
  const cover = run.clips[0];

  return (
    <MadeTile
      title={run.source}
      subtitle={tileText(run)}
      target={runTarget(run)}
      fps={cover ? clipFps(cover) : 1}
      art={(frame, onCount) =>
        cover ? (
          <StripArt
            src={cover.sheet}
            alt={`${run.source}, ${clipText(cover)}`}
            kept={cover.kept}
            frame={frame}
            onCount={onCount}
          />
        ) : null
      }
      onOpen={() => onOpen(run)}
      onDelete={onDelete}
    />
  );
}

interface GalleryProps {
  query: RunsQuery;
  onOpen: (run: AnimatedRun) => void;
  onDelete: (target: MadeTarget) => void;
}

// Every animated run as a grid, newest first; a click plays it in a sheet, the corner deletes it.
export function AnimatedGallery({ query, onOpen, onDelete }: GalleryProps) {
  if (query.isError) {
    return <GalleryError query={query} />;
  }

  if (!query.data) {
    return (
      <div className="create-loading">
        <Progress value={null} label="Loading the clips" />
      </div>
    );
  }

  if (!query.data.runs.length) {
    return (
      <EmptyState icon="animate" title="Nothing animated yet">
        Choose a character and its actions, then Animate.
      </EmptyState>
    );
  }

  return (
    <MadeGrid label="Animated so far">
      {query.data.runs.map((run) => (
        <RunTile key={run.folder} run={run} onOpen={onOpen} onDelete={onDelete} />
      ))}
    </MadeGrid>
  );
}
