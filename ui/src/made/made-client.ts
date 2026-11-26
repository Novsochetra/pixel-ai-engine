import { postJson } from '@/api/read-json';

// The folders of data/ that hold what the dashboard made: Create and Rotate's, and Animate's.
export type MadeKind = 'generated' | 'animated';

// One set that is deleted whole: a folder, its name for people, and how many things are in it.
export interface MadeTarget {
  kind: MadeKind;
  folder: string;
  title: string;
  count: number | null;
}

export interface Trashed {
  folder: string;
  trashed: string;
}

export const trashMade = ({ kind, folder }: MadeTarget) =>
  postJson<Trashed>(`/api/${kind}/trash`, { folder });

export const restoreMade = (kind: MadeKind, { folder, trashed }: Trashed) =>
  postJson<{ folder: string }>(`/api/${kind}/restore`, { folder, trashed });
