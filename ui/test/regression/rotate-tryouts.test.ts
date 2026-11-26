import { describe, expect, it } from 'vitest';
import { rotateTryoutsView } from '@/rotate/rotate-tryouts';
import { TRYOUTS } from '../integration/rotate-server';

// The first try-outs (tryout-20261118-1730 and before) only drew from text: Rotate shows none of them.
describe('the rotate try-outs', () => {
  it('leave out the text-to-character pictures', () => {
    const view = rotateTryoutsView(TRYOUTS);

    expect(view.sections.map((section) => section.title)).toEqual(['pac/val/3 → back']);
    expect(view.sections[0]!.items.map((item) => item.title)).toEqual([
      'front given',
      'real back',
      'flux2-klein-4b',
    ]);
  });

  it('say so when a run turned no test character', () => {
    const run = { ...TRYOUTS.run!, groups: TRYOUTS.run!.groups.slice(0, 1) };
    const view = rotateTryoutsView({ ...TRYOUTS, run });

    expect(view.sections).toEqual([]);
    expect(view.empty.title).toBe('No turned test characters in this run');
    expect(view.picker?.value).toBe('v2-flux2-klein-4b');
  });

  it('keep the Library notice when there are no try-outs at all', () => {
    expect(rotateTryoutsView({ runs: [], run: null }).empty.title).toBe('No try-outs yet');
  });
});
