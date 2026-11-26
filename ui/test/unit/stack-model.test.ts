import { describe, expect, it } from 'vitest';
import {
  advanceStack,
  createStack,
  frontAndBack,
  moveBetween,
  parentOf,
  settleStack,
} from '@/navigation/stack/stack-model';

describe('the move between two screens', () => {
  it('pushes into a screen under the one shown and pops back out', () => {
    expect(moveBetween('/training', '/training/rotate-v2', 'PUSH')).toBe('push');
    expect(moveBetween('/training/rotate-v2', '/training', 'PUSH')).toBe('pop');
    expect(moveBetween('/training/rotate-v2', '/training', 'POP')).toBe('pop');
  });

  it('swaps between sections, even from inside one', () => {
    expect(moveBetween('/create', '/training', 'PUSH')).toBe('swap');
    expect(moveBetween('/training/rotate-v2', '/create', 'POP')).toBe('swap');
  });

  it('cuts at once on a redirect, and does not count a longer name as inside', () => {
    expect(moveBetween('/', '/create', 'REPLACE')).toBe('none');
    expect(moveBetween('/train', '/training', 'PUSH')).toBe('swap');
  });

  it('knows the parent of a screen', () => {
    expect(parentOf('/training/rotate-v2')).toBe('/training');
    expect(parentOf('/training')).toBeNull();
  });
});

describe('the screen stack', () => {
  it('keeps the screen pushed from under the one pushed, and brings it back on a pop', () => {
    const pushed = advanceStack(createStack('/training'), '/training/a', 'PUSH');

    expect(frontAndBack(pushed)).toEqual({ front: '/training/a', back: '/training' });
    expect(settleStack(pushed).layers).toEqual(['/training', '/training/a']);

    const popped = advanceStack(settleStack(pushed), '/training', 'POP');

    expect(frontAndBack(popped)).toEqual({ front: '/training/a', back: '/training' });
    expect(popped.layers).toEqual(['/training', '/training/a']);
    expect(settleStack(popped).layers).toEqual(['/training']);
  });

  it('lets a swap drop the screens under the one it leaves', () => {
    const pushed = settleStack(advanceStack(createStack('/training'), '/training/a', 'PUSH'));
    const swapped = advanceStack(pushed, '/create', 'PUSH');

    expect(swapped.move).toBe('swap');
    expect(frontAndBack(swapped)).toEqual({ front: '/create', back: '/training/a' });
    expect(swapped.layers).toEqual(['/training/a', '/create']);
    expect(settleStack(swapped).layers).toEqual(['/create']);
  });

  it('replaces the screen at once on a redirect', () => {
    const redirected = advanceStack(createStack('/'), '/create', 'REPLACE');

    expect(redirected).toMatchObject({ layers: ['/create'], leaving: null, move: 'none' });
  });

  it('counts each move, and stays the same when the screen does', () => {
    const stack = createStack('/create');
    const moved = advanceStack(stack, '/library', 'PUSH');

    expect(advanceStack(stack, '/create', 'PUSH')).toBe(stack);
    expect(advanceStack(moved, '/create', 'PUSH').id).toBe(moved.id + 1);
  });
});
