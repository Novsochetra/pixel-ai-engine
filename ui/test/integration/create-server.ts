import { vi } from 'vitest';
import type { FormOptions, GeneratedEntry } from '@/create/create-client';
import type { JobView } from '@/jobs/jobs-client';
import { NO_JOB, RUNNING } from './render-app';

export const BASE = 'flux2-klein-base-4b';

export const OPTIONS: FormOptions = {
  models: [
    { value: 'flux2-klein-4b', label: 'fast (4 steps, ~40 s a view)' },
    { value: 'flux2-klein-base-4b', label: 'base (28 steps, ~6 min a view)' },
  ],
  sprites: [
    { value: '64', label: '64 × 64' },
    { value: '128', label: '128 × 128' },
  ],
  facing: [
    { value: 'front', label: 'front, then turned to left, back, right' },
    { value: 'side', label: 'side, facing right (left is its mirror)' },
  ],
  promptLength: 300,
  poseLength: 100,
  characters: { min: 1, max: 8, default: 2 },
  defaults: { sprite: '128', model: 'flux2-klein-4b', facing: 'front' },
};

export const DRAGON: GeneratedEntry = {
  folder: '20261124-1437-a-lava-dragon',
  prompt: 'a lava dragon',
  createdAt: '2026-11-24T08:30:08+00:00',
  sprite: 128,
  facing: 'front',
  drawWith: 'create-v1 · final',
  drawingModel: 'flux2-klein-4b',
  turnWith: 'rotate-v2 · final',
  turningModel: 'flux2-klein-4b',
  sheets: [
    { label: 'Character 1', src: '/api/files/generated/dragon/s0-sheet.png' },
    { label: 'Character 2', src: '/api/files/generated/dragon/s1-sheet.png' },
  ],
};

export const FROG: GeneratedEntry = {
  ...DRAGON,
  folder: '20261121-1146-a-frog-wizard',
  prompt: 'a frog wizard',
  createdAt: '2026-11-21T04:50:09+00:00',
  drawWith: '',
  sheets: [{ label: 'Character 1', src: '/api/files/generated/frog/s0-sheet.png' }],
};

interface CreateState {
  job: JobView;
  items: GeneratedEntry[];
  refusal?: { status: number; detail: string };
  trash?: GeneratedEntry[];
}

const json = (body: object, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const GETS: Record<string, (state: CreateState) => object> = {
  '/api/jobs/current': (state) => state.job,
  '/api/generate/options': () => OPTIONS,
  '/api/generated': (state) => ({ items: state.items }),
};

function loras(url: string) {
  const task = new URL(url, 'http://test').searchParams.get('task');

  return {
    loras: [{ value: `runs/${task}-v1/final`, label: `${task}-v1 · final`, model: BASE }],
  };
}

// Delete moves a folder to the trash and Undo brings it back, as the server does.
function moveMade(state: CreateState, path: string, body: { folder: string }) {
  const trash = (state.trash ??= []);

  if (path.endsWith('/trash')) {
    trash.push(...state.items.filter((item) => item.folder === body.folder));
    state.items = state.items.filter((item) => item.folder !== body.folder);

    return { folder: body.folder, trashed: body.folder };
  }

  state.items = [...trash.filter((item) => item.folder === body.folder), ...state.items];

  return { folder: body.folder };
}

// The Create API with a state the test can change: the job, what was made, a refusal to give.
export function createServer(state: CreateState) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.split('?')[0]!;

    if (path === '/api/generate' && init?.method === 'POST') {
      return state.refusal
        ? json({ detail: state.refusal.detail }, state.refusal.status)
        : json((state.job = RUNNING));
    }

    if (path.startsWith('/api/generated/') && init?.method === 'POST') {
      return json(moveMade(state, path, JSON.parse(String(init.body))));
    }

    if (path === '/api/loras') {
      return json(loras(url));
    }

    const answer = GETS[path];

    return answer ? json(answer(state)) : json({}, 404);
  });
}

export const startState = (): CreateState => ({ job: NO_JOB, items: [DRAGON, FROG] });

export function postedBody(server: ReturnType<typeof createServer>) {
  const call = server.mock.calls.find(([url, init]) => url === '/api/generate' && init?.method);

  return call ? JSON.parse(String(call[1]!.body)) : undefined;
}
