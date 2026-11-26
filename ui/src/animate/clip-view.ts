import { dateText, dayText } from '@/library/library-view';
import type { MadeTarget } from '@/made/made-client';
import type { AnimatedRun, Clip } from './animate-client';

export const actionText = (action: string) => action.replaceAll('-', ' ');

export const viewText = (view: string) => view.charAt(0).toUpperCase() + view.slice(1);

export const clipText = (clip: Clip) =>
  [clip.view ? viewText(clip.view) : null, actionText(clip.action)].filter(Boolean).join(' · ');

const unique = (values: string[]) => [...new Set(values)];

export const clipViews = (run: AnimatedRun) =>
  unique(run.clips.flatMap((clip) => (clip.view ? [clip.view] : [])));

export const clipActions = (run: AnimatedRun) => unique(run.clips.map((clip) => clip.action));

// A view without the chosen action shows its first clip, so a choice always shows something.
export function findClip(run: AnimatedRun, view: string | null, action: string) {
  const inView = run.clips.filter((clip) => clip.view === view);

  return inView.find((clip) => clip.action === action) ?? inView[0] ?? run.clips[0] ?? null;
}

export function runSubtitle(run: AnimatedRun) {
  const parts = [
    run.createdAt ? dateText(run.createdAt) : 'Unknown',
    run.size ? `${run.size} px` : null,
    run.frames ? `${run.frames} frames` : null,
    run.openEnd ? 'open end' : null,
  ];

  return parts.filter(Boolean).join(' · ');
}

const clipsText = (count: number) => (count === 1 ? '1 clip' : `${count} clips`);

export const tileText = (run: AnimatedRun) =>
  `${dayText(run.createdAt)} · ${run.clips.length ? clipsText(run.clips.length) : 'No clips yet'}`;

export interface ClipChoice {
  folder: string;
  clipId: string;
}

// A run that is gone closes the player; a clip that is gone shows the run's first.
export function chosenClip(runs: readonly AnimatedRun[], choice: ClipChoice) {
  const run = runs.find((entry) => entry.folder === choice.folder);
  const clip = run?.clips.find((entry) => entry.id === choice.clipId) ?? run?.clips[0];

  return run && clip ? { run, clip } : null;
}

// A run is deleted whole: its folder under data/animated/ with every clip in it.
export const runTarget = (run: AnimatedRun): MadeTarget => ({
  kind: 'animated',
  folder: run.folder,
  title: run.source,
  count: run.clips.length,
});
