import { useState } from 'react';
import type { LibraryRequest } from './use-library';
import type { LibraryFilter, LibraryItem } from './library-view';

const FIRST: LibraryRequest = { filter: 'all', page: 1, search: '', choice: '' };

// What the library shows: any change but a page turn starts again at page 1 with nothing chosen.
export function useLibraryState() {
  const [request, setRequest] = useState(FIRST);
  const [selected, setSelected] = useState<LibraryItem | null>(null);
  const [viewing, setViewing] = useState<LibraryItem | null>(null);

  const change = (next: Partial<LibraryRequest>) => {
    setRequest((current) => ({ ...current, page: 1, ...next }));
    setSelected(null);
  };

  return {
    request,
    selected,
    viewing,
    setFilter: (filter: LibraryFilter) => change({ filter, choice: '' }),
    setSearch: (search: string) => change({ search }),
    setChoice: (choice: string) => change({ choice }),
    setPage: (page: number) => change({ page }),
    select: setSelected,
    open: setViewing,
    close: () => setViewing(null),
  };
}
