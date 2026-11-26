import { useState } from 'react';
import type { AnimateSources } from './animate-client';
import { firstSource, sourceKind, type SourceKind } from './animate-form';
import { useUpload } from './use-animate';

// What to work on: a generated character or an uploaded PNG. A new upload is chosen at once.
export function useSourcePicker(
  source: string | undefined,
  sources: AnimateSources | undefined,
  chooseSource: (source: string) => void,
) {
  const [pickedKind, setPickedKind] = useState<SourceKind>('made');
  const upload = useUpload((uploaded) => chooseSource(uploaded.value));

  return {
    kind: source ? sourceKind(source) : pickedKind,
    upload,
    chooseSource,

    chooseKind: (kind: SourceKind) => {
      setPickedKind(kind);
      chooseSource(sources ? firstSource(kind, sources) : '');
    },
  };
}

export type SourcePicker = ReturnType<typeof useSourcePicker>;
