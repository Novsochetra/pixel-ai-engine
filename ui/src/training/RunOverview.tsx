import { FactList } from '@/components/fact-list/FactList';
import type { Choice } from '@/create/create-client';
import { LossChart } from './LossChart';
import { RunNumbers, TrainingNow } from './RunNumbers';
import { passesText, runFacts, runSubtitle, sourcesText } from './run-view';
import type { Run } from './training-client';

function savedText(run: Run) {
  const count = run.checkpoints.length;

  return `${count} checkpoint${count === 1 ? '' : 's'}${run.final ? ' and a final' : ''}`;
}

// One run on its own screen: what it is, how far it got, its loss over the steps, its settings.
export function RunOverview({ run, models }: { run: Run; models: readonly Choice[] }) {
  return (
    <div className="run-overview">
      <section className="training-run run-overview__card">
        <span className="training-run__head">
          <span className="training-run__subtitle">{runSubtitle(run, models)}</span>
          {run.isTraining ? <TrainingNow /> : null}
        </span>
        <span className="training-run__subtitle">{sourcesText(run)}</span>
        <RunNumbers run={run} facts={[passesText(run.passes), savedText(run)]} />
        <LossChart run={run} />
      </section>
      <FactList title="Run" facts={runFacts(run, models)} />
    </div>
  );
}
