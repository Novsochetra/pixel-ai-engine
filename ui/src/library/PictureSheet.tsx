import { useState, type ReactNode } from 'react';
import { Icon } from '@/components/icons';
import { Sheet } from '@/components/sheet/Sheet';
import { ItemDetails } from './ItemDetails';
import { PixelImage } from './PixelImage';
import { ZoomControls } from './ZoomControls';
import type { Picture } from './library-client';
import type { LibraryItem } from './library-view';
import './picture-sheet.css';

function ViewStrip({
  pictures,
  chosen,
  onChoose,
}: {
  pictures: readonly Picture[];
  chosen: number;
  onChoose: (index: number) => void;
}) {
  return (
    <div className="view-strip" role="group" aria-label="Views">
      {pictures.map((picture, i) => (
        <button
          className="view-strip__view pixel-art"
          type="button"
          key={picture.src}
          aria-pressed={i === chosen}
          aria-label={picture.label}
          title={picture.label}
          onClick={() => onChoose(i)}
        >
          <PixelImage src={picture.thumb ?? picture.src} alt="" />
        </button>
      ))}
    </div>
  );
}

function PictureViewer({ item }: { item: LibraryItem }) {
  const [chosen, setChosen] = useState(0);
  const [zoom, setZoom] = useState<number | null>(null);
  const [fit, setFit] = useState(1);
  const picture = item.pictures[chosen]!;

  function choose(index: number) {
    setChosen(index);
    setZoom(null);
  }

  return (
    <>
      <div className="picture-stage pixel-art">
        <PixelImage
          key={picture.src}
          src={picture.src}
          alt={`${item.title}, ${picture.label}`}
          scale={zoom ?? undefined}
          onFit={setFit}
        />
      </div>
      <div className="picture-controls">
        <ZoomControls scale={zoom ?? fit} onZoom={setZoom} />
        <a className="pill-button pill-button--tinted" href={picture.src} download>
          <Icon name="download" />
          Download
        </a>
      </div>
      {item.pictures.length > 1 ? (
        <ViewStrip pictures={item.pictures} chosen={chosen} onChoose={choose} />
      ) : null}
    </>
  );
}

// One picture large, at a whole-number zoom, with its other views, its details and any actions below.
export function PictureSheet({
  item,
  actions,
  onClosed,
}: {
  item: LibraryItem | null;
  actions?: ReactNode;
  onClosed: () => void;
}) {
  return (
    <Sheet title={item?.title ?? ''} isOpen={item !== null} onClosed={onClosed}>
      {item ? (
        <>
          <PictureViewer item={item} />
          <ItemDetails item={item} />
          {actions}
        </>
      ) : null}
    </Sheet>
  );
}
