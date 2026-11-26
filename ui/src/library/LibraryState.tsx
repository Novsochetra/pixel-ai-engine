import { EmptyState } from '@/components/empty-state/EmptyState';
import { Progress } from '@/components/progress/Progress';
import type { LibraryNotice } from './library-view';

export function LibraryLoading() {
  return (
    <div className="library-loading">
      <Progress value={null} label="Loading the library" />
    </div>
  );
}

export function LibraryError({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const retry = (
    <button className="pill-button pill-button--tinted" type="button" onClick={onRetry}>
      Try again
    </button>
  );

  return (
    <EmptyState icon="warning" title="The library did not load" action={retry}>
      {error.message} Check that the server runs, then try again.
    </EmptyState>
  );
}

export function LibraryEmpty({ notice }: { notice: LibraryNotice }) {
  return (
    <EmptyState icon="library" title={notice.title}>
      {notice.text}
      {notice.command ? (
        <>
          {' '}
          <code>{notice.command}</code>
        </>
      ) : null}
    </EmptyState>
  );
}
