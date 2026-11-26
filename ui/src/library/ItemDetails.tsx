import type { ReactNode } from 'react';
import { FactList } from '@/components/fact-list/FactList';
import { CharacterRecords } from './CharacterRecords';
import type { LibraryItem, LibrarySummary } from './library-view';

export function ItemDetails({ item, action }: { item: LibraryItem; action?: ReactNode }) {
  return (
    <>
      <div className="library-details__head">
        <h2 className="library-details__title">{item.title}</h2>
        {item.subtitle ? <p className="library-details__subtitle">{item.subtitle}</p> : null}
      </div>
      <FactList facts={item.facts} />
      {action}
      {item.character ? <CharacterRecords id={item.character} /> : null}
    </>
  );
}

interface LibraryInspectorProps {
  item: LibraryItem | null;
  summary: readonly LibrarySummary[];
  onOpen: (item: LibraryItem) => void;
}

export function LibraryInspector({ item, summary, onOpen }: LibraryInspectorProps) {
  if (!item) {
    return (
      <>
        {summary.map((part) => (
          <FactList key={part.title} title={part.title} facts={part.facts} />
        ))}
        <p className="inspector-note">Select a picture to see its details.</p>
      </>
    );
  }

  const open = (
    <button className="pill-button pill-button--tinted" type="button" onClick={() => onOpen(item)}>
      Open
    </button>
  );

  return <ItemDetails item={item} action={open} />;
}
