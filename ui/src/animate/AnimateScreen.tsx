import { FormError } from '@/create/FormError';
import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { AnimatedGallery } from './AnimatedGallery';
import { AnimateInspector } from './AnimateInspector';
import { SpritePlayer } from './SpritePlayer';
import { useAnimated } from './use-animate';
import { useAnimateScreen } from './use-animate-screen';
import { useClipChoice } from './use-clip-choice';
import '@/create/create.css';
import './animate.css';

// The player and the gallery of animated runs; the inspector holds the form, the toolbar Animate.
export function AnimateScreen() {
  const screen = useAnimateScreen();
  const runs = useAnimated();
  const isNarrow = useMediaQuery(NARROW);
  const { chosen, shown, player, choose, play } = useClipChoice(runs.data?.runs);

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
        <div className="animate-player" ref={player}>
          {chosen ? (
            <SpritePlayer
              key={chosen.run.folder}
              run={chosen.run}
              clip={chosen.clip}
              onChoose={(clip) => choose(chosen.run, clip)}
            />
          ) : null}
        </div>
        <AnimatedGallery query={runs} chosen={shown} onChoose={play} />
      </div>
    </ScreenFrame>
  );
}
