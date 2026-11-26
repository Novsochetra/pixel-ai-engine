import { describe, expect, it } from 'vitest';
import { lastCheck, readoutAt, tableRows } from '@/training/chart-readout';
import {
  chartBox,
  chartScale,
  linePath,
  nearestIndex,
  niceTicks,
  smoothLoss,
  tickDecimals,
  type Point,
} from '@/training/loss-chart';

const BOX = { width: 240, height: 140, left: 40, right: 0, top: 20, bottom: 20 };

describe('the loss chart', () => {
  it('smooths the loss with a trailing mean', () => {
    const points: Point[] = [
      [1, 0.4],
      [2, 0.2],
      [3, 0.3],
    ];

    expect(smoothLoss(points, 2)).toEqual([
      [1, 0.4],
      [2, 0.30000000000000004],
      [3, 0.25],
    ]);
  });

  it('thins a long run to a few hundred points and keeps the last step', () => {
    const points: Point[] = Array.from({ length: 2000 }, (_, i) => [i + 1, 0.1]);
    const smooth = smoothLoss(points);

    expect(smooth.length).toBeLessThanOrEqual(241);
    expect(smooth.at(-1)![0]).toBe(2000);
  });

  it('puts the axis on round numbers that cover the data', () => {
    expect(niceTicks(0, 2000)).toEqual([0, 500, 1000, 1500, 2000]);
    expect(niceTicks(0.046, 0.2)).toEqual([0, 0.05, 0.1, 0.15, 0.2]);
    expect(niceTicks(0.0581, 0.0934)).toEqual([0.05, 0.06, 0.07, 0.08, 0.09, 0.1]);
    expect(niceTicks(0.1, 0.1)).toEqual([0.1, 0.15]);
    expect(niceTicks(0, 2500)).toEqual([0, 1000, 2000, 3000]);
  });

  it('shows as many decimals as the ticks need', () => {
    expect(tickDecimals([0, 0.05, 0.1])).toBe(2);
    expect(tickDecimals([0, 500, 1000])).toBe(0);
    expect(tickDecimals([0.05, 0.06])).toBe(2);
  });

  it('maps steps left to right and lower loss further down', () => {
    const scale = chartScale(2000, [0, 0.1], BOX);

    expect(scale.steps).toEqual([0, 500, 1000, 1500, 2000]);
    expect(scale.x(0)).toBe(40);
    expect(scale.x(2000)).toBe(240);
    expect(scale.y(0.1)).toBe(20);
    expect(scale.y(0)).toBe(120);
    expect(scale.stepAt(140)).toBe(1000);
  });

  it('has an axis before the first step is logged', () => {
    const scale = chartScale(2000, [], BOX);

    expect(scale.values).toEqual([0, 1]);
    expect(scale.y(0)).toBe(120);
  });

  it('draws a path through each point', () => {
    const scale = chartScale(2000, [0, 0.1], BOX);

    expect(
      linePath(
        [
          [0, 0.1],
          [2000, 0],
        ],
        scale,
      ),
    ).toBe('M40.0,20.0L240.0,120.0');
    expect(linePath([], scale)).toBe('');
  });

  it('finds the drawn point nearest a step', () => {
    const points: Point[] = [
      [5, 0],
      [10, 0],
      [20, 0],
    ];

    expect(nearestIndex(points, 0)).toBe(0);
    expect(nearestIndex(points, 16)).toBe(2);
    expect(nearestIndex(points, 99)).toBe(2);
  });

  it('keeps room for the axis numbers whatever the width', () => {
    expect(chartBox(320)).toMatchObject({ width: 320, left: 44 });
  });
});

describe('the chart readout', () => {
  const smooth: Point[] = [
    [50, 0.2],
    [100, 0.15],
    [150, 0.12],
  ];
  const val: Point[] = [[100, 0.14]];

  it('reads the last check up to the step', () => {
    expect(lastCheck(val, 99)).toBeNull();
    expect(lastCheck(val, 150)).toEqual([100, 0.14]);
    expect(readoutAt(smooth, val, 2)).toEqual({ step: 150, loss: 0.12, val: [100, 0.14] });
    expect(readoutAt(smooth, val, 7)).toBeNull();
  });

  it('lists each check with the smoothed loss beside it', () => {
    expect(tableRows(smooth, val)).toEqual([{ step: 100, loss: 0.15, val: [100, 0.14] }]);
  });

  it('lists the smoothed loss when there is no check yet', () => {
    expect(tableRows(smooth, []).map((row) => row.step)).toEqual([50, 100, 150]);
  });
});
