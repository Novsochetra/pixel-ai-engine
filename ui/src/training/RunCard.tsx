import { Progress } from '@/components/progress/Progress';
import type { Choice } from '@/create/create-client';
import { LossChart } from './LossChart';
import {
  passesText,
  runSubtitle,
  sourcesText,
  stepShare,
  stepsText,
  stepTimeText,
  timeLeftText,
} from './run-view';
import type { Run } from './training-client';

interface RunCardProps {
  run: Run;
  models: readonly Choice[];
  isChosen: boolean;
  onChoose: (name: string) => void;
}

function RunNumbers({ run }: { run: Run }) {
  const pace = [stepTimeText(run.secondsPerStep), timeLeftText(run)].filter(Boolean).join(', ');
  const checkpoints = run.checkpoints.length;
  const saved = `${checkpoints} checkpoint${checkpoints === 1 ? '' : 's'}${run.final ? ' and a final' : ''}`;

  return (
    <span className="training-run__numbers">
      <span className="training-run__steps">
        <strong>{stepsText(run)}</strong>
        {pace ? <span>{pace}</span> : null}
      </span>
      <Progress value={stepShare(run)} label={`${run.name}: ${stepsText(run)}`} />
      <span className="training-run__facts">
        {[passesText(run.passes), saved].filter(Boolean).join(' · ')}
      </span>
    </span>
  );
}

// The head of a card is the button that selects it; the chart below it can be read on its own.
export function RunCard({ run, models, isChosen, onChoose }: RunCardProps) {
  return (
    <li className="training-run" data-chosen={isChosen}>
      <button
        className="training-run__select"
        type="button"
        aria-pressed={isChosen}
        onClick={() => onChoose(run.name)}
      >
        <span className="training-run__head">
          <span className="training-run__name">{run.name}</span>
          {run.isTraining ? (
            <span className="training-run__now">
              <Progress value={null} label="Training" />
              Training now
            </span>
          ) : null}
        </span>
        <span className="training-run__subtitle">{runSubtitle(run, models)}</span>
        <span className="training-run__subtitle">{sourcesText(run)}</span>
        <RunNumbers run={run} />
      </button>
      <LossChart run={run} />
    </li>
  );
}
