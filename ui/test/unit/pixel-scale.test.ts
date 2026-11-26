import { describe, expect, it } from 'vitest';
import { canZoomIn, canZoomOut, fitScale, zoomIn, zoomOut, zoomText } from '@/library/pixel-scale';

describe('pixel scale', () => {
  it('fits a small picture at the largest whole number', () => {
    expect(fitScale(64, 64, 136, 136)).toBe(2);
    expect(fitScale(48, 64, 400, 300)).toBe(4);
  });

  it('shrinks a big picture by a whole factor', () => {
    expect(fitScale(512, 512, 136, 136)).toBe(1 / 4);
    expect(fitScale(200, 100, 136, 136)).toBe(1 / 2);
  });

  it('never zooms past the last step, and stays at 1 with nothing to measure', () => {
    expect(fitScale(8, 8, 1000, 1000)).toBe(16);
    expect(fitScale(64, 64, 0, 0)).toBe(1);
  });

  it('steps through whole-number zooms', () => {
    expect(zoomIn(4)).toBe(6);
    expect(zoomOut(4)).toBe(3);
    expect(zoomIn(0.25)).toBe(1);
    expect(zoomIn(16)).toBe(16);
    expect(canZoomIn(16)).toBe(false);
    expect(canZoomOut(1)).toBe(false);
  });

  it('names a zoom as people read it', () => {
    expect(zoomText(6)).toBe('6×');
    expect(zoomText(0.25)).toBe('1/4×');
  });
});
