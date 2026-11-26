import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import { PixelImage } from '@/library/PixelImage';
import type { LibraryItem } from '@/library/library-view';
import type { TurnedCharacter } from './rotate-client';
import { fromText, turnedItem } from './turned-view';

type TurnedQuery = UseQueryResult<{ characters: TurnedCharacter[] }>;

function TurnedCard({ character, onOpen }: { character: TurnedCharacter; onOpen: () => void }) {
  const item = turnedItem(character);

  return (
    <li>
      <button className="made-card" type="button" onClick={onOpen}>
        <span className="made-card__title">{item.title}</span>
        <span className="made-card__subtitle">
          {item.subtitle} · {fromText(character)}
        </span>
        <span className="turned-card__views">
          {character.views.map((view) => (
            <span className="turned-card__view" key={view.src}>
              <span className="turned-card__art pixel-art">
                <PixelImage src={view.src} alt={`${item.title}, ${view.label}`} />
              </span>
              <span className="turned-card__label">{view.label}</span>
            </span>
          ))}
        </span>
      </button>
    </li>
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

// Every character a rotate LoRA turned, newest first, its views side by side in turning order.
export function TurnedGallery({
  query,
  onOpen,
}: {
  query: TurnedQuery;
  onOpen: (item: LibraryItem) => void;
}) {
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
    <ul className="made-list" aria-label="Turned characters">
      {query.data.characters.map((character) => (
        <TurnedCard
          key={character.key}
          character={character}
          onOpen={() => onOpen(turnedItem(character))}
        />
      ))}
    </ul>
  );
}
