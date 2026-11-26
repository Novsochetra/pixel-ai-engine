import { vi } from 'vitest';
import type { CharacterDetail, CharacterPage, FlaggedPage } from '@/library/library-client';
import { NO_JOB } from './render-app';

export const CHARACTERS: CharacterPage = {
  imported: true,
  characters: [
    {
      id: 'pac/train/0',
      source: 'pac',
      caption: 'a knight with a spear',
      views: [
        { label: 'front', src: '/api/images/pac/train/0/front.png', thumb: '/api/thumbs/x.png' },
        { label: 'left', src: '/api/images/pac/train/0/left.png', thumb: '/api/thumbs/y.png' },
      ],
    },
  ],
  total: 1,
  page: 1,
  pages: 1,
  sources: ['pac'],
};

export const KNIGHT: CharacterDetail = {
  id: 'pac/train/0',
  source: 'pac',
  split: 'train',
  caption: 'a knight with a spear',
  group: { kind: 'copy', characters: ['pac/test/0'] },
  images: [
    {
      id: 'pac/train/0/front',
      label: 'front',
      src: '/api/images/pac/train/0/front.png',
      width: 64,
      height: 64,
      license: 'CC-BY-NC-4.0',
      use: 'train',
      file: 'pac/pac-train-000000.tar',
      analysis: {
        status: 'drop',
        flags: ['duplicate'],
        colors: 25,
        filled: 900,
        softEdge: 0,
        scale: 1,
      },
    },
  ],
};

export const NOT_ANALYZED: FlaggedPage = {
  imported: true,
  analyzed: false,
  flags: [],
  flag: '',
  page: 1,
  hasMore: false,
  images: [],
};

type Answer = object | number;

// Each API path answers with its JSON, or with a status code when the answer is a number.
export function libraryServer(answers: Record<string, Answer>) {
  return vi.fn(async (url: string, _init?: RequestInit) => {
    const path = url.split('?')[0]!;
    const answer = path === '/api/jobs/current' ? NO_JOB : answers[path];

    if (answer === undefined || typeof answer === 'number') {
      return new Response('{}', { status: typeof answer === 'number' ? answer : 404 });
    }

    return new Response(JSON.stringify(answer), {
      headers: { 'Content-Type': 'application/json' },
    });
  });
}
