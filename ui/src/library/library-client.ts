import { getJson } from '@/api/read-json';

export interface Picture {
  label: string;
  src: string;
  thumb?: string;
}

export interface CharacterEntry {
  id: string;
  source: string;
  caption: string;
  views: Picture[];
}

export interface CharacterPage {
  imported: boolean;
  characters: CharacterEntry[];
  total: number;
  page: number;
  pages: number;
  sources: string[];
}

export interface Analysis {
  status: string;
  flags: string[];
  colors: number;
  filled: number;
  softEdge: number;
  scale: number;
}

export interface CharacterImage extends Picture {
  id: string;
  width: number;
  height: number;
  license: string;
  use: string;
  file: string;
  analysis: Analysis | null;
}

export interface CharacterDetail {
  id: string;
  source: string;
  split: string | null;
  caption: string;
  images: CharacterImage[];
  group: { kind: 'copy' | 'group'; characters: string[] } | null;
}

export interface Flag {
  name: string;
  count: number;
  meaning: string;
  outcome: string;
}

export interface FlaggedImage extends Picture {
  character: string;
  flags: string[];
  colors: number;
  filled: number;
  softEdge: number;
}

export interface FlaggedPage {
  imported: boolean;
  analyzed: boolean;
  flags: Flag[];
  flag: string;
  page: number;
  hasMore: boolean;
  images: FlaggedImage[];
}

export interface ExportSample {
  character: string;
  split: string;
  views: Picture[];
}

export interface ExportSummary {
  name: string;
  createdAt: string;
  characters: Record<string, Record<string, number>>;
  leftOut: Record<string, number>;
  isLeakFree: boolean | null;
  licenses: Record<string, string>;
  samples: ExportSample[];
}

export interface TryoutModel {
  name: string;
  repo: string;
  state: 'done' | 'failed' | 'pending';
  error: string;
  secondsPerImage: number | null;
}

export interface TryoutRun {
  name: string;
  createdAt: string;
  device: string;
  models: TryoutModel[];
  groups: { title: string; character: string | null; pictures: Picture[] }[];
}

export interface TryoutList {
  runs: { name: string; createdAt: string }[];
  run: TryoutRun | null;
}

const query = (params: Record<string, string | number>) =>
  new URLSearchParams(
    Object.entries(params)
      .filter(([, value]) => value !== '')
      .map(([key, value]) => [key, String(value)]),
  ).toString();

export const fetchCharacters = (page: number, search: string, source: string) =>
  getJson<CharacterPage>(`/api/characters?${query({ page, q: search, source })}`);

export const fetchCharacter = (id: string) =>
  getJson<CharacterDetail>(`/api/characters/${id.split('/').map(encodeURIComponent).join('/')}`);

export const fetchFlagged = (page: number, flag: string) =>
  getJson<FlaggedPage>(`/api/flagged?${query({ page, flag })}`);

export const fetchExports = () => getJson<{ exports: ExportSummary[] }>('/api/exports');

export const fetchTryouts = (run: string) => getJson<TryoutList>(`/api/tryouts?${query({ run })}`);
