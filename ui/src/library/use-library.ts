import { useQuery } from '@tanstack/react-query';
import { characterView } from './character-view';
import { exportsView, flaggedView } from './collection-view';
import { tryoutsView } from './tryout-view';
import {
  fetchCharacter,
  fetchCharacters,
  fetchExports,
  fetchFlagged,
  fetchTryouts,
} from './library-client';
import { searchView, type LibraryFilter, type LibraryView } from './library-view';
import { useDebounced } from './use-debounced';

const SEARCH_PAUSE_MS = 300;

export interface LibraryRequest {
  filter: LibraryFilter;
  page: number;
  search: string;
  choice: string;
}

// Only the dataset is searched on the server: it holds millions of characters.
export function fetchView({ filter, page, search, choice }: LibraryRequest): Promise<LibraryView> {
  switch (filter) {
    case 'all':
      return fetchCharacters(page, search, choice).then((reply) => characterView(reply, choice));
    case 'flagged':
      return fetchFlagged(page, choice).then(flaggedView);
    case 'exports':
      return fetchExports().then(exportsView);
    case 'tryouts':
      return fetchTryouts(choice).then(tryoutsView);
  }
}

export function useLibrary(request: LibraryRequest) {
  const { filter, page, choice } = request;
  const search = filter === 'all' ? request.search : '';

  return useQuery({
    queryKey: ['library', filter, page, search, choice],
    queryFn: () => fetchView({ ...request, search }),

    // Turning a page keeps the old one in view until the next arrives; another filter does not.
    placeholderData: (previous, previousQuery) =>
      previousQuery?.queryKey[1] === filter ? previous : undefined,
  });
}

// The dataset waits for a pause in typing; the lists already here are searched at once.
export function useLibraryView(request: LibraryRequest) {
  const search = useDebounced(request.search, SEARCH_PAUSE_MS);
  const query = useLibrary({ ...request, search });
  const localSearch = request.filter === 'all' ? '' : request.search;

  return { query, view: query.data && searchView(query.data, localSearch) };
}

export function useCharacter(id: string | null) {
  return useQuery({
    queryKey: ['library', 'character', id],
    queryFn: () => fetchCharacter(id!),
    enabled: id !== null,
  });
}
