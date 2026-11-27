import { describe, expect, it } from 'vitest';
import { galleryItem, tileText, turnText } from '@/create/create-view';
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

  it('names the reference it was drawn from, or none', () => {
    const drawnFrom = galleryItem({ ...FROG, reference: '20261127-hero.png' });

    expect(drawnFrom.facts).toContainEqual({ label: 'Reference', value: '20261127-hero.png' });
    expect(galleryItem(FROG).facts).toContainEqual({ label: 'Reference', value: 'None' });
  });

  it('says on a tile when it was made and how many characters it holds', () => {
    expect(tileText(DRAGON)).toBe('Nov 24 · 2 characters');
    expect(tileText(FROG)).toBe('Nov 21 · 1 character');
  });

  it('reads a missing date as unknown', () => {
    expect(galleryItem({ ...FROG, createdAt: '' }).facts[0]).toEqual({
      label: 'Made',
      value: 'Unknown',
    });
  });
});
