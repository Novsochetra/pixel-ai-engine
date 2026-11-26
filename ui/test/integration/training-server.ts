import { vi } from 'vitest';
import type { JobView } from '@/jobs/jobs-client';
import type { Run, TrainingOptions } from '@/training/training-client';
import { NO_JOB, RUNNING } from './render-app';

export const OPTIONS: TrainingOptions = {
  tasks: [
    { value: 'rotate', label: 'rotate: turn a front view' },
    { value: 'create', label: 'create: draw a front view from text' },
  ],
  models: [
    { value: 'flux2-klein-4b', label: 'fast (4 steps, ~40 s a view)' },
    { value: 'flux2-klein-base-4b', label: 'base (28 steps, ~6 min a view)' },
  ],
  sizes: [
    { value: '256', label: '256 px' },
    { value: '512', label: '512 px' },
  ],
  exports: [
    {
      name: 'characters-v2',
      sources: [
        { name: 'lpc-4view', licence: 'CC-BY-SA-3.0', use: 'train', count: 45016 },
        { name: 'pac', licence: 'CC-BY-NC-4.0', use: 'train', count: 10898 },
      ],
    },
    {
      name: 'opengameart-v1',
      sources: [{ name: 'opengameart-2d', licence: 'CC0', use: 'train', count: 5188 }],
    },
  ],
  namePattern: '^[A-Za-z0-9_-]{1,40}$',
  mostSteps: 50000,
  characters: { min: 1, max: 20, default: 4 },
  defaults: {
    task: 'rotate',
    model: 'flux2-klein-base-4b',
    size: '256',
    steps: 2000,
    tryoutModel: 'flux2-klein-4b',
    addSteps: 500,
  },
};

const loss = (steps: number) =>
  Array.from({ length: steps }, (_, i) => [i + 1, 0.2 - i / (steps * 10)] as const);

export const ROTATE_RUN: Run = {
  name: 'rotate-v2',
  task: 'rotate',
  createdAt: '2026-11-20T14:18:20+00:00',
  model: 'flux2-klein-base-4b',
  size: 256,
  export: 'rotation-v1',
  sources: [],
  moreExports: [],
  step: 2000,
  steps: 2000,
  secondsPerStep: 27.36,
  passes: null,
  checkpoints: ['step-001900', 'step-002000'],
  final: true,
  loss: loss(2000),
  val: [
    [1000, 0.09],
    [2000, 0.08054],
  ],
  tryouts: [
    { value: 'runs/rotate-v2/final', label: 'final' },
    { value: 'runs/rotate-v2/checkpoints/step-002000', label: 'step-002000' },
  ],
  isTraining: false,
};

export const CREATE_RUN: Run = {
  ...ROTATE_RUN,
  name: 'pixie-draw-v1',
  task: 'create',
  createdAt: '2026-11-25T10:00:00+00:00',
  sources: ['lpc-4view', 'pac'],
  moreExports: ['opengameart-v1'],
  step: 1500,
  steps: 1500,
  passes: 0.42,
  checkpoints: ['step-001500'],
  final: false,
  loss: loss(1500),
  val: [[1500, 0.061]],
  tryouts: [{ value: 'runs/pixie-draw-v1/checkpoints/step-001500', label: 'step-001500' }],
};

interface TrainingState {
  job: JobView;
  runs: Run[];
  refusal?: { status: number; detail: string };
}

const json = (body: object, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const GETS: Record<string, (state: TrainingState) => object> = {
  '/api/jobs/current': (state) => state.job,
  '/api/training/options': () => OPTIONS,
  '/api/runs': (state) => ({ runs: state.runs }),
};

// The Training API with a state the test can change: the job, the runs, a refusal to give.
export function trainingServer(state: TrainingState) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    const path = url.split('?')[0]!;

    if (init?.method === 'POST') {
      return state.refusal
        ? json({ detail: state.refusal.detail }, state.refusal.status)
        : json((state.job = RUNNING));
    }

    const answer = GETS[path];

    return answer ? json(answer(state)) : json({}, 404);
  });
}

export const startState = (): TrainingState => ({ job: NO_JOB, runs: [CREATE_RUN, ROTATE_RUN] });

export function postedBody(server: ReturnType<typeof trainingServer>, path: string) {
  const call = server.mock.calls.find(([url, init]) => url === path && init?.method === 'POST');

  return call ? JSON.parse(String(call[1]!.body)) : undefined;
}
