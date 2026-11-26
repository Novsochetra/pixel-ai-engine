import type { AnimateOptions } from './animate-client';
import { actionLines, sourceKind, type AnimateValues } from './animate-form';

// What a clip took on an M1 Max when the server names no time for a size and length.
const USUAL_MINUTES = 11;

function sourceProblem(values: AnimateValues) {
  if (!values.source) {
    return 'Choose a character, or upload a PNG.';
  }

  if (sourceKind(values.source) === 'upload') {
    return values.subject.trim() ? null : 'Say what the picture shows.';
  }

  return values.views.length ? null : 'Pick at least one view.';
}

function actionsProblem(actions: string[], options: AnimateOptions) {
  if (!actions.length) {
    return 'Say at least one action, for example: walk.';
  }

  if (actions.length > options.mostActions) {
    return `Give at most ${options.mostActions} actions at a time.`;
  }

  if (actions.some((action) => action.length > options.longestAction)) {
    return `Keep each action to at most ${options.longestAction} characters.`;
  }

  return null;
}

// The same refusals as the server's, said before Animate rather than after it.
export const formProblem = (values: AnimateValues, options: AnimateOptions) =>
  sourceProblem(values) ?? actionsProblem(actionLines(values.actions), options);

// A PNG of your own has one view: the way it is drawn.
export function clipCount(values: AnimateValues) {
  const views = sourceKind(values.source) === 'upload' ? 1 : values.views.length;

  return views * actionLines(values.actions).length;
}

export function minutesEach(options: AnimateOptions, size: string, frames: string) {
  const known = options.minutes.find((entry) => entry.size === size && entry.frames === frames);

  return known?.minutes ?? USUAL_MINUTES;
}

export function estimateText(values: AnimateValues, options: AnimateOptions) {
  const clips = clipCount(values);
  const minutes = clips * minutesEach(options, values.size, values.frames);

  return `${clips} clip${clips === 1 ? '' : 's'}, about ${minutes} min, plus a few minutes to load the models.`;
}
