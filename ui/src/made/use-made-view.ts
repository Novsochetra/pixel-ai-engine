import { useState } from 'react';
import type { LibraryItem } from '@/library/library-view';
import type { MadeTarget } from './made-client';
import { useDeleteMade } from './use-delete-made';

// What a gallery of made things has open: the picture sheet, or the question a trash button asks.
export function useMadeView() {
  const trash = useDeleteMade();
  const [viewing, setViewing] = useState<LibraryItem | null>(null);
  const [asking, setAsking] = useState<MadeTarget | null>(null);

  return {
    trash,
    viewing,
    asking,
    open: setViewing,
    closeView: () => setViewing(null),
    ask: setAsking,
    closeAsk: () => setAsking(null),
  };
}

export type MadeView = ReturnType<typeof useMadeView>;
