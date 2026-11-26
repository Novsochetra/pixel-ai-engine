import { dateText } from '@/library/library-view';
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

export interface ClipChoice {
  folder: string;
  clipId: string;
}

// Nothing chosen yet shows the newest clip.
export function chosenClip(runs: readonly AnimatedRun[], choice: ClipChoice | null) {
  const run = runs.find((entry) => entry.folder === choice?.folder) ?? runs[0];
  const clip = run?.clips.find((entry) => entry.id === choice?.clipId) ?? run?.clips[0];

  return run && clip ? { run, clip } : null;
}
