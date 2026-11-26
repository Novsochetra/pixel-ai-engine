import { useState } from 'react';
import type { AnimatedRun, Clip } from './animate-client';
import { chosenClip, type ClipChoice } from './clip-view';

// The clip in the player sheet: none until a run is opened from the gallery.
export function useClipChoice(runs: readonly AnimatedRun[] | undefined) {
  const [choice, setChoice] = useState<ClipChoice | null>(null);
  const chosen = runs && choice ? chosenClip(runs, choice) : null;

  const choose = (run: AnimatedRun, clip: Clip) =>
    setChoice({ folder: run.folder, clipId: clip.id });

  function open(run: AnimatedRun) {
    const first = run.clips[0];

    if (first) {
      choose(run, first);
    }
  }

  return { chosen, choose, open, close: () => setChoice(null) };
}
