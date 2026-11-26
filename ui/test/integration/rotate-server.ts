import { vi } from 'vitest';
import type { UploadSource } from '@/animate/animate-client';
import type { Choice } from '@/create/create-client';
import type { JobView } from '@/jobs/jobs-client';
import type { TryoutList } from '@/library/library-client';
import type { RotateOptions, TurnedCharacter } from '@/rotate/rotate-client';
import { NEW_UPLOAD, SOURCES } from './animate-server';
import { NO_JOB, RUNNING } from './render-app';

export const OPTIONS: RotateOptions = {
  models: [
    { value: 'flux2-klein-4b', label: 'fast (4 steps, ~40 s a view)' },
    { value: 'flux2-klein-base-4b', label: 'base (28 steps, ~6 min a view)' },
  ],
  sprites: ['64', '96', '128'].map((size) => ({ value: size, label: `${size} × ${size}` })),
  views: ['left', 'back', 'right'],
  largestUpload: 2048,
  uploadLimit: 10_000_000,
  defaults: { sprite: '128', model: 'flux2-klein-4b', views: ['left', 'back', 'right'] },
};

export const LORAS: Choice[] = [
  { value: 'runs/rotate-v2/final', label: 'rotate-v2 · final' },
  { value: 'runs/rotate-v2/checkpoints/step-000500', label: 'rotate-v2 · step-000500' },
];

const view = (folder: string, name: string) => ({
  label: name.charAt(0).toUpperCase() + name.slice(1),
  src: `/api/files/generated/${folder}/s0-${name}.png`,
});

const turned = (folder: string, prompt: string, rotatedFrom: string): TurnedCharacter => ({
  key: `${folder}/s0`,
  folder,
  seed: 0,
  prompt,
  createdAt: '2026-11-26T09:00:00+00:00',
  sprite: 128,
  rotatedFrom,
  turnWith: 'rotate-v2 · final',
  turningModel: 'flux2-klein-4b',
  views: ['front', 'left', 'back', 'right'].map((name) => view(folder, name)),
});

export const TURNED = [
  turned('20261126-090000-turned-dragon', 'a lava dragon', 'dragon'),
  turned('knight', 'a knight', ''),
];

const tryoutPicture = (label: string) => ({ label, src: `/api/files/tryouts/v2/${label}.png` });

export const TRYOUTS: TryoutList = {
  runs: [{ name: 'v2-flux2-klein-4b', createdAt: '2026-11-20T10:00:00+00:00' }],
  run: {
    name: 'v2-flux2-klein-4b',
    createdAt: '2026-11-20T10:00:00+00:00',
    device: 'mps',
    models: [{ name: 'flux2-klein-4b', repo: 'x/y', state: 'done', error: '', secondsPerImage: 9 }],
    groups: [
      { title: 'pixel art of a knight', character: null, pictures: [tryoutPicture('knight')] },
      {
        title: 'pac/val/3 → back',
        character: 'pac/val/3',
        pictures: ['front given', 'real back', 'flux2-klein-4b'].map(tryoutPicture),
      },
    ],
  },
};

interface RotateState {
  job: JobView;
  loras: Choice[];
  turned: TurnedCharacter[];
  uploads: UploadSource[];
  refusal?: { status: number; detail: string };
}

const json = (body: object, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const GETS: Record<string, (state: RotateState) => object> = {
  '/api/jobs/current': (state) => state.job,
  '/api/rotate/options': () => OPTIONS,
  '/api/animate/sources': (state) => ({ ...SOURCES, uploads: state.uploads }),
  '/api/loras': (state) => ({ loras: state.loras }),
  '/api/rotated': (state) => ({ characters: state.turned }),
  '/api/tryouts': () => TRYOUTS,
};

function post(state: RotateState, path: string, body: BodyInit | null | undefined) {
  if (path === '/api/generated/trash') {
    const { folder } = JSON.parse(String(body));

    state.turned = state.turned.filter((character) => character.folder !== folder);

    return json({ folder, trashed: folder });
  }

  if (path === '/api/uploads') {
    state.uploads = [NEW_UPLOAD, ...state.uploads];

    return json({ upload: NEW_UPLOAD });
  }

  return state.refusal
    ? json({ detail: state.refusal.detail }, state.refusal.status)
    : json((state.job = RUNNING));
}

// The Rotate API with a state the test can change: the job, the LoRAs, a refusal to give.
export function rotateServer(state: RotateState) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.split('?')[0]!;

    if (init?.method === 'POST') {
      return post(state, path, init.body);
    }

    const answer = GETS[path];

    return answer ? json(answer(state)) : json({}, 404);
  });
}

export const startState = (): RotateState => ({
  job: NO_JOB,
  loras: LORAS,
  turned: TURNED,
  uploads: [],
});

export function postedBody(server: ReturnType<typeof rotateServer>) {
  const call = server.mock.calls.find(
    ([url, init]) => url === '/api/rotate' && init?.method === 'POST',
  );

  return call ? JSON.parse(String(call[1]!.body)) : undefined;
}
