import { useState, type SyntheticEvent } from 'react';
import { fitScale } from './pixel-scale';

interface PixelImageProps {
  src: string;
  alt: string;
  scale?: number;
  onFit?: (scale: number) => void;
}

interface Size {
  width: number;
  height: number;
}

// Drawn at a whole-number scale that fits its box, unless a zoom is given.
export function PixelImage({ src, alt, scale, onFit }: PixelImageProps) {
  const [size, setSize] = useState<Size | null>(null);
  const [fit, setFit] = useState(1);

  function measure(event: SyntheticEvent<HTMLImageElement>) {
    const image = event.currentTarget;
    const box = image.parentElement!;
    const found = fitScale(
      image.naturalWidth,
      image.naturalHeight,
      box.clientWidth,
      box.clientHeight,
    );

    setSize({ width: image.naturalWidth, height: image.naturalHeight });
    setFit(found);
    onFit?.(found);
  }

  const shown = scale ?? fit;
  const style = size
    ? { inlineSize: size.width * shown, blockSize: size.height * shown }
    : undefined;

  return (
    <img
      className="pixel-image"
      src={src}
      alt={alt}
      style={style}
      onLoad={measure}
      draggable={false}
    />
  );
}
