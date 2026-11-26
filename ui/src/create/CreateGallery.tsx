import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import { TURN_FPS } from '@/animate/sprite-frames';
import type { LibraryItem } from '@/library/library-view';
import type { MadeTarget } from '@/made/made-client';
import { MadeGrid, MadeTile } from '@/made/MadeTile';
import { StripArt } from '@/made/TileArt';
import type { GeneratedEntry } from './create-client';
import { galleryItem, tileText } from './create-view';

type GeneratedQuery = UseQueryResult<{ items: GeneratedEntry[] }>;

interface TileProps {
  entry: GeneratedEntry;
  onOpen: (item: LibraryItem) => void;
  onDelete: (target: MadeTarget) => void;
}

// The first character stands for its set; under the pointer it turns through its views.
function CreateTile({ entry, onOpen, onDelete }: TileProps) {
  const item = galleryItem(entry);
  const cover = item.pictures[0];

  return (
    <MadeTile
      title={item.title}
      subtitle={tileText(entry)}
      target={item.made!}
      fps={TURN_FPS}
      art={(frame, onCount) =>
        cover ? (
          <StripArt
            src={cover.src}
            alt={`${item.title}, ${cover.label}`}
            kept={0}
            frame={frame}
            onCount={onCount}
          />
        ) : null
      }
      onOpen={() => onOpen(item)}
      onDelete={onDelete}
    />
  );
}

function GalleryError({ query }: { query: GeneratedQuery }) {
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
    <EmptyState icon="warning" title="The gallery did not load" action={retry}>
      {query.error?.message} Check that the server runs, then try again.
    </EmptyState>
  );
}

interface GalleryProps {
  query: GeneratedQuery;
  onOpen: (item: LibraryItem) => void;
  onDelete: (target: MadeTarget) => void;
}

// What was made so far as a grid, newest first; a click opens its sheets large, the corner deletes it.
export function CreateGallery({ query, onOpen, onDelete }: GalleryProps) {
  if (query.isError) {
    return <GalleryError query={query} />;
  }

  if (!query.data) {
    return (
      <div className="create-loading">
        <Progress value={null} label="Loading what was made" />
      </div>
    );
  }

  const entries = query.data.items;

  if (!entries.length) {
    return (
      <EmptyState icon="create" title="Nothing made yet">
        Write what to draw, then Generate.
      </EmptyState>
    );
  }

  return (
    <MadeGrid label="Made so far">
      {entries.map((entry) => (
        <CreateTile key={entry.folder} entry={entry} onOpen={onOpen} onDelete={onDelete} />
      ))}
    </MadeGrid>
  );
}
