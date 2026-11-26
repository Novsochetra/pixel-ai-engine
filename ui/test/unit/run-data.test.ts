import { describe, expect, it } from 'vitest';
import { formSources, sentData, setRepeat, toggleExport } from '@/training/run-data';
import { defaultValues } from '@/training/training-form';
import { OPTIONS } from '../integration/training-server';

const CREATE = { ...defaultValues(OPTIONS), task: 'create' as const };

describe('the data of a new run', () => {
  it('adds an export with all its sources, and takes them away with it', () => {
    const added = { ...CREATE, ...toggleExport(OPTIONS, CREATE, 'opengameart-v1') };

    expect(added.moreExports).toEqual(['opengameart-v1']);
    expect(added.sources).toEqual(['lpc-4view', 'pac', 'opengameart-2d']);
    expect(formSources(OPTIONS, added).map((source) => source.name)).toEqual(added.sources);
    expect(toggleExport(OPTIONS, added, 'opengameart-v1')).toEqual({
      moreExports: [],
      sources: ['lpc-4view', 'pac'],
    });
  });

  it('keeps a repeat only when it is not once', () => {
    expect(setRepeat({}, 'pac', 5)).toEqual({ pac: 5 });
    expect(setRepeat({ pac: 5 }, 'pac', 1)).toEqual({});
  });

  it('sends no more exports for a rotate run, nor what belongs to them', () => {
    const added = { ...CREATE, ...toggleExport(OPTIONS, CREATE, 'opengameart-v1') };
    const rotate = { ...added, task: 'rotate' as const, repeat: { 'opengameart-2d': 5, pac: 2 } };

    expect(sentData(OPTIONS, rotate)).toEqual({
      moreExports: [],
      sources: ['lpc-4view', 'pac'],
      repeat: { pac: 2 },
    });
  });
});
