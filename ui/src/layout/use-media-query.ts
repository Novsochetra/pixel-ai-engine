import { useSyncExternalStore } from 'react';

// Matches the 48rem breakpoint in the layout CSS: below it the sidebar becomes a tab bar.
export const NARROW = '(max-width: 47.99rem)';

export function useMediaQuery(query: string): boolean {
  const subscribe = (onChange: () => void) => {
    const list = window.matchMedia(query);

    list.addEventListener('change', onChange);

    return () => list.removeEventListener('change', onChange);
  };

  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches);
}
