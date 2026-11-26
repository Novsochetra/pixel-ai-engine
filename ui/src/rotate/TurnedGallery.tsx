import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import { TURN_FPS } from '@/animate/sprite-frames';
import type { LibraryItem } from '@/library/library-view';
import type { MadeTarget } from '@/made/made-client';
import { MadeGrid, MadeTile } from '@/made/MadeTile';
import { ViewsArt } from '@/made/TileArt';
import type { TurnedCharacter } from './rotate-client';
import { tileText, turnedItem } from './turned-view';

type TurnedQuery = UseQueryResult<{ characters: TurnedCharacter[] }>;

interface TileProps {
  character: TurnedCharacter;
  onOpen: (item: LibraryItem) => void;
  onDelete: (target: MadeTarget) => void;
}

// Under the pointer the character turns through its views in turning order.
function TurnedTile({ character, onOpen, onDelete }: TileProps) {
  const item = turnedItem(character);

  return (
    <MadeTile
      title={item.title}
      subtitle={tileText(character)}
      target={item.made!}
      fps={TURN_FPS}
      art={(frame, onCount) => (
        <ViewsArt title={item.title} views={character.views} frame={frame} onCount={onCount} />
      )}
      onOpen={() => onOpen(item)}
      onDelete={onDelete}
    />
  );
}

function GalleryError({ query }: { query: TurnedQuery }) {
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
    <EmptyState icon="warning" title="The turned characters did not load" action={retry}>
      {query.error?.message} Check that the server runs, then try again.
    </EmptyState>
  );
}

interface GalleryProps {
  query: TurnedQuery;
  onOpen: (item: LibraryItem) => void;
  onDelete: (target: MadeTarget) => void;
}

// Every character a rotate LoRA turned, as a grid, newest first.
export function TurnedGallery({ query, onOpen, onDelete }: GalleryProps) {
  if (query.isError) {
    return <GalleryError query={query} />;
  }

  if (!query.data) {
    return (
      <div className="create-loading">
        <Progress value={null} label="Loading the turned characters" />
      </div>
    );
  }

  if (!query.data.characters.length) {
    return (
      <EmptyState icon="rotate" title="Nothing turned yet">
        Choose a character with a front view, then Rotate.
      </EmptyState>
    );
  }

  return (
    <MadeGrid label="Turned characters">
      {query.data.characters.map((character) => (
        <TurnedTile key={character.key} character={character} onOpen={onOpen} onDelete={onDelete} />
      ))}
    </MadeGrid>
  );
}
