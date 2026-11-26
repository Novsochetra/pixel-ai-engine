import { describe, expect, it } from 'vitest';
import { moveFrames, type MoveLook } from '@/navigation/stack/stack-motion';

const LOOK: MoveLook = {
  motion: 'zoom',
  offsetUnder: '-30%',
  dimUnder: '0.55',
  shadow: 'none',
  scaleUnder: '1.03',
  scaleAway: '0.96',
  reduced: false,
};

const opacities = (frames: Keyframe[]) => frames.map((frame) => frame.opacity);

describe('the frames of a move', () => {
  it('zooms a pushed screen in from small as the one left grows away and fades', () => {
    const frames = moveFrames('push', LOOK);

    expect(frames.front[0]).toEqual({ opacity: 0, scale: '0.96' });
    expect(frames.front.at(-1)).toEqual({ opacity: 1, scale: '1' });
    expect(frames.back.at(-1)).toEqual({ opacity: 0, scale: '1.03' });
  });

  it('plays a pop as the push backwards, with its offsets turned around', () => {
    const frames = moveFrames('pop', LOOK);

    expect(frames.front.at(-1)).toEqual({ opacity: 0, scale: '0.96' });
    expect(frames.back.map((frame) => frame.offset)).toEqual([undefined, 0.4, undefined]);
    expect(frames.back.at(-1)).toEqual({ opacity: 1, scale: '1' });
  });

  it('slides a pushed screen in from the right over the one left, which dims', () => {
    const frames = moveFrames('push', { ...LOOK, motion: 'slide' });

    expect(frames.front[0]!.translate).toBe('100% 0');
    expect(frames.back.at(-1)).toEqual({ translate: '-30% 0', filter: 'brightness(0.55)' });
  });

  it('cross-fades a swap, the screen left fading out first', () => {
    const frames = moveFrames('swap', LOOK);

    expect(opacities(frames.front)).toEqual([0, 1]);
    expect(opacities(frames.back)).toEqual([1, 0, 0]);
  });

  it('only fades with reduced motion, the screen leaving fading whichever is on top', () => {
    const pop = moveFrames('pop', { ...LOOK, reduced: true });

    expect(moveFrames('push', { ...LOOK, reduced: true })).toEqual(moveFrames('swap', LOOK));
    expect(opacities(pop.front)).toEqual([1, 0, 0]);
    expect(opacities(pop.back)).toEqual([0, 1]);
  });
});
