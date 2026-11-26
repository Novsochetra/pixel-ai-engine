import { describe, expect, it } from 'vitest';
import { exportsView } from '@/library/collection-view';

// An export made without a leak check (opengameart-v1) once broke the whole exports list.
describe('an export without a leak check', () => {
  it('is listed and says the check was not run', () => {
    const view = exportsView({
      exports: [
        {
          name: 'opengameart-v1',
          createdAt: '2026-11-24T03:48:36+00:00',
          characters: { train: { 'opengameart-2d': 3 } },
          leftOut: {},
          isLeakFree: null,
          licenses: { 'opengameart-2d': 'CC0' },
          samples: [
            {
              character: 'opengameart-2d/0',
              split: 'train',
              views: [{ label: 'front', src: '/api/files/exports/opengameart-v1/front.png' }],
            },
          ],
        },
      ],
    });

    expect(view.sections[0]!.title).toBe('opengameart-v1');
    expect(view.summary[0]!.facts).toContainEqual({ label: 'Leak check', value: 'Not run' });
    expect(view.summary[0]!.facts).toContainEqual({ label: 'Left out', value: 'None' });
  });
});
