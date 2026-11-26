import { describe, expect, it } from 'vitest';
import { sparklinePoints } from '@/training/sparkline';

describe('a run card sparkline', () => {
  it('runs from the highest loss at the top to the lowest at the bottom', () => {
    const loss = [
      [1, 0.4],
      [2, 0.2],
    ] as const;

    expect(sparklinePoints(loss, 2)).toBe('50.0,2.0 100.0,30.0');
  });

  it('leaves room for the steps still to come', () => {
    expect(sparklinePoints([[1, 0.3]], 4)).toBe('25.0,30.0');
  });

  it('draws nothing before the first step', () => {
    expect(sparklinePoints([], 2000)).toBe('');
  });
});
