import { dateText, dayText, type Fact, type LibraryItem } from '@/library/library-view';
import type { GeneratedEntry } from './create-client';

const whenText = (stamp: string) => (stamp ? dateText(stamp) : 'Unknown');

export function turnText(entry: GeneratedEntry): string {
  if (entry.facing === 'side') {
    return 'Side, flipped for the left';
  }

  return entry.turnWith || 'Front only';
}

export const subtitleText = (entry: GeneratedEntry) =>
  `${whenText(entry.createdAt)} · ${entry.sprite} px · ${turnText(entry)}`;

const charactersText = (count: number) => (count === 1 ? '1 character' : `${count} characters`);

export const tileText = (entry: GeneratedEntry) =>
  `${dayText(entry.createdAt)} · ${charactersText(entry.sheets.length)}`;

function facts(entry: GeneratedEntry): Fact[] {
  const turning = entry.turningModel ? [{ label: 'Turning model', value: entry.turningModel }] : [];

  return [
    { label: 'Made', value: whenText(entry.createdAt) },
    { label: 'Characters', value: String(entry.sheets.length) },
    { label: 'Sprite size', value: `${entry.sprite} × ${entry.sprite}` },
    { label: 'Drawn with', value: entry.drawWith || 'The model as it is' },
    { label: 'Drawing model', value: entry.drawingModel || 'Unknown' },
    { label: 'Reference', value: entry.reference || 'None' },
    { label: 'Turned with', value: turnText(entry) },
    ...turning,
  ];
}

// A made character opens in the same viewer as the library's pictures.
export function galleryItem(entry: GeneratedEntry): LibraryItem {
  return {
    key: entry.folder,
    title: entry.prompt,
    subtitle: subtitleText(entry),
    pictures: entry.sheets,
    character: null,
    facts: facts(entry),
    made: {
      kind: 'generated',
      folder: entry.folder,
      title: entry.prompt,
      count: entry.sheets.length,
    },
  };
}
