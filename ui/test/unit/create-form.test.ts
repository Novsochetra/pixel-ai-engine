import { describe, expect, it } from 'vitest';
import {
  createBody,
  defaultValues,
  drawWithNote,
  isReady,
  facingNote,
  modelFor,
} from '@/create/create-form';
import { BASE, OPTIONS } from '../integration/create-server';

const ROTATE = [{ value: 'runs/rotate-v2/final', label: 'rotate-v2 · final', model: BASE }];
const CREATE = [{ value: 'runs/create-v1/final', label: 'create-v1 · final', model: BASE }];
const values = { ...defaultValues(OPTIONS, []), prompt: ' a frog ', drawWith: 'runs/c/final' };

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

  it('lets a create LoRA draw only a standing front view', () => {
    expect(drawWithNote({ facing: 'front', pose: '' })).toBeNull();
    expect(drawWithNote({ facing: 'front', pose: ' Standing ' })).toBeNull();
    expect(drawWithNote({ facing: 'front', pose: 'flying' })).toMatch(/standing/);
    expect(drawWithNote({ facing: 'side', pose: '' })).toMatch(/front views/);
  });

  it('says a front view is turned later on Rotate, and a side view is mirrored', () => {
    expect(facingNote('front')).toMatch(/Turn it on Rotate/);
    expect(facingNote('side')).toMatch(/left is its mirror/);
  });

  it('sends a choice that is turned off as none', () => {
    expect(createBody(values)).toMatchObject({ prompt: 'a frog', drawWith: 'runs/c/final' });
    expect(createBody({ ...values, pose: 'flying' }).drawWith).toBe('');
    expect(createBody({ ...values, facing: 'side' }).drawWith).toBe('');
  });

  it('is ready once there is something to draw', () => {
    expect(isReady({ ...values, prompt: '   ' })).toBe(false);
    expect(isReady(values)).toBe(true);
  });
});
