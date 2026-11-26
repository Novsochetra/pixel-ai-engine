import { describe, expect, it } from 'vitest';
import { estimateText, formProblem } from '@/animate/animate-checks';
import {
  actionLines,
  animateBody,
  defaultValues,
  sourceDefaults,
  toggleView,
  type AnimateValues,
} from '@/animate/animate-form';
import { OPTIONS, SOURCES } from '../integration/animate-server';

const DRAGON: AnimateValues = {
  source: 'generated/dragon/s0',
  subject: 'a lava dragon',
  views: ['front', 'right'],
  actions: 'idle\nwalk',
  size: '384',
  frames: '33',
};

describe('the animate form', () => {
  it('starts on the newest character, with its words and the usual views', () => {
    expect(defaultValues(OPTIONS, SOURCES)).toEqual(DRAGON);
  });

  it('starts on an upload when no character was made', () => {
    const uploads = [{ value: 'uploads/a.png', label: 'a.png', src: '/a.png' }];

    expect(defaultValues(OPTIONS, { characters: [], uploads }).source).toBe('uploads/a.png');
  });

  it('picks the first view a character has when it has none of the usual ones', () => {
    const backOnly = { ...SOURCES.characters[0]!, views: ['back'] };

    expect(
      sourceDefaults(backOnly.value, OPTIONS, { characters: [backOnly], uploads: [] }),
    ).toEqual({
      subject: 'a lava dragon',
      views: ['back'],
    });
  });

  it('gives an upload no words and no views', () => {
    expect(sourceDefaults('uploads/a.png', OPTIONS, SOURCES)).toEqual({ subject: '', views: [] });
  });

  it('tidies the actions as the server does', () => {
    expect(actionLines('  idle \n\nWalk\nwalk\nflaps   its wings')).toEqual([
      'idle',
      'Walk',
      'flaps its wings',
    ]);
  });

  it('keeps the views in their own order', () => {
    expect(toggleView(['right'], 'front', OPTIONS.views)).toEqual(['front', 'right']);
    expect(toggleView(['front', 'right'], 'front', OPTIONS.views)).toEqual(['right']);
  });

  it('sends an upload with no views, and tidy words', () => {
    const body = animateBody({ ...DRAGON, source: 'uploads/a.png', subject: ' a  slime ' });

    expect(body.views).toEqual([]);
    expect(body.subject).toBe('a slime');
  });
});

describe('the checks before Animate', () => {
  it('finds nothing wrong with a full form', () => {
    expect(formProblem(DRAGON, OPTIONS)).toBeNull();
  });

  it.each([
    [{ source: '' }, 'Choose a character, or upload a PNG.'],
    [{ views: [] }, 'Pick at least one view.'],
    [{ source: 'uploads/a.png', subject: ' ' }, 'Say what the picture shows.'],
    [{ actions: '\n ' }, 'Say at least one action, for example: walk.'],
    [{ actions: 'a\nb\nc\nd\ne\nf\ng\nh\ni' }, 'Give at most 8 actions at a time.'],
    [{ actions: 'x'.repeat(201) }, 'Keep each action to at most 200 characters.'],
  ])('says what is missing in %o', (change, problem) => {
    expect(formProblem({ ...DRAGON, ...change }, OPTIONS)).toBe(problem);
  });

  it('counts a clip per view and action, at the minutes of its size and length', () => {
    expect(estimateText(DRAGON, OPTIONS)).toBe(
      '4 clips, about 44 min, plus a few minutes to load the models.',
    );
    expect(
      estimateText({ ...DRAGON, size: '512', frames: '17', actions: 'idle' }, OPTIONS),
    ).toMatch(/^2 clips, about 16 min/);
  });

  it('counts an upload as one view', () => {
    expect(estimateText({ ...DRAGON, source: 'uploads/a.png' }, OPTIONS)).toMatch(/^2 clips/);
  });
});
