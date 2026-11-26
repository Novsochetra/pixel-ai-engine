import { describe, expect, it } from 'vitest';
import { estimateText } from '@/animate/animate-checks';
import { animateBody, defaultValues } from '@/animate/animate-form';
import { clipFps } from '@/animate/sprite-frames';
import { OPTIONS, SOURCES } from '../integration/animate-server';

// The old /animate page started with front and right, idle and walk, 384 px and 33 frames, and
// said about 11 min a clip; the new form must match.
describe('the animate form, as the old /animate page', () => {
  it('sends the old defaults', () => {
    expect(animateBody(defaultValues(OPTIONS, SOURCES))).toEqual({
      source: 'generated/dragon/s0',
      subject: 'a lava dragon',
      views: ['front', 'right'],
      actions: 'idle\nwalk',
      size: '384',
      frames: '33',
    });
  });

  it('says the old time for the old defaults', () => {
    expect(estimateText(defaultValues(OPTIONS, SOURCES), OPTIONS)).toMatch(/about 44 min/);
  });

  // The first runs (2026-11-23) kept no count of used frames.
  it('plays a clip of the first runs at a usual speed', () => {
    expect(clipFps({ kept: 8, used: null })).toBe(8);
  });
});
