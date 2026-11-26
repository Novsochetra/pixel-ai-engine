import type { CSSProperties } from 'react';
import { ChartPlot } from './ChartPlot';
import { ChartTable } from './ChartTable';
import { lossText, readoutAt, stepText, type ReadoutRow } from './chart-readout';
import { chartBox, chartScale, smoothLoss, type Point } from './loss-chart';
import type { Run } from './training-client';
import { useChartPointer } from './use-chart-pointer';
import { useChartWidth } from './use-chart-width';
import './loss-chart.css';

const FALLBACK_WIDTH = 560;

function Legend() {
  return (
    <ul className="loss-chart__legend" aria-label="Lines">
      <li>
        <span className="loss-chart__key loss-chart__key--val" aria-hidden="true" />
        Val loss, on the fixed check pairs
      </li>
      <li>
        <span className="loss-chart__key loss-chart__key--loss" aria-hidden="true" />
        Training loss, smoothed
      </li>
    </ul>
  );
}

// Values lead and the names follow: here the reader knows the lines and wants the numbers.
function Readout({ row, left }: { row: ReadoutRow; left: number }) {
  return (
    <div className="loss-chart__readout" style={{ '--readout-x': `${left}px` } as CSSProperties}>
      <span className="loss-chart__readout-step">Step {stepText(row.step)}</span>
      <span className="loss-chart__readout-row">
        <span className="loss-chart__line-key loss-chart__key--loss" aria-hidden="true" />
        <strong>{lossText(row.loss)}</strong> loss
      </span>
      <span className="loss-chart__readout-row">
        <span className="loss-chart__line-key loss-chart__key--val" aria-hidden="true" />
        <strong>{lossText(row.val?.[1])}</strong> val loss
        {row.val && row.val[0] !== row.step ? ` at ${stepText(row.val[0])}` : ''}
      </span>
    </div>
  );
}

function chartLabel(run: Run, val: readonly Point[]) {
  const last = val.at(-1);
  const check = last ? `, val loss ${lossText(last[1])} at step ${stepText(last[0])}` : '';

  return `Loss of ${run.name} over ${stepText(run.step)} steps${check}.`;
}

// Loss and val loss over the steps, out to the steps planned so the line shows how far it is.
export function LossChart({ run }: { run: Run }) {
  const { ref, width } = useChartWidth(FALLBACK_WIDTH);
  const smooth = smoothLoss(run.loss);
  const box = chartBox(width);
  const values = [...smooth, ...run.val].map((point) => point[1]);
  const scale = chartScale(Math.max(run.steps, run.step), values, box);
  const pointer = useChartPointer(smooth, scale);
  const row = pointer.index === null ? null : readoutAt(smooth, run.val, pointer.index);

  if (!smooth.length) {
    return <p className="loss-chart__empty">No steps yet. The chart starts with the first step.</p>;
  }

  return (
    <figure className="loss-chart">
      <Legend />
      <div className="loss-chart__frame" ref={ref}>
        <ChartPlot
          smooth={smooth}
          val={run.val}
          scale={scale}
          box={box}
          pointer={pointer}
          label={chartLabel(run, run.val)}
        />
        {row ? <Readout row={row} left={scale.x(row.step)} /> : null}
      </div>
      <ChartTable run={run} smooth={smooth} />
    </figure>
  );
}
