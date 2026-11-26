import { ViewTransition } from 'react';
import { Link } from 'react-router';
import type { Choice } from '@/create/create-client';
import { RunNumbers, TrainingNow } from './RunNumbers';
import { runTransitionName } from './run-transition';
import { lastValLoss, passesText, runSubtitle } from './run-view';
import { SPARK_HEIGHT, SPARK_WIDTH, sparklinePoints } from './sparkline';
import type { Run } from './training-client';

interface RunTileProps {
  run: Run;
  models: readonly Choice[];
}

export const runPath = (name: string) => `/training/${encodeURIComponent(name)}`;

// The card's numbers say the same, so the line is only a shape to the eye.
function Sparkline({ run }: { run: Run }) {
  return (
    <svg
      className="training-run__spark"
      viewBox={`0 0 ${SPARK_WIDTH} ${SPARK_HEIGHT}`}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polyline points={sparklinePoints(run.loss, run.steps)} />
    </svg>
  );
}

// The whole card opens the run's own screen, growing into its chart card as its name moves up
// to the toolbar.
export function RunTile({ run, models }: RunTileProps) {
  const val = run.val.length ? `Val loss ${lastValLoss(run)}` : '';

  return (
    <ViewTransition name={runTransitionName(run.name, 'card')} share="run-card">
      <li className="training-run">
        <Link className="training-run__select" to={runPath(run.name)}>
          <span className="training-run__head">
            <ViewTransition name={runTransitionName(run.name, 'title')}>
              <span className="training-run__name">{run.name}</span>
            </ViewTransition>
            {run.isTraining ? <TrainingNow /> : null}
          </span>
          <span className="training-run__subtitle">{runSubtitle(run, models)}</span>
          <Sparkline run={run} />
          <RunNumbers run={run} facts={[passesText(run.passes), val]} />
        </Link>
      </li>
    </ViewTransition>
  );
}
