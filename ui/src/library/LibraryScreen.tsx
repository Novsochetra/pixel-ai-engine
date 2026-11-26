import { ScreenFrame } from '@/layout/ScreenFrame';
import { NARROW, useMediaQuery } from '@/layout/use-media-query';
import { LibraryInspector } from './ItemDetails';
import { LibraryBar } from './LibraryBar';
import { LibraryContent } from './LibraryContent';
import { PictureSheet } from './PictureSheet';
import type { LibraryItem } from './library-view';
import { useLibraryView } from './use-library';
import { useLibraryState } from './use-library-state';
import './library.css';

// The dataset, flagged images, exports and try-outs in one grid; the inspector shows the records.
export function LibraryScreen() {
  const state = useLibraryState();
  const { request } = state;
  const isNarrow = useMediaQuery(NARROW);
  const { query, view } = useLibraryView(request);

  // A phone has no inspector beside the grid, so a tap opens the picture with its details.
  const select = (item: LibraryItem) => {
    state.select(item);

    if (isNarrow) {
      state.open(item);
    }
  };

  const summary = view?.summary ?? [];
  const inspector = (
    <LibraryInspector item={state.selected} summary={summary} onOpen={state.open} />
  );

  return (
    <ScreenFrame title="Library" inspector={inspector}>
      <LibraryBar
        request={request}
        picker={view?.picker ?? null}
        onFilter={state.setFilter}
        onSearch={state.setSearch}
        onChoice={state.setChoice}
      />
      <LibraryContent
        query={query}
        view={view}
        selectedKey={state.selected?.key}
        onSelect={select}
        onOpen={state.open}
        onPage={state.setPage}
      />
      <PictureSheet key={state.viewing?.key ?? ''} item={state.viewing} onClosed={state.close} />
    </ScreenFrame>
  );
}
