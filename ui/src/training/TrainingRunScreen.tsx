import { Link, useParams } from 'react-router';
import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import { FormError } from '@/create/FormError';
import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { RunOverview } from './RunOverview';
import { TrainingInspector } from './TrainingInspector';
import { useTrainingScreen, type TrainingScreenState } from './use-training-screen';
import '@/create/create.css';
import './training.css';

const BACK = { to: '/training', label: 'Training' };

function RunBody({ screen, name }: { screen: TrainingScreenState; name: string }) {
  const { run } = screen.choice;

  if (run) {
    return <RunOverview run={run} models={screen.options.data?.models ?? []} />;
  }

  if (!screen.runs.data) {
    return (
      <div className="create-loading">
        <Progress value={null} label="Loading the run" />
      </div>
    );
  }

  const back = (
    <Link className="pill-button pill-button--glass" to={BACK.to}>
      See all runs
    </Link>
  );

  return (
    <EmptyState icon="training" title={`No run called ${name}`} action={back}>
      It may have been deleted. Pick another run from Training.
    </EmptyState>
  );
}

// One run: its numbers and chart in the middle, Resume or Try out in the inspector.
export function TrainingRunScreen() {
  const name = useParams().name ?? '';
  const screen = useTrainingScreen(name);
  const isNarrow = useMediaQuery(NARROW);

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;
  const inspector = <TrainingInspector screen={screen} error={isNarrow ? null : error} />;
  const action = <JobButton {...screen.button} onRun={screen.run} />;

  return (
    <ScreenFrame title={name} back={BACK} actions={action} inspector={inspector}>
      <div className="create-body">
        {isNarrow ? error : null}
        <RunBody screen={screen} name={name} />
      </div>
    </ScreenFrame>
  );
}
