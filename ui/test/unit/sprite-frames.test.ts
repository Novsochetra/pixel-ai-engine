import { describe, expect, it } from 'vitest';
import { chosenClip, clipText, findClip, runSubtitle } from '@/animate/clip-view';
import {
  clipFps,
  frameBox,
  frameCount,
  frameDelay,
  frameText,
  nextFrame,
  previousFrame,
} from '@/animate/sprite-frames';
import { DRAGON_RUN, SLIME_RUN } from '../integration/animate-server';

describe('the sprite frames', () => {
  it('waits a frame time for each frame', () => {
    expect(frameDelay(4)).toBe(250);
    expect(frameDelay(24)).toBe(42);
  });

  it('goes round the frames both ways', () => {
    expect(nextFrame(7, 8)).toBe(0);
    expect(previousFrame(0, 8)).toBe(7);
    expect(nextFrame(0, 0)).toBe(0);
  });

  it('plays the kept frames as long as the clip lasts', () => {
    expect(clipFps({ kept: 8, used: 32 })).toBe(4);
    expect(clipFps({ kept: 8, used: 9 })).toBe(14);
    expect(clipFps({ kept: 8, used: null })).toBe(8);
    expect(clipFps({ kept: 40, used: 2 })).toBe(24);
  });

  it('cuts a sheet into its kept frames, or into squares', () => {
    expect(frameCount(2048, 256, 8)).toBe(8);
    expect(frameCount(1024, 256, 0)).toBe(4);
    expect(frameCount(0, 0, 0)).toBe(1);
  });

  it('slides the sheet a whole frame at each step, at the scale', () => {
    const box = frameBox({ width: 2048, height: 256 }, 8, 3);

    expect(box(1)).toEqual({ width: 256, height: 256, offset: -768 });
    expect(box(2)).toEqual({ width: 512, height: 512, offset: -1536 });
    expect(box(0.5)).toEqual({ width: 128, height: 128, offset: -384 });
  });

  it('counts frames from one', () => {
    expect(frameText(0, 8)).toBe('Frame 1 of 8');
  });
});

describe('the clips of a run', () => {
  it('names a clip by its view and action', () => {
    expect(clipText(DRAGON_RUN.clips[1]!)).toBe('Front · flying');
    expect(clipText(SLIME_RUN.clips[0]!)).toBe('hops');
  });

  it('finds the clip of a view and action, or the view’s first', () => {
    expect(findClip(DRAGON_RUN, 'left', 'flying')!.id).toBe('s0-left-flying');
    expect(findClip(DRAGON_RUN, 'left', 'swims')!.id).toBe('s0-left-idle');
    expect(findClip(DRAGON_RUN, 'back', 'idle')!.id).toBe('s0-front-idle');
  });

  it('plays the newest clip until another is chosen', () => {
    const runs = [DRAGON_RUN, SLIME_RUN];

    expect(chosenClip(runs, null)!.clip.id).toBe('s0-front-idle');
    expect(chosenClip(runs, { folder: SLIME_RUN.folder, clipId: 's0-hops' })!.run).toBe(SLIME_RUN);
    expect(chosenClip([], null)).toBeNull();
  });

  it('says when, how big and how long a run is', () => {
    expect(runSubtitle({ ...DRAGON_RUN, createdAt: '', openEnd: true })).toBe(
      'Unknown · 384 px · 33 frames · open end',
    );
  });
});
