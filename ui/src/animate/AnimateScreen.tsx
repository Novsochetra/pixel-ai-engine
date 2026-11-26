import { FormError } from '@/create/FormError';
import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { MadeLayer } from '@/made/MadeLayer';
import { useMadeView } from '@/made/use-made-view';
import { AnimatedGallery } from './AnimatedGallery';
import { AnimateInspector } from './AnimateInspector';
import { PlayerSheet } from './PlayerSheet';
import { useAnimated } from './use-animate';
import { useAnimateScreen } from './use-animate-screen';
import { useClipChoice } from './use-clip-choice';
import '@/create/create.css';
import './animate.css';

// Animated runs, each playing in a sheet; the inspector holds the form, the toolbar Animate.
export function AnimateScreen() {
  const screen = useAnimateScreen();
  const runs = useAnimated();
  const isNarrow = useMediaQuery(NARROW);
  const clips = useClipChoice(runs.data?.runs);
  const made = useMadeView();

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;

  // A phone's form is a sheet that is closed when Animate is pressed, so the error shows on top.
  const inspector = (
    <AnimateInspector form={screen.form} problem={screen.problem} error={isNarrow ? null : error} />
  );
  const animate = <JobButton label="Animate" {...screen.button} onRun={screen.run} />;

  return (
    <ScreenFrame title="Animate" actions={animate} inspector={inspector}>
      <div className="create-body">
        {isNarrow ? error : null}
        <AnimatedGallery query={runs} onOpen={clips.open} onDelete={made.ask} />
      </div>
      <PlayerSheet
        chosen={clips.chosen}
        trash={made.trash}
        onChoose={clips.choose}
        onClosed={clips.close}
      />
      <MadeLayer view={made} />
    </ScreenFrame>
  );
}
