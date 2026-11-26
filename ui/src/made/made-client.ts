import { postJson } from '@/api/read-json';

export interface Trashed {
  folder: string;
  trashed: string;
}

export const trashMade = (folder: string) => postJson<Trashed>('/api/generated/trash', { folder });

export const restoreMade = ({ folder, trashed }: Trashed) =>
  postJson<{ folder: string }>('/api/generated/restore', { folder, trashed });
