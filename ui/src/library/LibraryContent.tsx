import type { UseQueryResult } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { LibraryGrid } from './LibraryGrid';
import { LibraryEmpty, LibraryError, LibraryLoading } from './LibraryState';
import { Pager } from './Pager';
import type { LibraryItem, LibraryView } from './library-view';

interface LibraryContentProps {
  query: UseQueryResult<LibraryView>;
  view: LibraryView | undefined;
  selectedKey: string | undefined;
  onSelect: (item: LibraryItem) => void;
  onOpen: (item: LibraryItem) => void;
  onPage: (page: number) => void;
}

export function LibraryContent(props: LibraryContentProps) {
  const { query, view, selectedKey, onSelect, onOpen, onPage } = props;
  const body = useRef<HTMLDivElement>(null);
  const page = view?.page;

  // The Next button sits at the bottom, so a new page would open scrolled to its end.
  useEffect(() => {
    body.current?.parentElement?.scrollTo({ top: 0 });
  }, [page]);

  if (query.isError) {
    return <LibraryError error={query.error} onRetry={() => query.refetch()} />;
  }

  if (!view) {
    return <LibraryLoading />;
  }

  const pager = (
    <Pager page={view.page} pages={view.pages} hasMore={view.hasMore} onPage={onPage} />
  );

  if (!view.sections.length) {
    return (
      <>
        <LibraryEmpty notice={view.empty} />
        {pager}
      </>
    );
  }

  return (
    <div className="library-body" ref={body} aria-busy={query.isPlaceholderData}>
      <LibraryGrid
        sections={view.sections}
        selectedKey={selectedKey}
        onSelect={onSelect}
        onOpen={onOpen}
      />
      {pager}
    </div>
  );
}
