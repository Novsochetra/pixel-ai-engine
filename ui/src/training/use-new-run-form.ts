import { useState } from 'react';
import type { TrainingOptions } from './training-client';
import { defaultValues, exportSources, type NewRunValues } from './training-form';

type Changes = Partial<NewRunValues>;

// Only what the person changed is kept; the rest follows the server's defaults once they load.
export function useNewRunForm(options: TrainingOptions | undefined) {
  const [changes, setChanges] = useState<Changes>({});

  return {
    values: options ? { ...defaultValues(options), ...changes } : null,
    change: (next: Changes) => setChanges((current) => ({ ...current, ...next })),

    // Another export has other sources: all of them are checked again, as on the old page.
    chooseExport: (name: string) =>
      setChanges((current) => ({
        ...current,
        export: name,
        sources: options ? exportSources(options, name) : [],
      })),

    clearName: () => setChanges(({ name: _name, ...current }) => current),
  };
}

export type NewRunForm = ReturnType<typeof useNewRunForm>;
