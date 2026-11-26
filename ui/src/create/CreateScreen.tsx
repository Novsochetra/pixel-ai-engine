import { JobButton } from '@/jobs/JobButton';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { MadeLayer } from '@/made/MadeLayer';
import { useMadeView } from '@/made/use-made-view';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { CreateGallery } from './CreateGallery';
import { CreateInspector } from './CreateInspector';
import { FormError } from './FormError';
import { useGenerated } from './use-create';
import { useCreateScreen } from './use-create-screen';
import './create.css';

// The gallery of made characters; the inspector holds the form, the toolbar its Generate.
export function CreateScreen() {
  const screen = useCreateScreen();
  const generated = useGenerated();
  const isNarrow = useMediaQuery(NARROW);
  const made = useMadeView();

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;

  // A phone's form is a sheet that is closed when Generate is pressed, so the error shows on top.
  const inspector = <CreateInspector form={screen.form} error={isNarrow ? null : error} />;
  const generate = <JobButton label="Generate" {...screen.button} onRun={screen.run} />;

  return (
    <ScreenFrame title="Create" actions={generate} inspector={inspector}>
      <div className="create-body">
        {isNarrow ? error : null}
        <CreateGallery query={generated} onOpen={made.open} onDelete={made.ask} />
      </div>
      <MadeLayer view={made} />
    </ScreenFrame>
  );
}
