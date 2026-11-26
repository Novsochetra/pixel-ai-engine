import { describe, expect, it } from 'vitest';
import { readIntent, shouldDismiss } from '@/components/sheet/sheet-drag.js';

describe('sheet drag', () => {
  it('dismisses past a third of the sheet, or on a flick', () => {
    expect(shouldDismiss({ offset: 140, height: 400, velocity: 0 })).toBe(true);
    expect(shouldDismiss({ offset: 40, height: 400, velocity: 0.8 })).toBe(true);
    expect(shouldDismiss({ offset: 40, height: 400, velocity: 0.1 })).toBe(false);
  });

  it('drags only a downward pull that starts at the top', () => {
    expect(readIntent({ dx: 2, dy: 10, atTop: true })).toBe('drag');
    expect(readIntent({ dx: 2, dy: 10, atTop: false })).toBe('scroll');
    expect(readIntent({ dx: 12, dy: 4, atTop: true })).toBe('scroll');
  });
});
