import { describe, expect, it } from 'vitest';
import { lastCheck } from '@/training/chart-readout';
import { smoothLoss } from '@/training/loss-chart';
import { tryoutDefaults } from '@/training/training-actions';
import type { Run } from '@/training/training-client';
import { defaultValues, startBody } from '@/training/training-form';
import { OPTIONS, ROTATE_RUN } from '../integration/training-server';

// The old /training page's choices when only the name was filled; the new forms must match them.
describe('the training forms, as the old /training page', () => {
  it('starts a run with the old defaults and every source', () => {
    expect(startBody({ ...defaultValues(OPTIONS), name: 'rotate-v3' })).toEqual({
      name: 'rotate-v3',
      task: 'rotate',
      export: 'characters-v2',
      model: 'flux2-klein-base-4b',
      size: '256',
      steps: 2000,
      sources: ['lpc-4view', 'pac'],
    });
  });

  it('tries the newest LoRA on the fast model with 4 test characters', () => {
    expect(tryoutDefaults(ROTATE_RUN, OPTIONS)).toEqual({
      checkpoint: 'runs/rotate-v2/final',
      model: 'flux2-klein-4b',
      characters: 4,
    });
  });
});

// The old chart averaged the last 25 steps; a run of a few hundred steps drew every step's mean.
describe('the loss chart, as the old /training page', () => {
  it('averages a trailing window of 25 steps', () => {
    const loss: Run['loss'] = Array.from({ length: 30 }, (_, i) => [i + 1, i < 5 ? 1 : 0]);

    expect(smoothLoss(loss).at(-1)).toEqual([30, 0]);
    expect(smoothLoss(loss)[24]).toEqual([25, 0.2]);
  });

  it('reads no val loss before the first check', () => {
    expect(lastCheck(ROTATE_RUN.val, 999)).toBeNull();
  });
});
