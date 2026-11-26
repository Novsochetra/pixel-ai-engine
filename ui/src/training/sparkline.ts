import { smoothLoss, type Point } from './loss-chart';

export const SPARK_WIDTH = 100;
export const SPARK_HEIGHT = 32;
const PAD = 2;

// The smoothed loss as an SVG polyline, out to the steps planned so the line shows how far it is.
export function sparklinePoints(loss: readonly Point[], steps: number): string {
  const smooth = smoothLoss(loss);
  const values = smooth.map((point) => point[1]);
  const low = Math.min(...values);
  const span = Math.max(...values) - low || 1;
  const last = Math.max(steps, smooth.at(-1)?.[0] ?? 1);

  return smooth
    .map(([step, value]) => {
      const x = (step / last) * SPARK_WIDTH;
      const y = PAD + (1 - (value - low) / span) * (SPARK_HEIGHT - 2 * PAD);

      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
}
