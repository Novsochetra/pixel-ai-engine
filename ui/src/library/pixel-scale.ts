const ZOOMS = [1, 2, 3, 4, 6, 8, 12, 16] as const;

// Pixel art stays sharp only at a whole-number scale: one source pixel becomes n × n screen
// pixels. A picture too big for its box shrinks by a whole factor instead.
export function fitScale(width: number, height: number, boxWidth: number, boxHeight: number) {
  if (!width || !height || !boxWidth || !boxHeight) {
    return 1;
  }

  const room = Math.min(boxWidth / width, boxHeight / height);

  return room >= 1 ? Math.min(Math.floor(room), ZOOMS.at(-1)!) : 1 / Math.ceil(1 / room);
}

export const zoomIn = (scale: number) => ZOOMS.find((zoom) => zoom > scale) ?? scale;

export const zoomOut = (scale: number) => ZOOMS.findLast((zoom) => zoom < scale) ?? scale;

export const canZoomIn = (scale: number) => scale < ZOOMS.at(-1)!;

export const canZoomOut = (scale: number) => scale > ZOOMS[0];

export const zoomText = (scale: number) =>
  scale >= 1 ? `${scale}×` : `1/${Math.round(1 / scale)}×`;
