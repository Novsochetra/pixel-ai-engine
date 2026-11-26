import { Progress } from '@/components/progress/Progress';
import { stepShare, stepsText, stepTimeText, timeLeftText } from './run-view';
import type { Run } from './training-client';

// The steps done, how fast and how long is left, then a line of what the place needs to know.
export function RunNumbers({ run, facts }: { run: Run; facts: readonly string[] }) {
  const pace = [stepTimeText(run.secondsPerStep), timeLeftText(run)].filter(Boolean).join(', ');

  return (
    <span className="training-run__numbers">
      <span className="training-run__steps">
        <strong>{stepsText(run)}</strong>
        {pace ? <span>{pace}</span> : null}
      </span>
      <Progress value={stepShare(run)} label={`${run.name}: ${stepsText(run)}`} />
      <span className="training-run__facts">{facts.filter(Boolean).join(' · ')}</span>
    </span>
  );
}

export function TrainingNow() {
  return (
    <span className="training-run__now">
      <Progress value={null} label="Training" />
      Training now
    </span>
  );
}
