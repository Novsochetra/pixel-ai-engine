import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import type { MadeTarget } from '@/made/made-client';
import type { AnimatedRun, Clip } from './animate-client';
import { type ClipChoice } from './clip-view';
import { RunCard } from './RunCard';
import './run-card.css';

type RunsQuery = UseQueryResult<{ runs: AnimatedRun[] }>;

interface GalleryProps {
  query: RunsQuery;
  chosen: ClipChoice | null;
  onChoose: (run: AnimatedRun, clip: Clip) => void;
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

// Every animated run, newest first; a click on a clip plays it, the corner deletes the run.
export function AnimatedGallery({ query, chosen, onChoose, onDelete }: GalleryProps) {
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
    <section className="animated-gallery" aria-labelledby="animated-title">
      <h2 className="animated-gallery__title" id="animated-title">
        Animated so far
      </h2>
      <ul className="run-list" aria-label="Animated so far">
        {query.data.runs.map((run) => (
          <RunCard
            key={run.folder}
            run={run}
            chosen={chosen}
            onChoose={onChoose}
            onDelete={onDelete}
          />
        ))}
      </ul>
    </section>
  );
}
