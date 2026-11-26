import { describe, expect, it } from 'vitest';
import { SECTIONS, moreSections, sectionAt, tabSections } from '@/navigation/sections';

describe('sections', () => {
  it('fit a tab bar of five with More', () => {
    expect(tabSections().length + 1).toBeLessThanOrEqual(5);
    expect(tabSections().length + moreSections().length).toBe(SECTIONS.length);
  });

  it('are found by their path and the paths under it', () => {
    expect(sectionAt('/library')?.id).toBe('library');
    expect(sectionAt('/library/pac-12')?.id).toBe('library');
    expect(sectionAt('/libraryish')).toBeUndefined();
  });
});
