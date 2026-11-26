import type { UseQueryResult } from '@tanstack/react-query';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import type { Choice } from '@/create/create-client';
import { RunCard } from './RunCard';
import type { Run } from './training-client';

type RunsQuery = UseQueryResult<{ runs: Run[] }>;

interface RunListProps {
  query: RunsQuery;
  models: readonly Choice[];
  chosen: string | null;
  onChoose: (name: string) => void;
}

function ListError({ query }: { query: RunsQuery }) {
  const retry = (
    <button
      className="pill-button pill-button--glass"
      type="button"
      onClick={() => query.refetch()}
    >
      Try again
    </button>
  );

  return (
    <EmptyState icon="warning" title="The runs did not load" action={retry}>
      {query.error?.message} Check that the server runs, then try again.
    </EmptyState>
  );
}

// Every training run, newest first, each with its loss chart.
export function RunList({ query, models, chosen, onChoose }: RunListProps) {
  if (query.isError) {
    return <ListError query={query} />;
  }

  if (!query.data) {
    return (
      <div className="create-loading">
        <Progress value={null} label="Loading the runs" />
      </div>
    );
  }

  if (!query.data.runs.length) {
    return (
      <EmptyState icon="training" title="No training runs yet">
        Name a run in the inspector, pick its sources, then Start training.
      </EmptyState>
    );
  }

  return (
    <ul className="training-runs" aria-label="Training runs">
      {query.data.runs.map((run) => (
        <RunCard
          key={run.name}
          run={run}
          models={models}
          isChosen={run.name === chosen}
          onChoose={onChoose}
        />
      ))}
    </ul>
  );
}
