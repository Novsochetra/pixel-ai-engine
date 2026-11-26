import { useState, type SyntheticEvent } from 'react';
import { fitScale } from '@/library/pixel-scale';
import { frameBox, frameCount } from './sprite-frames';

export interface SheetMeasure {
  count: number;
  fit: number;
}

interface SheetFrameProps {
  src: string;
  alt: string;
  kept: number;
  frame: number;
  scale?: number;
  onMeasure?: (measure: SheetMeasure) => void;
}

interface Size {
  width: number;
  height: number;
}

// One frame of a sprite sheet, through a window the size of a frame, at a whole-number scale that
// fits the box around it unless a zoom is given.
export function SheetFrame({ src, alt, kept, frame, scale, onMeasure }: SheetFrameProps) {
  const [sheet, setSheet] = useState<Size | null>(null);
  const [fit, setFit] = useState(1);
  const count = sheet ? frameCount(sheet.width, sheet.height, kept) : Math.max(kept, 1);

  function measure(event: SyntheticEvent<HTMLImageElement>) {
    const image = event.currentTarget;
    const box = image.parentElement!.parentElement!;
    const size = { width: image.naturalWidth, height: image.naturalHeight };
    const found = frameCount(size.width, size.height, kept);
    const scaled = fitScale(size.width / found, size.height, box.clientWidth, box.clientHeight);

    setSheet(size);
    setFit(scaled);
    onMeasure?.({ count: found, fit: scaled });
  }

  const box = sheet ? frameBox(sheet, count, frame % count)(scale ?? fit) : null;

  return (
    <span
      className="sheet-frame"
      data-loaded={box !== null}
      style={box ? { inlineSize: box.width, blockSize: box.height } : undefined}
    >
      <img
        className="sheet-frame__sheet"
        src={src}
        alt={alt}
        style={box ? { blockSize: box.height, translate: `${box.offset}px 0` } : undefined}
        onLoad={measure}
        draggable={false}
      />
    </span>
  );
}
