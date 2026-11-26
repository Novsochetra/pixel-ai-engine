import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import { PixelImage } from '@/library/PixelImage';
import type { LibraryItem } from '@/library/library-view';
import type { GeneratedEntry } from './create-client';
import { galleryItem } from './create-view';
import './made-card.css';

type GeneratedQuery = UseQueryResult<{ items: GeneratedEntry[] }>;

function MadeCard({ item, onOpen }: { item: LibraryItem; onOpen: () => void }) {
  return (
    <li>
      <button className="made-card" type="button" onClick={onOpen}>
        <span className="made-card__title">{item.title}</span>
        <span className="made-card__subtitle">{item.subtitle}</span>
        <span className="made-card__sheets">
          {item.pictures.map((sheet) => (
            <span className="made-card__sheet pixel-art" key={sheet.src}>
              <PixelImage src={sheet.src} alt={`${item.title}, ${sheet.label}`} />
            </span>
          ))}
        </span>
      </button>
    </li>
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

// What was made so far, newest first; a click opens its sheets large.
export function CreateGallery({
  query,
  onOpen,
}: {
  query: GeneratedQuery;
  onOpen: (item: LibraryItem) => void;
}) {
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

  const items = query.data.items.map(galleryItem);

  if (!items.length) {
    return (
      <EmptyState icon="create" title="Nothing made yet">
        Write what to draw, then Generate.
      </EmptyState>
    );
  }

  return (
    <ul className="made-list" aria-label="Made so far">
      {items.map((item) => (
        <MadeCard key={item.key} item={item} onOpen={() => onOpen(item)} />
      ))}
    </ul>
  );
}
