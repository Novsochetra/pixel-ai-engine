import { FormError } from '@/create/FormError';
import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { RunGrid } from './RunGrid';
import { TrainingInspector } from './TrainingInspector';
import { useTrainingScreen } from './use-training-screen';
import '@/create/create.css';
import './training.css';

// The runs as cards, each opening its own screen; the inspector holds a new run, which the
// toolbar's one button starts.
export function TrainingScreen() {
  const screen = useTrainingScreen(null);
  const isNarrow = useMediaQuery(NARROW);

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;

  // A phone's inspector is a sheet that may be closed when the button is pressed, so the error
  // shows on top of the runs there.
  const inspector = <TrainingInspector screen={screen} error={isNarrow ? null : error} />;
  const action = <JobButton {...screen.button} onRun={screen.run} />;

  return (
    <ScreenFrame title="Training" actions={action} inspector={inspector}>
      <div className="create-body">
        {isNarrow ? error : null}
        <RunGrid query={screen.runs} models={screen.options.data?.models ?? []} />
      </div>
    </ScreenFrame>
  );
}
