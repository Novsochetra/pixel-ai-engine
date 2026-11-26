import { useState } from 'react';
import { Segmented } from '@/components/segmented/Segmented';
import { FormError } from '@/create/FormError';
import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { MadeLayer } from '@/made/MadeLayer';
import { useMadeView } from '@/made/use-made-view';
import { RotateInspector } from './RotateInspector';
import { RotateTryouts } from './RotateTryouts';
import { TurnedGallery } from './TurnedGallery';
import { useRotated } from './use-rotate';
import { useRotateScreen } from './use-rotate-screen';
import '@/animate/animate.css';
import '@/create/create.css';
import '@/create/made-card.css';
import '@/library/library.css';
import './rotate.css';

type Shown = 'turned' | 'tryouts';

const SHOWN: { value: Shown; label: string }[] = [
  { value: 'turned', label: 'Turned' },
  { value: 'tryouts', label: 'Try-outs' },
];

// The turned characters, or the rotate try-outs to compare with; the inspector holds the form.
export function RotateScreen() {
  const screen = useRotateScreen();
  const turned = useRotated();
  const isNarrow = useMediaQuery(NARROW);
  const [shown, setShown] = useState<Shown>('turned');
  const made = useMadeView();

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;

  // A phone's form is a sheet that is closed when Rotate is pressed, so the error shows on top.
  const inspector = (
    <RotateInspector form={screen.form} problem={screen.problem} error={isNarrow ? null : error} />
  );
  const rotate = <JobButton label="Rotate" {...screen.button} onRun={screen.run} />;

  return (
    <ScreenFrame title="Rotate" actions={rotate} inspector={inspector}>
      <div className="library-bar">
        <div className="library-bar__filter">
          <Segmented label="Show" options={SHOWN} value={shown} onChange={setShown} />
        </div>
      </div>
      {shown === 'turned' ? (
        <div className="create-body">
          {isNarrow ? error : null}
          <TurnedGallery query={turned} onOpen={made.open} onDelete={made.ask} />
        </div>
      ) : (
        <RotateTryouts onOpen={made.open} />
      )}
      <MadeLayer view={made} />
    </ScreenFrame>
  );
}
