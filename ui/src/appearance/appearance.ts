export type Appearance = 'light' | 'dark';

export interface SavedAppearance {
  choice: Appearance;
  system: Appearance;
}

export const APPEARANCE_KEY = 'pixel.appearance';

const isAppearance = (value: unknown): value is Appearance => value === 'light' || value === 'dark';

// The person's switch holds while the device keeps the appearance it had then; when the device
// changes, the device wins again. public/appearance-early.js makes the same choice before React runs.
export function resolveAppearance(saved: SavedAppearance | null, system: Appearance): Appearance {
  const isKept = saved && saved.system === system && isAppearance(saved.choice);

  return isKept ? saved.choice : system;
}

export function readSaved(storage: Storage): SavedAppearance | null {
  try {
    return JSON.parse(storage.getItem(APPEARANCE_KEY) ?? 'null');
  } catch {
    return null;
  }
}

export function systemAppearance(window: Window): Appearance {
  return window.matchMedia?.('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

export const otherAppearance = (appearance: Appearance): Appearance =>
  appearance === 'dark' ? 'light' : 'dark';
