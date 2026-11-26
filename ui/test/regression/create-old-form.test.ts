import { describe, expect, it } from 'vitest';
import { createBody, defaultValues } from '@/create/create-form';
import { OPTIONS } from '../integration/create-server';

// The old /generate page sent these when only the prompt was filled; the new form must match.
describe('the create form, as the old /generate page', () => {
  it('sends the old defaults', () => {
    const values = { ...defaultValues(OPTIONS, []), prompt: 'a frog wizard with a staff' };

    expect(createBody(values)).toEqual({
      prompt: 'a frog wizard with a staff',
      pose: '',
      facing: 'front',
      characters: 2,
      sprite: '128',
      drawWith: '',
      drawingModel: 'flux2-klein-4b',
      turnWith: '',
      turningModel: 'flux2-klein-4b',
    });
  });
});
