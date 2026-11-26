import { describe, expect, it } from 'vitest';
import { otherAppearance, resolveAppearance } from '@/appearance/appearance';

describe('resolveAppearance', () => {
  it('follows the device when nothing is saved', () => {
    expect(resolveAppearance(null, 'light')).toBe('light');
  });

  it('keeps the switch while the device keeps its appearance', () => {
    expect(resolveAppearance({ choice: 'light', system: 'dark' }, 'dark')).toBe('light');
  });

  it('follows the device again once the device changes', () => {
    expect(resolveAppearance({ choice: 'light', system: 'dark' }, 'light')).toBe('light');
    expect(resolveAppearance({ choice: 'dark', system: 'light' }, 'dark')).toBe('dark');
  });

  it('switches between the two', () => {
    expect(otherAppearance('dark')).toBe('light');
  });
});
