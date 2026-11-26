import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import {
  restoreMade,
  trashMade,
  type MadeKind,
  type MadeTarget,
  type Trashed,
} from './made-client';

export interface Deleted extends Trashed {
  kind: MadeKind;
  title: string;
}

// Every list that shows made things: Create's gallery, Rotate's, and Animate's runs and sources.
const MADE_LISTS = [['create', 'generated'], ['rotate', 'turned'], ['animate']];

export function useDeleteMade() {
  const client = useQueryClient();
  const [deleted, setDeleted] = useState<Deleted | null>(null);

  const refresh = () =>
    Promise.all(MADE_LISTS.map((queryKey) => client.invalidateQueries({ queryKey })));

  const remove = useMutation({
    mutationFn: trashMade,

    onSuccess: (moved, { kind, title }: MadeTarget) => {
      setDeleted({ ...moved, kind, title });
      refresh();
    },
  });

  const restore = useMutation({
    mutationFn: (gone: Deleted) => restoreMade(gone.kind, gone),

    onSuccess: () => {
      setDeleted(null);
      refresh();
    },
  });

  // Stable, so the toast's timer is not started again each time a list refreshes.
  const dismiss = useCallback(() => setDeleted(null), []);

  return { remove, restore, deleted, dismiss };
}

export type DeleteMade = ReturnType<typeof useDeleteMade>;
