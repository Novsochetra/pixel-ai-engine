import { useEffect, useState } from 'react';
import { frameDelay, nextFrame } from '@/animate/sprite-frames';
import { REDUCED_MOTION, useMediaQuery } from '@/layout/use-media-query';

// A tile stays on its first frame and plays only under the pointer, so a full gallery stays quiet.
// With reduced motion it never moves; its sheet still plays on Play.
export function useHoverFrames(count: number, fps: number) {
  const isReduced = useMediaQuery(REDUCED_MOTION);
  const [isHovered, setHovered] = useState(false);
  const [frame, setFrame] = useState(0);
  const isPlaying = isHovered && !isReduced && count > 1;

  useEffect(() => {
    if (!isPlaying) {
      return;
    }

    const timer = window.setInterval(
      () => setFrame((current) => nextFrame(current, count)),
      frameDelay(fps),
    );

    return () => window.clearInterval(timer);
  }, [isPlaying, count, fps]);

  const leave = () => {
    setHovered(false);
    setFrame(0);
  };

  return {
    frame: count ? frame % count : 0,
    isPlaying,
    hover: { onPointerEnter: () => setHovered(true), onPointerLeave: leave },
  };
}
