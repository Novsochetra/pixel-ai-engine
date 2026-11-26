// A push goes into a screen under the one shown, a pop comes back out of it, and a swap trades one
// section for another, as a tab bar or sidebar does.
export type Move = 'push' | 'pop' | 'swap' | 'none';

export type NavigationType = 'PUSH' | 'POP' | 'REPLACE';

export interface StackModel {
  // the paths of the screens in the document, in the order they were added
  layers: string[];
  top: string;
  // the screen a move is leaving, until the move settles
  leaving: string | null;
  move: Move;
  // counts moves, so a move that lands mid-move restarts the animation
  id: number;
}

const isInside = (path: string, parent: string) => path.startsWith(`${parent}/`);

export function parentOf(path: string): string | null {
  const cut = path.lastIndexOf('/');

  return cut > 0 ? path.slice(0, cut) : null;
}

export function moveBetween(from: string, to: string, navigationType: NavigationType): Move {
  if (from === to || navigationType === 'REPLACE') {
    return 'none';
  }

  if (isInside(to, from)) {
    return 'push';
  }

  return isInside(from, to) ? 'pop' : 'swap';
}

// Layers keep their order, so React never moves one in the document, which would lose its scroll.
function keepOnly(layers: readonly string[], kept: readonly (string | null)[]): string[] {
  const wanted = new Set(kept.filter((path): path is string => path !== null));
  const staying = layers.filter((path) => wanted.has(path));

  return [...staying, ...[...wanted].filter((path) => !staying.includes(path))];
}

// The screen a pop comes back to stays rendered under the one pushed over it, so it shows again
// as it was left, at its own scroll, as an iOS navigation stack keeps it.
function parentKept(layers: readonly string[], top: string) {
  const parent = parentOf(top);

  return parent && layers.includes(parent) ? parent : null;
}

export function createStack(top: string): StackModel {
  return { layers: [top], top, leaving: null, move: 'none', id: 0 };
}

export function advanceStack(
  stack: StackModel,
  to: string,
  navigationType: NavigationType,
): StackModel {
  if (to === stack.top) {
    return stack;
  }

  const move = moveBetween(stack.top, to, navigationType);
  const id = stack.id + 1;

  if (move === 'none') {
    return { layers: [to], top: to, leaving: null, move, id };
  }

  const layers = keepOnly(stack.layers, [parentKept(stack.layers, to), stack.top, to]);

  return { layers, top: to, leaving: stack.top, move, id };
}

export function settleStack(stack: StackModel): StackModel {
  const layers = keepOnly(stack.layers, [parentKept(stack.layers, stack.top), stack.top]);

  return { ...stack, layers, leaving: null, move: 'none' };
}

// The screen that moves over the other: the one arriving on a push or swap, the one leaving on a pop.
export function frontAndBack(stack: StackModel): { front: string; back: string } | null {
  if (!stack.leaving) {
    return null;
  }

  return stack.move === 'pop'
    ? { front: stack.leaving, back: stack.top }
    : { front: stack.top, back: stack.leaving };
}
