import { countText } from './library-view';

interface PagerProps {
  page: number;
  pages: number | null;
  hasMore: boolean;
  onPage: (page: number) => void;
}

export function Pager({ page, pages, hasMore, onPage }: PagerProps) {
  if (page === 1 && !hasMore) {
    return null;
  }

  return (
    <nav className="pager" aria-label="Pages">
      <button
        className="pill-button pill-button--plain"
        type="button"
        disabled={page === 1}
        onClick={() => onPage(page - 1)}
      >
        Previous
      </button>
      <span className="pager__place">
        Page {countText(page)}
        {pages ? ` of ${countText(pages)}` : ''}
      </span>
      <button
        className="pill-button pill-button--plain"
        type="button"
        disabled={!hasMore}
        onClick={() => onPage(page + 1)}
      >
        Next
      </button>
    </nav>
  );
}
