import { useState } from 'react';
import { defaultValues, type CreateValues } from './create-form';
import { useFormOptions, useLoras } from './use-create';

// Only what the person changed is kept; the rest follows the server's defaults once they load.
export function useCreateForm() {
  const options = useFormOptions();
  const createLoras = useLoras('create');
  const rotateLoras = useLoras('rotate');
  const [changes, setChanges] = useState<Partial<CreateValues>>({});

  const queries = [options, createLoras, rotateLoras];
  const failed = queries.find((query) => query.isError);
  const isLoaded = options.data && createLoras.data && rotateLoras.data;
  const values = isLoaded
    ? { ...defaultValues(options.data!, rotateLoras.data!), ...changes }
    : null;

  return {
    options: options.data,
    createLoras: createLoras.data ?? [],
    rotateLoras: rotateLoras.data ?? [],
    values,
    error: failed?.error ?? null,
    change: (next: Partial<CreateValues>) => setChanges((current) => ({ ...current, ...next })),
    retry: () => queries.forEach((query) => query.isError && query.refetch()),
  };
}

export type CreateForm = ReturnType<typeof useCreateForm>;
