import { useState } from 'react';
import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { PictureSheet } from '@/library/PictureSheet';
import type { LibraryItem } from '@/library/library-view';
import { CreateGallery } from './CreateGallery';
import { CreateInspector } from './CreateInspector';
import { FormError } from './FormError';
import { GenerateButton } from './GenerateButton';
import { useGenerated } from './use-create';
import { useCreateScreen } from './use-create-screen';
import './create.css';

// The gallery of made characters; the inspector holds the form, the toolbar its Generate.
export function CreateScreen() {
  const screen = useCreateScreen();
  const generated = useGenerated();
  const isNarrow = useMediaQuery(NARROW);
  const [viewing, setViewing] = useState<LibraryItem | null>(null);

  const error = screen.error ? (
    <FormError message={screen.error} onClose={screen.closeError} />
  ) : null;

  // A phone's form is a sheet that is closed when Generate is pressed, so the error shows on top.
  const inspector = <CreateInspector form={screen.form} error={isNarrow ? null : error} />;
  const generate = <GenerateButton {...screen.button} onGenerate={screen.run} />;

  return (
    <ScreenFrame title="Create" actions={generate} inspector={inspector}>
      <div className="create-body">
        {isNarrow ? error : null}
        <CreateGallery query={generated} onOpen={setViewing} />
      </div>
      <PictureSheet key={viewing?.key ?? ''} item={viewing} onClosed={() => setViewing(null)} />
    </ScreenFrame>
  );
}
