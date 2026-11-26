import { describe, expect, it } from 'vitest';
import {
  createBody,
  defaultValues,
  drawWithNote,
  isReady,
  modelFor,
  turnWithNote,
} from '@/create/create-form';
import { BASE, OPTIONS } from '../integration/create-server';

const ROTATE = [{ value: 'runs/rotate-v2/final', label: 'rotate-v2 · final', model: BASE }];
const values = { ...defaultValues(OPTIONS, ROTATE), prompt: ' a frog ', drawWith: 'runs/c/final' };

describe('the create form', () => {
  it('starts from the server defaults and the newest rotate LoRA', () => {
    expect(defaultValues(OPTIONS, ROTATE)).toMatchObject({
      facing: 'front',
      characters: 2,
      sprite: '128',
      drawWith: '',
      turnWith: 'runs/rotate-v2/final',
      drawingModel: 'flux2-klein-4b',
      turningModel: BASE,
    });
    expect(defaultValues(OPTIONS, [])).toMatchObject({
      turnWith: '',
      turningModel: 'flux2-klein-4b',
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

  it('turns only a front view', () => {
    expect(turnWithNote('front')).toBeNull();
    expect(turnWithNote('side')).toMatch(/not turned/);
  });

  it('sends a choice that is turned off as none', () => {
    expect(createBody(values)).toMatchObject({ prompt: 'a frog', drawWith: 'runs/c/final' });
    expect(createBody({ ...values, pose: 'flying' }).drawWith).toBe('');
    expect(createBody({ ...values, facing: 'side' })).toMatchObject({ drawWith: '', turnWith: '' });
  });

  it('is ready once there is something to draw', () => {
    expect(isReady({ ...values, prompt: '   ' })).toBe(false);
    expect(isReady(values)).toBe(true);
  });
});
