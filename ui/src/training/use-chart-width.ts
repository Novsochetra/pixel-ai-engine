import { useEffect, useRef, useState } from 'react';

// Drawn in real pixels, not a stretched viewBox, so the axis text keeps its size on a phone.
export function useChartWidth(fallback: number) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const element = ref.current;

    if (!element || typeof ResizeObserver === 'undefined') {
      return undefined;
    }

    const observer = new ResizeObserver(([entry]) => setWidth(entry?.contentRect.width ?? 0));

    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return { ref, width: width || fallback };
}
