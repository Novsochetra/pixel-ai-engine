import { describe, expect, it } from 'vitest';
import { defaultValues, formProblem, turnable, turnText } from '@/rotate/rotate-form';
import { fromText, turnedItem } from '@/rotate/turned-view';
import { NEW_UPLOAD, SOURCES } from '../integration/animate-server';
import { LORAS, OPTIONS, TURNED } from '../integration/rotate-server';

describe('the rotate form', () => {
  it('starts on the first character with a front view, and the first LoRA', () => {
    const values = defaultValues(OPTIONS, turnable(SOURCES), LORAS);

    expect(values).toEqual({
      source: 'generated/dragon/s0',
      lora: 'runs/rotate-v2/final',
      turningModel: 'flux2-klein-4b',
      sprite: '128',
      views: ['left', 'back', 'right'],
    });
  });

  it('starts on an upload when no character has a front view', () => {
    const sources = { characters: SOURCES.characters.slice(1), uploads: [NEW_UPLOAD] };

    expect(defaultValues(OPTIONS, turnable(sources), []).source).toBe(NEW_UPLOAD.value);
  });

  it('says what is missing, the source first', () => {
    const values = defaultValues(OPTIONS, turnable(SOURCES), LORAS);

    expect(formProblem({ ...values, source: '' }, [])).toBe('Choose a character, or upload a PNG.');
    expect(formProblem(values, [])).toBe('Train a rotate LoRA first, on the Training screen.');
    expect(formProblem({ ...values, views: [] }, LORAS)).toBe('Pick at least one view to turn to.');
    expect(formProblem(values, LORAS)).toBeNull();
  });

  it('says what Rotate will make', () => {
    const values = defaultValues(OPTIONS, turnable(SOURCES), LORAS);

    expect(turnText({ ...values, views: ['back'] })).toMatch(
      /^Turns the front view to back: 1 picture,/,
    );
  });
});

describe('a turned character', () => {
  it('opens with its views in turning order and says where it came from', () => {
    const item = turnedItem(TURNED[0]!);

    expect(item.pictures.map((picture) => picture.label)).toEqual([
      'Front',
      'Left',
      'Back',
      'Right',
    ]);
    expect(item.subtitle).toMatch(/· 128 px · rotate-v2 · final$/);
    expect(item.facts).toContainEqual({ label: 'Source', value: 'Turned from dragon' });
    expect(fromText(TURNED[1]!)).toBe('Made and turned in Create');
  });
});
