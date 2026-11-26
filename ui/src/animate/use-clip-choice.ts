import { useRef, useState } from 'react';
import { prefersReducedMotion } from '@/styles/motion-tokens.js';
import type { AnimatedRun, Clip } from './animate-client';
import { chosenClip, type ClipChoice } from './clip-view';

// The clip in the player: the newest one until another is chosen.
export function useClipChoice(runs: readonly AnimatedRun[] | undefined) {
  const [choice, setChoice] = useState<ClipChoice | null>(null);
  const player = useRef<HTMLDivElement>(null);
  const chosen = runs ? chosenClip(runs, choice) : null;

  const choose = (run: AnimatedRun, clip: Clip) =>
    setChoice({ folder: run.folder, clipId: clip.id });

  // A clip chosen far down the gallery plays at the top, so the page goes to where it plays.
  function play(run: AnimatedRun, clip: Clip) {
    choose(run, clip);
    player.current?.scrollIntoView({
      block: 'nearest',
      behavior: prefersReducedMotion(window) ? 'auto' : 'smooth',
    });
  }

  return {
    chosen,
    shown: chosen ? { folder: chosen.run.folder, clipId: chosen.clip.id } : null,
    player,
    choose,
    play,
  };
}
