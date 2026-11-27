import { describe, expect, it } from 'vitest';
import {
  createBody,
  defaultValues,
  drawChoices,
  drawWithNote,
  isReady,
  facingNote,
  modelFor,
} from '@/create/create-form';
import { BASE, OPTIONS } from '../integration/create-server';

const ROTATE = [{ value: 'runs/rotate-v2/final', label: 'rotate-v2 · final', model: BASE }];
const CREATE = [{ value: 'runs/create-v1/final', label: 'create-v1 · final', model: BASE }];
const SIDES = {
  value: 'runs/pixie-draw-v1/final',
  label: 'pixie-draw-v1 · final',
  model: BASE,
  views: ['front' as const, 'side' as const],
};
const BOTH = [...CREATE, SIDES];
const values = {
  ...defaultValues(OPTIONS, []),
  prompt: ' a frog ',
  drawWith: 'runs/create-v1/final',
};

describe('the create form', () => {
  it('draws with the newest create LoRA on the base model it learnt on, never turning', () => {
    expect(defaultValues(OPTIONS, CREATE)).toEqual({
      prompt: '',
      pose: '',
      facing: 'front',
      characters: 2,
      sprite: '128',
      drawWith: 'runs/create-v1/final',
      drawingModel: BASE,
      reference: '',
    });
    expect(defaultValues(OPTIONS, [])).toMatchObject({
      drawWith: '',
      drawingModel: 'flux2-klein-4b',
    });
  });

  it('picks the model a LoRA learnt on, and the default for none', () => {
    expect(modelFor(ROTATE, 'runs/rotate-v2/final', 'fast')).toBe(BASE);
    expect(modelFor(ROTATE, '', 'fast')).toBe('fast');
    expect(modelFor(ROTATE, 'runs/gone/final', 'fast')).toBe('fast');
  });

  it('lets a create LoRA draw only standing, and a side view only once one learnt sides', () => {
    expect(drawWithNote({ facing: 'front', pose: '' }, CREATE)).toBeNull();
    expect(drawWithNote({ facing: 'front', pose: ' Standing ' }, CREATE)).toBeNull();
    expect(drawWithNote({ facing: 'front', pose: 'flying' }, CREATE)).toMatch(/standing/);
    expect(drawWithNote({ facing: 'side', pose: '' }, CREATE)).toMatch(/learnt side views/);
    expect(drawWithNote({ facing: 'side', pose: '' }, BOTH)).toBeNull();
    expect(drawWithNote({ facing: 'side', pose: 'flying' }, BOTH)).toMatch(/standing/);
  });

  it('lists every LoRA for a front view and only the side-trained ones for a side view', () => {
    expect(drawChoices(BOTH, 'front')).toEqual(BOTH);
    expect(drawChoices(BOTH, 'side')).toEqual([SIDES]);
  });

  it('says a front view is turned later on Rotate, and a side view is mirrored', () => {
    expect(facingNote('front')).toMatch(/Turn it on Rotate/);
    expect(facingNote('side')).toMatch(/left is its mirror/);
  });

  it('sends a choice that is turned off as none', () => {
    expect(createBody(values, BOTH)).toMatchObject({
      prompt: 'a frog',
      drawWith: 'runs/create-v1/final',
    });
    expect(createBody({ ...values, pose: 'flying' }, BOTH).drawWith).toBe('');
    expect(createBody({ ...values, facing: 'side' }, BOTH).drawWith).toBe('');
    expect(createBody({ ...values, drawWith: 'runs/gone/final' }, BOTH).drawWith).toBe('');
  });

  it('sends a side view with a LoRA that learnt sides', () => {
    const side = { ...values, facing: 'side' as const, drawWith: SIDES.value };

    expect(createBody(side, BOTH).drawWith).toBe(SIDES.value);
  });

  it('is ready once there is something to draw', () => {
    expect(isReady({ ...values, prompt: '   ' })).toBe(false);
    expect(isReady(values)).toBe(true);
  });
});
