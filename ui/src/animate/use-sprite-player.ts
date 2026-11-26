import { useEffect, useState } from 'react';
import { REDUCED_MOTION, useMediaQuery } from '@/layout/use-media-query';
import { frameDelay, nextFrame, previousFrame } from './sprite-frames';

// With reduced motion the clip waits for Play, so nothing moves that the person did not start.
export function useSpritePlayer(count: number, startFps: number) {
  const isReduced = useMediaQuery(REDUCED_MOTION);
  const [frame, setFrame] = useState(0);
  const [isPlaying, setPlaying] = useState(!isReduced);
  const [fps, setFps] = useState(startFps);

  useEffect(() => {
    if (!isPlaying || count < 2) {
      return;
    }

    const timer = window.setInterval(
      () => setFrame((current) => nextFrame(current, count)),
      frameDelay(fps),
    );

    return () => window.clearInterval(timer);
  }, [isPlaying, count, fps]);

  // Stepping by hand pauses, so the frame stays to be looked at.
  const step = (move: typeof nextFrame) => {
    setPlaying(false);
    setFrame((current) => move(current, count));
  };

  return {
    frame: count ? frame % count : 0,
    fps,
    isPlaying,
    setFps,
    toggle: () => setPlaying((playing) => !playing),
    next: () => step(nextFrame),
    previous: () => step(previousFrame),
  };
}

export type SpritePlayerState = ReturnType<typeof useSpritePlayer>;
