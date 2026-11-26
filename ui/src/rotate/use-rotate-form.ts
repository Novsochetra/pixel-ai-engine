import { useState } from 'react';
import { useAnimateSources } from '@/animate/use-animate';
import { useSourcePicker } from '@/animate/use-source-picker';
import { useLoras } from '@/create/use-create';
import { defaultValues, turnable, type RotateValues } from './rotate-form';
import { useRotateOptions } from './use-rotate';

type Changes = Partial<RotateValues>;

// Only what the person changed is kept; the rest follows the server's defaults once they load.
export function useRotateForm() {
  const options = useRotateOptions();
  const sources = useAnimateSources();
  const loras = useLoras('rotate');
  const [changes, setChanges] = useState<Changes>({});

  const queries = [options, sources, loras];
  const choices = sources.data && turnable(sources.data);
  const isLoaded = options.data && choices && loras.data;
  const values = isLoaded
    ? { ...defaultValues(options.data!, choices, loras.data!), ...changes }
    : null;
  const picker = useSourcePicker(values?.source, choices, (source) =>
    setChanges((current) => ({ ...current, source })),
  );

  return {
    ...picker,
    options: options.data,
    sources: choices,
    loras: loras.data ?? [],
    values,
    error: queries.find((query) => query.isError)?.error ?? null,
    change: (next: Changes) => setChanges((current) => ({ ...current, ...next })),
    retry: () => queries.forEach((query) => query.isError && query.refetch()),
  };
}

export type RotateForm = ReturnType<typeof useRotateForm>;
