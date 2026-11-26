import { describe, expect, it } from 'vitest';
import { runTransitionName } from '@/training/run-transition';

describe('the names a run card shares with its screen', () => {
  it('differ per run and per part', () => {
    expect(runTransitionName('rotate-v2', 'card')).toBe('run-card-rotate-v2');
    expect(runTransitionName('rotate-v2', 'title')).toBe('run-title-rotate-v2');
    expect(runTransitionName('pixie_draw-v1', 'card')).not.toBe(
      runTransitionName('rotate-v2', 'card'),
    );
  });
});
