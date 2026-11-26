import { useState } from 'react';
import type { AnimateOptions, AnimateSources } from './animate-client';
import {
  defaultValues,
  firstSource,
  sourceDefaults,
  sourceKind,
  type AnimateValues,
  type SourceKind,
} from './animate-form';
import { useAnimateOptions, useAnimateSources, useUpload } from './use-animate';

type Changes = Partial<AnimateValues>;

function formValues(options: AnimateOptions, sources: AnimateSources, changes: Changes) {
  const base = defaultValues(options, sources);
  const source = changes.source ?? base.source;

  return { ...base, ...sourceDefaults(source, options, sources), ...changes };
}

// A new character gets its own views; words the person typed stay, the character's own do not.
function withSource({ views: _views, ...changes }: Changes, source: string): Changes {
  return { ...changes, source };
}

// Only what the person changed is kept; the rest follows the server's defaults once they load.
export function useAnimateForm() {
  const options = useAnimateOptions();
  const sources = useAnimateSources();
  const [changes, setChanges] = useState<Changes>({});
  const [pickedKind, setPickedKind] = useState<SourceKind>('made');

  const chooseSource = (source: string) => setChanges((current) => withSource(current, source));
  const upload = useUpload((uploaded) => chooseSource(uploaded.value));

  const queries = [options, sources];
  const isLoaded = options.data && sources.data;
  const values = isLoaded ? formValues(options.data!, sources.data!, changes) : null;

  return {
    options: options.data,
    sources: sources.data,
    values,
    kind: values?.source ? sourceKind(values.source) : pickedKind,
    upload,
    error: queries.find((query) => query.isError)?.error ?? null,
    change: (next: Changes) => setChanges((current) => ({ ...current, ...next })),
    chooseSource,

    chooseKind: (kind: SourceKind) => {
      setPickedKind(kind);
      chooseSource(sources.data ? firstSource(kind, sources.data) : '');
    },

    retry: () => queries.forEach((query) => query.isError && query.refetch()),
  };
}

export type AnimateForm = ReturnType<typeof useAnimateForm>;
