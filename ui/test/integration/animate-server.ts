import { vi } from 'vitest';
import type {
  AnimatedRun,
  AnimateOptions,
  AnimateSources,
  UploadSource,
} from '@/animate/animate-client';
import type { JobView } from '@/jobs/jobs-client';
import { NO_JOB, RUNNING } from './render-app';

export const OPTIONS: AnimateOptions = {
  views: ['front', 'left', 'back', 'right'],
  sizes: [
    { value: '384', label: '384 px (faster)' },
    { value: '512', label: '512 px' },
  ],
  frames: [
    { value: '17', label: '17 frames (~1 s)' },
    { value: '33', label: '33 frames (~2 s)' },
  ],
  minutes: [
    { size: '384', frames: '33', minutes: 11 },
    { size: '512', frames: '17', minutes: 8 },
  ],
  mostActions: 8,
  longestAction: 200,
  subjectLength: 300,
  largestUpload: 2048,
  uploadLimit: 10_000_000,
  defaults: { size: '384', frames: '33', actions: 'idle\nwalk', views: ['front', 'right'] },
};

const picture = (folder: string, view: string) => `/api/files/generated/${folder}/s0-${view}.png`;

export const SOURCES: AnimateSources = {
  characters: [
    {
      value: 'generated/dragon/s0',
      label: 'a lava dragon · s0',
      subject: 'a lava dragon',
      views: ['front', 'left', 'back', 'right'],
      pictures: { front: picture('dragon', 'front'), right: picture('dragon', 'right') },
    },
    {
      value: 'generated/bird/s0',
      label: 'a blue bird · s0',
      subject: 'a blue bird',
      views: ['right'],
      pictures: { right: picture('bird', 'right') },
    },
  ],
  uploads: [],
};

export const NEW_UPLOAD: UploadSource = {
  value: 'uploads/20261126-100000-slime.png',
  label: '20261126-100000-slime.png',
  src: '/api/files/uploads/20261126-100000-slime.png',
};

function clip(folder: string, view: string | null, action: string) {
  const id = view ? `s0-${view}-${action}` : `s0-${action}`;
  const file = `/api/files/animated/${folder}/${id}`;

  return {
    id,
    seed: 0,
    view,
    action,
    kept: 8,
    used: 32,
    gif: `${file}.gif`,
    raw: `${file}-raw.gif`,
    sheet: `${file}-sheet.png`,
  };
}

export const DRAGON_RUN: AnimatedRun = {
  folder: '20261124-111713-dragon',
  source: 'dragon',
  subject: 'a lava dragon',
  createdAt: '2026-11-24T11:17:13+00:00',
  size: 384,
  frames: 33,
  openEnd: false,
  clips: [
    clip('20261124-111713-dragon', 'front', 'idle'),
    clip('20261124-111713-dragon', 'front', 'flying'),
    clip('20261124-111713-dragon', 'left', 'idle'),
    clip('20261124-111713-dragon', 'left', 'flying'),
  ],
};

export const SLIME_RUN: AnimatedRun = {
  ...DRAGON_RUN,
  folder: '20261123-090000-slime',
  source: 'slime.png',
  subject: '',
  createdAt: '2026-11-23T09:00:00+00:00',
  clips: [clip('20261123-090000-slime', null, 'hops')],
};

interface AnimateState {
  job: JobView;
  runs: AnimatedRun[];
  uploads: UploadSource[];
  refusal?: { status: number; detail: string };
  uploadRefusal?: string;
}

const json = (body: object, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const GETS: Record<string, (state: AnimateState) => object> = {
  '/api/jobs/current': (state) => state.job,
  '/api/animate/options': () => OPTIONS,
  '/api/animate/sources': (state) => ({ ...SOURCES, uploads: state.uploads }),
  '/api/animated': (state) => ({ runs: state.runs }),
};

function post(state: AnimateState, path: string) {
  if (path === '/api/uploads') {
    if (state.uploadRefusal) {
      return json({ detail: state.uploadRefusal }, 400);
    }

    state.uploads = [NEW_UPLOAD, ...state.uploads];

    return json({ upload: NEW_UPLOAD });
  }

  return state.refusal
    ? json({ detail: state.refusal.detail }, state.refusal.status)
    : json((state.job = RUNNING));
}

// The Animate API with a state the test can change: the job, the runs, a refusal to give.
export function animateServer(state: AnimateState) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.split('?')[0]!;

    if (init?.method === 'POST') {
      return post(state, path);
    }

    const answer = GETS[path];

    return answer ? json(answer(state)) : json({}, 404);
  });
}

export const startState = (): AnimateState => ({
  job: NO_JOB,
  runs: [DRAGON_RUN, SLIME_RUN],
  uploads: [],
});

export function postedTo(server: ReturnType<typeof animateServer>, path: string) {
  return server.mock.calls.find(([url, init]) => url.startsWith(path) && init?.method === 'POST');
}

export function postedBody(server: ReturnType<typeof animateServer>) {
  const call = postedTo(server, '/api/animate');

  return call ? JSON.parse(String(call[1]!.body)) : undefined;
}
