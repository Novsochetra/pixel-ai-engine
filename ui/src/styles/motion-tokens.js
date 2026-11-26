const DURATION_PATTERN = /^(\d+(?:\.\d+)?|\.\d+)(ms|s)$/;

export function parseDuration(value) {
  const match = DURATION_PATTERN.exec(String(value ?? '').trim());
  if (!match) {
    return 0;
  }

  const amount = Number(match[1]);

  return match[2] === 's' ? amount * 1000 : amount;
}

export function readToken(document, name) {
  const style = document.defaultView.getComputedStyle(document.documentElement);

  return style.getPropertyValue(name).trim();
}

export const readDuration = (document, name) => parseDuration(readToken(document, name));

export function prefersReducedMotion(window) {
  return Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);
}

// Script-driven motion reads its timing from the tokens like the CSS does; without them (the tests)
// its length is 0, so it does not play.
export function readTiming(document, { duration, easing }) {
  return {
    duration: readDuration(document, duration),
    easing: readToken(document, easing) || 'linear',
  };
}
