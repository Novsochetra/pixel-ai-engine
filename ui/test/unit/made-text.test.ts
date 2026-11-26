import { describe, expect, it } from 'vitest';
import { deleteQuestion, deletedText } from '@/made/made-text';

describe('deleteQuestion', () => {
  it('says how much goes with the folder', () => {
    expect(deleteQuestion('a frog', 1)).toMatch(/^Delete “a frog”\? It goes to the trash/);
    expect(deleteQuestion('a dragon', 3)).toMatch(/the 3 characters made with it/);
  });

  it('warns that a turned character takes its whole set with it', () => {
    expect(deleteQuestion('a knight', null)).toMatch(
      /every character made with it, in Create and Rotate/,
    );
  });
});

describe('deletedText', () => {
  it('names what was deleted', () => {
    expect(deletedText('a frog')).toBe('Deleted “a frog”.');
  });
});
