import { useEffect } from 'react';
import { SheetFrame } from '@/animate/SheetFrame';
import type { Picture } from '@/library/library-client';
import { PixelImage } from '@/library/PixelImage';

interface StripProps {
  src: string;
  alt: string;
  kept: number;
  frame: number;
  onCount: (count: number) => void;
}

// A sheet whose frames sit side by side: a Create turnaround or an animated clip.
export function StripArt({ src, alt, kept, frame, onCount }: StripProps) {
  return (
    <SheetFrame
      src={src}
      alt={alt}
      kept={kept}
      frame={frame}
      onMeasure={(measure) => onCount(measure.count)}
    />
  );
}

interface ViewsProps {
  title: string;
  views: readonly Picture[];
  frame: number;
  onCount: (count: number) => void;
}

// Views in their own files, stacked so each is loaded and sized before its turn comes.
export function ViewsArt({ title, views, frame, onCount }: ViewsProps) {
  useEffect(() => onCount(views.length), [onCount, views.length]);

  return (
    <span className="made-views">
      {views.map((view, i) => (
        <span className="made-views__view" key={view.src} aria-hidden={i !== frame}>
          <PixelImage src={view.src} alt={`${title}, ${view.label}`} />
        </span>
      ))}
    </span>
  );
}
