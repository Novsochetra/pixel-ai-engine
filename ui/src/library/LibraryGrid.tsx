import { PixelImage } from './PixelImage';
import type { LibraryItem, LibrarySection } from './library-view';
import './library-tile.css';

interface LibraryGridProps {
  sections: readonly LibrarySection[];
  selectedKey: string | undefined;
  onSelect: (item: LibraryItem) => void;
  onOpen: (item: LibraryItem) => void;
}

function Tile({
  item,
  isSelected,
  onSelect,
  onOpen,
}: {
  item: LibraryItem;
  isSelected: boolean;
  onSelect: () => void;
  onOpen: () => void;
}) {
  const cover = item.pictures[0]!;

  return (
    <li>
      <button
        className="library-tile"
        type="button"
        aria-pressed={isSelected}
        onClick={onSelect}
        onDoubleClick={onOpen}
      >
        <span className="library-tile__art pixel-art">
          <PixelImage src={cover.thumb ?? cover.src} alt={`${item.title}, ${cover.label}`} />
        </span>
        <span className="library-tile__title">{item.title}</span>
        <span className="library-tile__subtitle">{item.subtitle}</span>
      </button>
    </li>
  );
}

export function LibraryGrid({ sections, selectedKey, onSelect, onOpen }: LibraryGridProps) {
  return sections.map((section) => (
    <section
      className="library-section"
      key={section.title}
      aria-label={section.title || 'Pictures'}
    >
      {section.title ? <h2 className="library-section__title">{section.title}</h2> : null}
      <ul className="library-grid">
        {section.items.map((item) => (
          <Tile
            key={item.key}
            item={item}
            isSelected={item.key === selectedKey}
            onSelect={() => onSelect(item)}
            onOpen={() => onOpen(item)}
          />
        ))}
      </ul>
    </section>
  ));
}
