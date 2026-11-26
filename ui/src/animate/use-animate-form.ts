import { useState } from 'react';
import type { AnimateOptions, AnimateSources } from './animate-client';
import { defaultValues, sourceDefaults, type AnimateValues } from './animate-form';
import { useAnimateOptions, useAnimateSources } from './use-animate';
import { useSourcePicker } from './use-source-picker';

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

  const queries = [options, sources];
  const isLoaded = options.data && sources.data;
  const values = isLoaded ? formValues(options.data!, sources.data!, changes) : null;
  const picker = useSourcePicker(values?.source, sources.data, (source) =>
    setChanges((current) => withSource(current, source)),
  );

  return {
    ...picker,
    options: options.data,
    sources: sources.data,
    values,
    error: queries.find((query) => query.isError)?.error ?? null,
    change: (next: Changes) => setChanges((current) => ({ ...current, ...next })),
    retry: () => queries.forEach((query) => query.isError && query.refetch()),
  };
}

export type AnimateForm = ReturnType<typeof useAnimateForm>;
