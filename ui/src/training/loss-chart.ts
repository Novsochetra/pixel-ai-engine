export type Point = readonly [step: number, value: number];

export interface Box {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
}

export interface Scale {
  x: (step: number) => number;
  y: (value: number) => number;
  stepAt: (x: number) => number;
  steps: number[];
  values: number[];
}

const SMOOTH_WINDOW = 25;
const MOST_POINTS = 240;

// Room on the left for "0.150", below for the step numbers.
export const chartBox = (width: number): Box => ({
  width,
  height: 176,
  left: 44,
  right: 16,
  top: 12,
  bottom: 28,
});

// One step's loss jumps with the pictures it drew; a trailing mean shows where it is heading.
// Thinned too, so a run of 20,000 steps still draws a light path.
export function smoothLoss(points: readonly Point[], window = SMOOTH_WINDOW): Point[] {
  const every = Math.max(1, Math.ceil(points.length / MOST_POINTS));
  const smooth: Point[] = [];

  for (let i = 0; i < points.length; i += 1) {
    if (i % every === 0 || i === points.length - 1) {
      const chunk = points.slice(Math.max(0, i - window + 1), i + 1);
      const mean = chunk.reduce((sum, point) => sum + point[1], 0) / chunk.length;

      smooth.push([points[i]![0], mean]);
    }
  }

  return smooth;
}

// Round axis numbers: steps of 1, 2 or 5 times a power of ten, covering low to high.
export function niceTicks(low: number, high: number, count = 4): number[] {
  const span = high > low ? high - low : Math.abs(high) || 1;
  const rough = span / count;
  const power = 10 ** Math.floor(Math.log10(rough));
  const step = [1, 2, 5, 10].map((times) => times * power).find((size) => size >= rough)!;
  const first = Math.floor(low / step);
  const last = Math.max(Math.ceil(high / step - 1e-9), first + 1);
  const ticks: number[] = [];

  for (let i = first; i <= last; i += 1) {
    ticks.push(Number((i * step).toPrecision(12)));
  }

  return ticks;
}

export function chartScale(lastStep: number, values: readonly number[], box: Box): Scale {
  const steps = niceTicks(0, Math.max(lastStep, 1));
  // A run that has just started has no loss yet; its chart still needs an axis to draw on.
  const ticks = values.length ? niceTicks(Math.min(...values), Math.max(...values)) : [0, 1];
  const xEnd = steps.at(-1)!;
  const yLow = ticks[0]!;
  const yHigh = ticks.at(-1)!;
  const plotWidth = box.width - box.left - box.right;
  const plotHeight = box.height - box.top - box.bottom;

  return {
    x: (step) => box.left + (plotWidth * step) / xEnd,
    y: (value) => box.top + (plotHeight * (yHigh - value)) / (yHigh - yLow),
    stepAt: (x) => ((x - box.left) * xEnd) / plotWidth,
    steps,
    values: ticks,
  };
}

export function linePath(points: readonly Point[], scale: Pick<Scale, 'x' | 'y'>): string {
  return points
    .map(([step, value], i) => {
      const command = i === 0 ? 'M' : 'L';

      return `${command}${scale.x(step).toFixed(1)},${scale.y(value).toFixed(1)}`;
    })
    .join('');
}

export function nearestIndex(points: readonly Point[], step: number): number {
  let best = 0;

  points.forEach(([at], i) => {
    if (Math.abs(at - step) < Math.abs(points[best]![0] - step)) {
      best = i;
    }
  });

  return best;
}

// Ticks a tenth apart show one decimal more than ticks a whole apart.
export function tickDecimals(ticks: readonly number[]): number {
  const step = ticks.length > 1 ? ticks[1]! - ticks[0]! : 1;

  return Math.max(0, -Math.floor(Math.log10(step)));
}
