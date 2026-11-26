import { describe, expect, it } from 'vitest';
import { galleryItem, turnText } from '@/create/create-view';
import { DRAGON, FROG } from '../integration/create-server';

describe('a made character', () => {
  it('says how it was turned', () => {
    expect(turnText(DRAGON)).toBe('rotate-v2 · final');
    expect(turnText({ ...DRAGON, facing: 'side' })).toBe('Side, flipped for the left');
    expect(turnText({ ...DRAGON, turnWith: '' })).toBe('Front only');
  });

  it('opens with its sheets and settings', () => {
    const item = galleryItem(FROG);

    expect(item.pictures).toEqual(FROG.sheets);
    expect(item.character).toBeNull();
    expect(item.facts).toContainEqual({ label: 'Drawn with', value: 'The model as it is' });
    expect(item.facts).toContainEqual({ label: 'Characters', value: '1' });
  });

  it('reads a missing date as unknown', () => {
    expect(galleryItem({ ...FROG, createdAt: '' }).facts[0]).toEqual({
      label: 'Made',
      value: 'Unknown',
    });
  });
});
