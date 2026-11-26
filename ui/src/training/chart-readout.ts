import { nearestIndex, type Point } from './loss-chart';

export interface ReadoutRow {
  step: number;
  loss: number | null;
  val: Point | null;
}

const TABLE_ROWS = 10;

// The val loss is checked only every hundred steps or so: the last check up to the step read.
export function lastCheck(val: readonly Point[], step: number): Point | null {
  return val.findLast(([at]) => at <= step) ?? null;
}

export function readoutAt(smooth: readonly Point[], val: readonly Point[], index: number) {
  const point = smooth[index];

  if (!point) {
    return null;
  }

  return { step: point[0], loss: point[1], val: lastCheck(val, point[0]) };
}

// The table carries every check; a run with none yet gets the smoothed loss at even steps.
export function tableRows(smooth: readonly Point[], val: readonly Point[]): ReadoutRow[] {
  if (val.length) {
    return val.map((point) => ({
      step: point[0],
      loss: smooth.length ? smooth[nearestIndex(smooth, point[0])]![1] : null,
      val: point,
    }));
  }

  const every = Math.max(1, Math.ceil(smooth.length / TABLE_ROWS));

  return smooth
    .filter((_, i) => i % every === 0 || i === smooth.length - 1)
    .map(([step, loss]) => ({ step, loss, val: null }));
}

export const lossText = (value: number | null | undefined) =>
  value === null || value === undefined ? '–' : value.toFixed(4);

export const stepText = (step: number) => step.toLocaleString('en-US');
