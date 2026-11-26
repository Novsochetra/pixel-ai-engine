import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { restoreMade, trashMade, type Trashed } from './made-client';

export interface Deleted extends Trashed {
  title: string;
}

// Every list that shows made characters: Create's gallery, Rotate's, and Animate's sources.
const MADE_LISTS = [['create', 'generated'], ['rotate', 'turned'], ['animate']];

export function useDeleteMade() {
  const client = useQueryClient();
  const [deleted, setDeleted] = useState<Deleted | null>(null);

  const refresh = () =>
    Promise.all(MADE_LISTS.map((queryKey) => client.invalidateQueries({ queryKey })));

  const remove = useMutation({
    mutationFn: ({ folder }: { folder: string; title: string }) => trashMade(folder),

    onSuccess: (moved, { title }) => {
      setDeleted({ ...moved, title });
      refresh();
    },
  });

  const restore = useMutation({
    mutationFn: restoreMade,

    onSuccess: () => {
      setDeleted(null);
      refresh();
    },
  });

  // Stable, so the toast's timer is not started again each time a list refreshes.
  const dismiss = useCallback(() => setDeleted(null), []);

  return { remove, restore, deleted, dismiss };
}
