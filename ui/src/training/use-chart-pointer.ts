import { useState, type KeyboardEvent, type PointerEvent } from 'react';
import { nearestIndex, type Point, type Scale } from './loss-chart';

const KEY_MOVES: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1 };

// The crosshair snaps to the nearest drawn step; arrow keys walk it along for the keyboard.
export function useChartPointer(points: readonly Point[], scale: Scale) {
  const [index, setIndex] = useState<number | null>(null);
  const last = points.length - 1;

  return {
    index: index === null ? null : Math.min(index, last),

    onPointerMove: (event: PointerEvent<SVGSVGElement>) => {
      const left = event.currentTarget.getBoundingClientRect().left;

      setIndex(nearestIndex(points, scale.stepAt(event.clientX - left)));
    },

    onKeyDown: (event: KeyboardEvent<SVGSVGElement>) => {
      const move = KEY_MOVES[event.key];

      if (move !== undefined) {
        event.preventDefault();
        setIndex((current) => Math.max(0, Math.min(last, (current ?? last) + move)));
      }
    },

    onFocus: () => setIndex(last),
    clear: () => setIndex(null),
  };
}
