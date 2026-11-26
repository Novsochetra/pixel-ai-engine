import { lossText, stepText, tableRows } from './chart-readout';
import type { Point } from './loss-chart';
import type { Run } from './training-client';

// Every value the chart draws can be read without pointing at it, as the dataviz rules ask.
export function ChartTable({ run, smooth }: { run: Run; smooth: readonly Point[] }) {
  return (
    <details className="loss-chart__table">
      <summary>Show as a table</summary>
      <table>
        <caption className="visually-hidden">Loss of {run.name} by step</caption>
        <thead>
          <tr>
            <th scope="col">Step</th>
            <th scope="col">Val loss</th>
            <th scope="col">Loss, smoothed</th>
          </tr>
        </thead>
        <tbody>
          {tableRows(smooth, run.val).map((row) => (
            <tr key={row.step}>
              <th scope="row">{stepText(row.step)}</th>
              <td>{lossText(row.val?.[1])}</td>
              <td>{lossText(row.loss)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  );
}
