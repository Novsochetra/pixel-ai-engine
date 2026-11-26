import { prefersReducedMotion, readTiming, readToken } from '@/styles/motion-tokens.js';
import type { Move } from './stack-model';

type Played = Exclude<Move, 'none'>;

export interface MoveFrames {
  front: Keyframe[];
  back: Keyframe[];
}

export interface MoveLook {
  motion: 'slide' | 'zoom';
  offsetUnder: string;
  dimUnder: string;
  shadow: string;
  scaleUnder: string;
  scaleAway: string;
  reduced: boolean;
}

// The screen left fades out before the one arriving is fully in, so the two never show through
// each other for long: both are glass over the same glow.
const GONE_AT = 0.6;

const reversed = (frames: Keyframe[]) =>
  [...frames]
    .reverse()
    .map((frame) =>
      typeof frame.offset !== 'number' ? frame : { ...frame, offset: 1 - frame.offset },
    );

const playedAs = (move: Played, push: MoveFrames): MoveFrames =>
  move === 'pop' ? { front: reversed(push.front), back: reversed(push.back) } : push;

const fadeFrames = (): MoveFrames => ({
  front: [{ opacity: 0 }, { opacity: 1 }],
  back: [{ opacity: 1 }, { opacity: 0, offset: GONE_AT }, { opacity: 0 }],
});

// A push zooms in, as a Mac app goes into a folder: the screen arriving grows into place as it fades
// in, while the one left grows a little past the viewer and fades; a pop zooms back out. Only
// opacity and scale change, so the compositor plays it alone, never waiting on the screen's work.
function zoomFrames(look: MoveLook): MoveFrames {
  return {
    front: [
      { opacity: 0, scale: look.scaleAway },
      { opacity: 1, scale: '1' },
    ],
    back: [
      { opacity: 1, scale: '1' },
      { opacity: 0, offset: GONE_AT },
      { opacity: 0, scale: look.scaleUnder },
    ],
  };
}

// A push slides the screen arriving in from the right with a shadow on its edge, over the one left,
// which slides a little to the left and dims; a pop plays it backwards, as an iOS navigation stack.
function slideFrames(look: MoveLook): MoveFrames {
  return {
    front: [
      { translate: '100% 0', boxShadow: look.shadow },
      { translate: '0 0', boxShadow: look.shadow },
    ],
    back: [
      { translate: '0 0', filter: 'brightness(1)' },
      { translate: `${look.offsetUnder} 0`, filter: `brightness(${look.dimUnder})` },
    ],
  };
}

const fades = (move: Played, look: MoveLook) => move === 'swap' || look.reduced;

// Sections swap with a cross-fade, as tabs do. With reduced motion every move only fades, as iOS
// dissolves instead: the screen leaving fades out early, whichever of the two is on top.
export function moveFrames(move: Played, look: MoveLook): MoveFrames {
  if (fades(move, look)) {
    const fade = fadeFrames();

    return move === 'pop' ? { front: fade.back, back: fade.front } : fade;
  }

  return playedAs(move, look.motion === 'zoom' ? zoomFrames(look) : slideFrames(look));
}

export const lookOf = (document: Document): MoveLook => ({
  motion: readToken(document, '--motion-navigation') === 'zoom' ? 'zoom' : 'slide',
  offsetUnder: readToken(document, '--offset-under') || '-30%',
  dimUnder: readToken(document, '--dim-under') || '1',
  shadow: readToken(document, '--shadow-navigation') || 'none',
  scaleUnder: readToken(document, '--scale-under') || '1',
  scaleAway: readToken(document, '--scale-away') || '1',
  reduced: prefersReducedMotion(document.defaultView),
});

export function timingOf(document: Document, move: Played, look: MoveLook) {
  return fades(move, look)
    ? readTiming(document, { duration: '--duration-swap', easing: '--easing-standard' })
    : readTiming(document, { duration: '--duration-navigation', easing: '--easing-navigation' });
}

// Plays a move on its two layers and settles once both have; with no timing (the tests) it settles
// at once. Each layer holds the last frame until the stack settles and cancels it, since one that
// went back to rest first would stand the screen popped over the window again for a frame.
export function playMove(move: Played, layers: { front: HTMLElement; back: HTMLElement }) {
  const document = layers.front.ownerDocument;
  const look = lookOf(document);
  const timing = timingOf(document, move, look);

  if (timing.duration <= 0 || !layers.front.animate) {
    return { finished: Promise.resolve(), cancel: () => {} };
  }

  const frames = moveFrames(move, look);
  const held = { ...timing, fill: 'forwards' as const };
  const animations = [
    layers.front.animate(frames.front, held),
    layers.back.animate(frames.back, held),
  ];
  const finished = Promise.all(animations.map((animation) => animation.finished)).then(
    () => {},
    () => {},
  );

  return { finished, cancel: () => animations.forEach((animation) => animation.cancel()) };
}
