import { describe, expect, it } from 'vitest';
import type { MadeTarget } from '@/made/made-client';
import { deleteQuestion, deletedText } from '@/made/made-text';

const made = (target: Partial<MadeTarget>): MadeTarget => ({
  kind: 'generated',
  folder: 'frog',
  title: 'a frog',
  count: 1,
  ...target,
});

describe('deleteQuestion', () => {
  it('says how many characters go with the folder', () => {
    expect(deleteQuestion(made({}))).toMatch(/^Delete “a frog”\? It goes to the trash/);
    expect(deleteQuestion(made({ title: 'a dragon', count: 3 }))).toMatch(
      /the 3 characters made with it/,
    );
  });

  it('warns that a turned character takes its whole set with it', () => {
    expect(deleteQuestion(made({ count: null }))).toMatch(
      /every character made with it, in Create and Rotate/,
    );
  });

  it('names an animation and its clips', () => {
    expect(deleteQuestion(made({ kind: 'animated', title: 'knight', count: 2 }))).toMatch(
      /^Delete the animation of “knight” and its 2 clips\?/,
    );
    expect(deleteQuestion(made({ kind: 'animated', title: 'knight', count: 1 }))).toMatch(
      /^Delete the animation of “knight”\?/,
    );
  });
});

describe('deletedText', () => {
  it('names what was deleted', () => {
    expect(deletedText('a frog')).toBe('Deleted “a frog”.');
  });
});
